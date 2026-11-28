# Recommendations

`client.recommendations` talks to the `/recommendations/v1` routes and
returns `Paper` models. Both routes answer `{"recommendedPapers": [...]}`.

## For one paper

```python
papers = await client.recommendations.for_paper(
    "DOI:10.1038/nature12373", fields=["title", "year"], limit=10
)
```

The id takes the same forms as a paper get (`DOI:`, `ARXIV:`, a bare S2
id, and so on). This route works without an API key.

## For a list of papers

```python
papers = await client.recommendations.for_list(
    positive_paper_ids=["ARXIV:2106.15928"],
    negative_paper_ids=["DOI:10.1038/nature12373"],
    fields=["title", "year"],
    limit=10,
)
```

`positive_paper_ids` steers toward these papers and
`negative_paper_ids` steers away; at least one id is required. The route
is a read-only `POST` and is sent with retries. It is more restricted
upstream than the single-paper route and may answer 400 on the anonymous
pool.
