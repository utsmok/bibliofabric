# Types

`client.types` covers `/types` and `/types/{id}`.

```python
type_ = await client.types.get("journal-article")
type_.label                          # "Journal Article"

page = await client.types.search()   # the complete list
```

The route takes no `query`, `filter`, `sort`, or `select`; any of those raises `ConfigurationError` client-side. The route also ignores paging parameters and always returns the complete list, about 30 types.

`types.works(type_id)` returns a works client bound to `/types/{id}/works`; see [Works](works.md#scoped-works).
