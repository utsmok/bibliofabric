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

## One citation by OCI

`citation(oci)` returns the single citation with this Open Citation Identifier, or `None`. The prefix is optional: `"oci:1-18"` and `"1-18"` both work.

```python
row = await client.index.citation("06101801781-06180334099")
```

## Counts

`citation_count(id)` and `reference_count(id)` return the number of incoming citations and outgoing references of one entity. `venue_citation_count(issn)` returns the incoming citations to all entities published in one venue; this operation accepts only `issn:` ids. An unknown identifier returns `None`, because the API answers `[]` instead of a zero row.

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
