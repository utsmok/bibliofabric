# Keywords

`client.keywords` talks to the `/keywords` endpoint and returns `Keyword` models.

```python
keyword = await client.keywords.get("photosynthesis")
```

Keyword ids are slugs (`photosynthesis`), not `K...` codes, and `get()` normalizes the id before the request. A bare id and a full URL both resolve.

## Filters

`KeywordsFilters` fields: `display_name`, `works_count` (accepts ints or OpenAlex range strings like `">1000"`), and `display_name.search`.

All shared operations are available: `get()`, `search()`, `iterate()`, `collect()`, `first()`, `count()`, `batch_get()`.
