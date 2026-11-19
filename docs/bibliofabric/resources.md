# Resources

`ResourceClient[E]` is a generic client for one API endpoint. Declare the
endpoint path, the entity model, and the query dialect; override hook methods
where the API deviates from the defaults.

```python
class Works(ResourceClient[Work]):
    path = "works"
    model = Work
    dialect = DIALECT
```

## Operations

- `get(id)` fetches one entity; a 404 raises `NotFoundError`.
- `search(filters, ...)` fetches one page and returns a `Page[E]` with
  `results`, `total`, `next_cursor`, `page`, and `meta`. Filters accept a
  pydantic model or a plain dict.
- `iterate(...)` yields entities across pages. It uses cursor paging when the
  dialect has a `cursor_param`, otherwise page or offset paging. It stops at
  `limit`, on an empty page, or when there is no next cursor.
  `on_page(page_number, next_cursor)` checkpoints progress; passing a saved
  cursor back via `cursor=` resumes a cursor-mode harvest.
- `count()` reads the unwrapper total from a minimal page.
- `batch_get(ids, field="id", batch_size=None, concurrency=4)` normalizes and
  deduplicates ids, fetches them in concurrent chunks, and returns a dict keyed
  by normalized id. Missing ids are absent from the result.

## Hooks

Override these methods on subclasses:

- `build_filter_params(filters)` — filter serialization (OpenAlex joins filters
  into one `filter` parameter).
- `format_sort(sort)` — sort parameter shape (Crossref splits `sort`/`order`).
- `build_batch_params(field, values)` — batch OR syntax (Crossref uses
  pipe-separated values in one parameter).
- `normalize_id(value)` — canonical identifier form (DOIs via
  `bibliofabric.ids.normalize_doi`).
- `item_path(id)` — single-entity path; the default URL-encodes the id.

`params=` is the escape hatch for API extras (facets, `sample`, `seed`); typed
wrappers for those belong on resource subclasses.

## API reference

::: bibliofabric.resources
    options:
      show_root_heading: true
