# Prefixes

Crossref serves no `/prefixes` list route, so prefixes are addressable only one at a time. `prefixes.search()`, `count()`, and `iterate()` raise `ConfigurationError`.

```python
prefix = await client.prefixes.get("10.1038")
prefix.member  # "297"; the API returns a full URI, the model keeps the bare value
prefix.name

page = await client.prefixes.works("10.1038").search()
```

`prefixes.works(prefix)` returns a works client bound to `/prefixes/{prefix}/works`; see [Works](works.md#scoped-works).
