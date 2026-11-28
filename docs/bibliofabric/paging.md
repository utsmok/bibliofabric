# Paging

Paging behavior is declared once per API in a frozen `QueryDialect` and shared
by all resource clients of that API (or overridden per instance via
`ResourceClient(..., dialect=...)`).

```python
DIALECT = QueryDialect(
    page_size_param="per_page",  # None for unpaged APIs (e.g. OpenCitations)
    max_page_size=200,
    default_page_size=25,
    page_param="page",  # None when the API has no page numbers
    page_start=1,  # 0 for OpenAIRE links and Scholix
    offset_param=None,  # "offset" for Crossref; replaces page_param
    max_offset=None,  # optional cap enforced on page/offset paging
    cursor_param=None,  # "cursor" enables cursor paging
    cursor_start="*",
    sort_param="sort",
    query_param=None,  # free-text search parameter
    select_param=None,  # field selection parameter
    iterate_page_size=100,  # page size iterate() uses when the caller passes none; falls back to default_page_size
    count_page_size=0,  # page size count() requests; 0 for APIs that return totals with zero rows
)
```

`iterate()` uses cursor paging when `cursor_param` is set; otherwise it walks
page numbers (`page_param`) or offsets (`offset_param`, where page N becomes
`offset=(N - page_start) * page_size`). When `page_param`, `offset_param`, and
`cursor_param` are all `None`, `iterate()` fetches once and stops.

Passing `query`, `select`, `sort`, `cursor`, or `page` when the corresponding
dialect parameter is `None`, or exceeding `max_offset` in page/offset mode,
raises `ConfigurationError` before sending any request.

`search()` returns a generic `Page[E]`:

| Field | Meaning |
|---|---|
| `results` | Validated entities |
| `total` | Total matches, or None when the API does not report it |
| `next_cursor` | Cursor for the next page, or None |
| `page` | The requested page number |
| `meta` | The raw envelope minus the results (facets, group-by) |

## API reference

::: bibliofabric.paging
    options:
      show_root_heading: true
