# Meta API

The Meta API v1 (`https://api.opencitations.net/meta/v1`) holds the bibliographic metadata of the documents involved in the citations of the OpenCitations Index. `client.meta` exposes one method per documented operation. The rows share the shape of `MetadataRecord`.

## Metadata

`metadata(ids)` returns the bibliographic metadata of one or more entities.

```python
records = await client.meta.metadata("doi:10.1007/978-1-4020-9632-7")
record = records[0]
print(
    record.title, record.type, record.pub_date
)  # "Adaptive Environmental Management", "book", "2009"
print(record.identifiers)  # parsed from record.id
print(record.authors, record.editors)  # split from the semicolon lists
```

The accepted schemes are `doi`, `issn`, `isbn`, `omid`, `openalex`, `pmid`, and `pmcid` (wider than the Index API, which rejects `openalex:`). Several entities travel in one request: pass a list of identifiers, or a single string with the `__` separator the API documents. One row comes back per entity found; an unknown identifier contributes no row, so an unknown single id answers with `[]`.

| Field | Meaning |
|---|---|
| `id` | Space-separated, prefixed identifiers of the entity. |
| `title`, `pub_date`, `volume`, `issue`, `page`, `type` | Bibliographic fields; empty strings when unknown. |
| `author`, `editor` | Semicolon-separated person strings with bracketed ids, for example `Peroni, Silvio [orcid:0000-0003-0530-4305 omid:ra/0614010840729]`. |
| `venue` | Venue title followed by its identifiers in brackets. |
| `publisher` | Publisher name with its identifiers in brackets. |

The `identifiers`, `authors`, and `editors` properties parse those packed strings into `ParsedIdentifier` entries and plain person strings.

## Authors and editors

`author(id)` returns the entities the person authored, `editor(id)` the entities the person edited. The identifier is an ORCID (`orcid:0000-0002-8420-0696`) or the OpenCitations id of a responsible entity (`omid:ra/0601`).

```python
works = await client.meta.author("orcid:0000-0002-8420-0696")
for record in works:
    print(record.pub_date, record.title)
```

## Row shaping

All three methods accept the same `require`, `filter`, `sort`, and `format` parameters as the Index API; see [Index API](index-api.md#row-shaping). `format="csv"` parses into `MetadataRecord` rows like the JSON form.
