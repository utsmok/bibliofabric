# Search

`client.search` talks to `/search`. Every method sends `format=json` and
returns :class:`Page` objects whose records are `SearchResult` models.

## One page

```python
page = await client.search.search(
    query="nanodiamond AND OPEN_ACCESS:Y", result_type="core", page_size=25
)
print(page.total)  # hitCount
print(page.next_cursor)  # nextCursorMark
print(page.results[0].title)
```

- `query` is a Europe PMC query string: free text, field queries
  (`DOI:`, `PMCID:`, `AUTH:`, `SRC:PMC`), boolean operators, and parentheses.
- `result_type` is `"lite"` (scalar metadata), `"core"` (adds abstract,
  keywords, MeSH headings, grants, chemicals, full text URLs, and more), or
  `"idlist"`, `"json"`, `"xml"`, `"dc"`. The model accepts all shapes; unknown
  fields are kept on the model.
- `synonym=True` expands query terms with MeSH synonyms.
- `sort` is an expression such as `"CITED desc"`, `"P_PDATE_D asc"`, or
  `"PDATE desc"`. The client rejects expressions whose field is not one of
  `CITED`, `P_PDATE_D`, `PDATE`, `AUTHOR_ID`, or `RELEVANCE`.
- `page_size` is capped at 1000, the maximum the API accepts.

## Iterate everything

The search pages with `cursorMark` tokens. `nextCursorMark` repeats unchanged
once the result list is exhausted, and the framework stops on that.

```python
async for record in client.search.iterate(
    query="cancer", result_type="lite", page_size=1000
):
    print(record.id, record.source)

# resume later from a saved cursor
async for record in client.search.iterate(query="cancer", cursor=saved_cursor):
    ...
```

A search can take several seconds. The client default timeout is 30 seconds.

## Count without fetching

```python
total = await client.search.count(query="SRC:PPR AND TITLE:nanodiamond")
```

## Search over POST

`POST /searchPOST` is the same search with the parameters in a form-encoded
body. `search_post()` mirrors `search()`, and cursor paging works on the
route, so `iterate_post()` mirrors `iterate()`.

```python
page = await client.search.search_post(query="cancer", result_type="core")
async for record in client.search.iterate_post(query="cancer", page_size=1000):
    print(record.id)
```

## Index terms

```python
fields = await client.search.fields()
# ["ACCESSION_ID", "ABSTRACT", ...]
```

`client.profiles.fields()` returns the same list as a typed
`FieldsResponse` model.
