# Licenses

`client.licenses` covers the `/licenses` list route. Crossref has no single-license route, so `licenses.get()` returns 404.

```python
page = await client.licenses.search(query="creativecommons", page_size=10)
page.results[0].url
page.results[0].work_count
```

Licenses can be iterated with `iterate()` like any other resource.
