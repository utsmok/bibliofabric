# Paging

Paging behavior is declared once per API in a frozen `QueryDialect` and shared
by all resource clients of that API.

```python
DIALECT = QueryDialect(
    page_size_param="per_page",
    max_page_size=200,
    default_page_size=25,
    page_param="page",  # None when the API has no page numbers
    page_start=1,  # 0 for OpenAIRE links and Scholix
    offset_param=None,  # "offset" for Crossref; replaces page_param
    cursor_param=None,  # "cursor" enables cursor paging
    cursor_start="*",
    sort_param="sort",
    query_param=None,  # free-text search parameter
    select_param=None,  # field selection parameter
)
```

`iterate()` uses cursor paging when `cursor_param` is set; otherwise it walks
page numbers (`page_param`) or offsets (`offset_param`, where page N becomes
`offset=(N - page_start) * page_size`).

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
