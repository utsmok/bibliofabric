# Search

`client.search` wraps `wbsearchentities` and the REST search routes.

## `wbsearchentities`

```python
page = await client.search.search(query="douglas adams", language="en", type="item")
```

`search()` returns a `Page[EntitySearchResult]`. The `language`, `uselang`, `type`, and `strict_language` options map to the module's parameters; `page`, `page_size`, and `iterate()`'s paging use the module's `limit` and `continue` parameters.

`wbsearchentities` reports no total, so `count()` raises `ConfigurationError`. `iterate()` and `collect()` walk `continue` offset pages until the API returns an empty page:

```python
async for hit in client.search.iterate(query="adams", page_size=50, limit=200):
    ...
```

`EntitySearchResult` carries `id`, `label`, `description`, `match`, `aliases`, and `concepturi`.

## REST search

The Wikibase REST API answers `search/items` and `search/properties` with a language-fallback display label:

```python
items = await client.search.search_items("Douglas Adams", language="en", limit=3)
props = await client.search.search_properties("instance", language="en", limit=5)
```

Both return `RestSearchResult` records with `id`, `display_label` (`language`, `value`), `description`, and `match`.

## REST suggestions

The REST suggest routes answer the same result shape as the search routes and match aliases too:

```python
items = await client.search.suggest_items("einstein", language="en", limit=3)
props = await client.search.suggest_properties("instance", language="en")
```

Their query parameter is `q`; a `search=` parameter answers 400 `parameter-validation-failed` (verified 2026-11-28). The client sends `q`.
