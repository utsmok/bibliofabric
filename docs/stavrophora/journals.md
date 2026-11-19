# Journals

`client.journals` covers `/journals` and `/journals/{issn}`.

```python
journal = await client.journals.get("20493630")  # ISSN normalized to 2049-3630
journal.primary_title  # scalar title on this route
journal.counts.total_dois

page = await client.journals.search(query="neurology", page_size=5)
```

The route accepts only plain `query`. `sort`, `select`, and `filter` raise `ConfigurationError` client-side, because the API answers 400 to them.

`journals.dois_by_year(issn)` returns DOI counts per issued year from the journal record's `breakdowns.dois-by-issued-year`, as a `dict[int, int]`:

```python
counts = await client.journals.dois_by_year("20493630")  # {2026: 838, 2020: 729, ...}
```

`journals.works(issn)` returns a works client bound to `/journals/{issn}/works`; see [Works](works.md#scoped-works).
