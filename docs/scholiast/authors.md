# Authors

`client.authors` talks to the `/author` routes and returns `Author` models.

## Get one author

```python
author = await client.authors.get("1741101", select=["name", "hIndex", "paperCount"])
found = await client.authors.exists("1741101")
```

Without `fields` the API answers with `authorId` only. `externalIds` and
`papers` are key-gated upstream: a keyless request that asks for them
answers HTTP 400.

## The author model

| Field | Content |
|---|---|
| `authorId` | The Semantic Scholar id |
| `name`, `aliases` | Names |
| `affiliations` | Affiliation strings |
| `homepage`, `url` | Links |
| `paperCount`, `citationCount`, `hIndex` | Counters |
| `externalIds` | Catalog ids; needs a key |
| `papers` | Papers linked to the author; needs a key |

Fields the API adds later are kept in `model_extra`.

## Search

```python
page = await client.authors.search(
    query="adam smith", fields=["name", "affiliations"], page_size=20
)
page.total
page.results
page.next_cursor  # the next offset as a string
```

`search()`, `iterate()`, `collect()`, `first()`, and `count()` come from
the resource base; paging uses `offset` and `limit` like the paper search.

## Papers of one author

```python
page = await client.authors.papers(
    "1741101", fields=["title", "year", "citationCount"], limit=100
)
```

Returns one page of `Paper` records. The route serves at most the most
recent 10,000 papers of an author.

## Batch

```python
authors = await client.authors.batch(
    ["1741101", "1780531", "99999999"], fields=["name", "hIndex"]
)
```

One `POST /author/batch` call fetches up to 1000 authors; the client
chunks longer lists. The API answers `null` for unknown ids and the
client drops those entries. The POST is a read and is sent with retries.
