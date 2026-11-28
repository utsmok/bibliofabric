# Index API

The Index API v2 (`https://api.opencitations.net/index/v2`) stores who cites whom. `client.index` exposes one method per documented operation; every method sends one GET and returns the complete result.

## Citations and references

`citations(id)` returns the incoming citations of one entity: every row records a reference in which the entity is cited. `references(id)` returns the outgoing references in the reference list of one entity.

```python
rows = await client.index.citations("doi:10.1108/jd-12-2013-0166")
row = rows[0]
print(row.oci)  # "06012708740-06180334099"
print(
    row.citing
)  # "omid:br/06012708740 doi:10.53730/ijhs.v9n2.15534 openalex:W4411604700"
print(
    row.cited_identifiers
)  # [ParsedIdentifier(scheme='omid', value='br/06180334099'), ...]
print(row.creation, row.timespan, row.journal_sc, row.author_sc)
```

`id` is a prefixed identifier. The Index API accepts `doi:`, `omid:`, `pmid:`, `issn:`, and `isbn:`; the client rejects anything else, including bare DOIs and `openalex:` ids, with `ConfigurationError` before a request is sent. The model fields:

| Field | Meaning |
|---|---|
| `oci` | Open Citation Identifier of the citation, `first-second`. |
| `citing`, `cited` | Space-separated, prefixed identifiers of the two entities. |
| `creation` | Publication date of the citing entity; may be partial (`2013`, `2013-07`). |
| `timespan` | XSD duration between the publication dates; may be negative (`-P1Y1M16D`). |
| `journal_sc`, `author_sc` | `"yes"`/`"no"` strings for a journal self-citation and an author self-citation. |

An unknown identifier is not an error: the API answers 200 with `[]` and the method returns an empty list.

The client percent-encodes the identifier for the URL path, so a DOI that contains `#`, `?`, parentheses, or angle brackets arrives whole. The server decodes the path before it looks up the identifier.

## One citation by OCI

`citation(oci)` returns the single citation with this Open Citation Identifier, or `None`. The prefix is optional: `"oci:1-18"` and `"1-18"` both work.

```python
row = await client.index.citation("06101801781-06180334099")
```

## Counts

`citation_count(id)` and `reference_count(id)` return the number of incoming citations and outgoing references of one entity. `venue_citation_count(issn)` returns the incoming citations to all entities published in one venue; this operation accepts only `issn:` ids. An unknown identifier answers 200 with a zero row, which the methods return as `0`. On 2026-11-27 the API answered `[]` for the same request instead; the methods return `None` for that body.

```python
incoming = await client.index.citation_count("doi:10.1108/jd-12-2013-0166")
venue = await client.index.venue_citation_count("issn:0138-9130")
```

The JSON body carries the count as a string (`{"count": "57"}`) even though the documentation types it as int; the `Count` model coerces it.

## Row shaping

`citations()`, `references()`, and the Meta row operations accept four parameters that the server applies in this order:

1. `require`: drop rows whose field is empty. A string or a list of field names; the parameter repeats.
2. `filter`: keep rows matching a regular expression, or `=`, `<`, `>` with a value, as in `creation:>2019-12`. The parameter repeats.
3. `sort`: `asc(field)` or `desc(field)`, for example `desc(creation)`.
4. `format`: `"json"` (default) or `"csv"`.

```python
rows = await client.index.citations(
    "doi:10.1108/jd-12-2013-0166",
    require="creation",
    filter="creation:>2019-12",
    sort="desc(creation)",
)
```

With `format="csv"` the server returns its CSV table; the client parses it into the same models, because the CSV header repeats the JSON field names. The `format` parameter overrides the `Accept` header server-side, so the header alone never changes the representation.

## SPARQL

Each OpenCitations dataset has a SPARQL endpoint on a second host: `https://sparql.opencitations.net/index` for the Index dataset and `https://sparql.opencitations.net/meta` for the Meta dataset. `sparql()` sends a query and returns the SPARQL 1.1 Query Results JSON answer as a `SparqlResult`. `sparql_text()` returns the body of another representation as text.

```python
result = await client.index.sparql(
    "SELECT ?ci ?citing ?cited WHERE { "
    "?ci <http://purl.org/spar/cito/hasCitingEntity> ?citing ; "
    "<http://purl.org/spar/cito/hasCitedEntity> ?cited } LIMIT 5"
)
for row in result.rows():
    print(row["ci"], row["citing"], row["cited"])
print(result.meta["result-size-total"])
```

`SparqlResult` keeps the whole answer: `head.vars`, `results.bindings`, `boolean` for an ASK query, and `meta` with the query time and the number of rows the server reports. `results.bindings` is a list of dictionaries from variable name to `SparqlTerm`. Each term has `type` (`uri`, `literal`, or `bnode`) and `value`; a literal also carries `datatype` and `xml_lang` when the server sends them. `rows()` flattens the bindings into a list of dictionaries from variable name to the term's string value. It returns `[]` for an ASK answer, where `boolean` holds the result.

`sparql_text()` asks for one of the other result formats through the `Accept` header. `format` is one of `json`, `xml`, `csv`, `tsv`, `turtle` (the default), or `n-triples`. Use this method for CONSTRUCT and DESCRIBE queries, because their answers are RDF documents: the endpoint answers Turtle when a CONSTRUCT query asks for JSON.

```python
turtle = await client.index.sparql_text(
    "CONSTRUCT { ?ci <http://purl.org/spar/cito/hasCitingEntity> ?citing } "
    "WHERE { ?ci <http://purl.org/spar/cito/hasCitingEntity> ?citing } LIMIT 5"
)
```

Both methods send the query in the URL of a GET request by default. Pass `method="POST"` to send it in the body of a form request instead, which suits long queries. The `timeout` argument sets a per-request timeout in seconds.

An empty query or an unknown `format` raises `ConfigurationError` before a request is sent. A malformed query makes the server answer 400, which raises `APIError`. An answer that is not a SPARQL result document raises `ValidationError`.
