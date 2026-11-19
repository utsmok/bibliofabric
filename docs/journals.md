# Journals

`client.journals` covers `/journals` and `/journals/{issn}`.

```python
journal = await client.journals.get("20493630")  # ISSN normalized to 2049-3630
journal.primary_title  # scalar title on this route
journal.counts.total_dois

page = await client.journals.search(query="neurology", page_size=5)
```

The route accepts only plain `query`. `sort`, `select`, and `filter` raise `ConfigurationError` client-side, because the API answers 400 to them.

`journals.works(issn)` returns a works client bound to `/journals/{issn}/works`; see [Works](works.md#scoped-works).
