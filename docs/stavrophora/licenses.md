# Licenses

`client.licenses` covers the `/licenses` list route. Crossref has no single-license route, so `licenses.get()` and `licenses.exists()` raise `ConfigurationError`.

```python
page = await client.licenses.search(query="creativecommons", page_size=10)
page.results[0].url
page.results[0].work_count
```

`licenses.iterate()` pages with `offset` and `rows` (Crossref does not support `cursor` on `/licenses`).
