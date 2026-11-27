# Works

`client.works` covers the `/works` route. It accepts queries, filters, sorting, field selection, and every paging style Crossref offers.

## Search

```python
page = await client.works.search(
    WorksFilters(type="journal-article", from_pub_date="2024-01-01"),
    query="proteomics",
    sort="is-referenced-by-count:desc",
    select=["DOI", "title"],
    page=1,
    page_size=20,
)
page.results  # list[Work]
page.total  # message.total-results
page.next_cursor  # cursor for the next page, or None
page.meta  # the envelope minus the results (facets, totals)
```

`sort` takes one field, optionally with `:asc` or `:desc`. Crossref accepts a single sort field; two fields raise `ConfigurationError`.

`select` takes a list of field names. Works also accept the `query.*` sub-fields through `params` (prefer `query.bibliographic` for citation matching; `query.title` is deprecated by Crossref):

```python
page = await client.works.search(params={"query.bibliographic": "crispr"})
```

Pass `on_error="skip"` with a `failures` list to drop records that fail validation instead of raising `ValidationError` for the whole page.

## Filters

`WorksFilters` mirrors the Crossref filter list; kebab-case wire names are handled by aliases. A list value uses the repeated-key OR form (`filter=doi:a,doi:b`), and different keys AND together.

```python
from stavrophora import WorksFilters

filters = WorksFilters(
    type="journal-article",
    has_abstract=True,
    doi=["10.1038/nature12373", "10.1109/tip.2009.2037465"],
)
page = await client.works.search(filters)
```

Unknown filter names are passed through as written.

## Paging

Crossref caps `offset + rows` at 10,000 and `rows` at 1,000. `search(page=..., page_size=...)` raises `ConfigurationError` before sending a request past that cap. Use `iterate()` for deep result sets.

```python
async for work in client.works.iterate(filters, query="crispr"):
    ...
```

`iterate()` pages with `cursor`, defaults to 1,000 rows, and repeats every parameter on each page. It rejects the `issued` and `published*` sorts, which the API no longer allows with cursors. `on_page(page_number, next_cursor)` records checkpoints; pass a saved cursor back with `cursor=` to resume. `collect(limit=100)` gathers results into a list, and `first()` returns the first match or `None`.

`count()` requests zero rows (`rows=0`) and returns the total.

## Batch DOI lookup

```python
works = await client.works.batch_get_by_doi(dois)
works["10.1038/nature12373"]
```

The helper batches 50 DOIs per request through the repeated-key OR form, runs the batches concurrently, and returns a dict keyed by bare lowercase DOI. DOIs that return nothing are absent from the dict.

## Existence checks and versions

```python
registered = await client.works.exists("10.1038/nature12373")
```

`exists()` sends a HEAD request, which Crossref documents as an existence check, so no record body is transferred. It returns `False` for unknown DOIs (404).

```python
work = await client.works.latest_version("10.12688/f1000research.141553.1")
all_updates = await client.works.latest_version(
    "10.12688/f1000research.141553.1", update_types=None
)
```

`latest_version()` resolves a DOI to the newest record in its Crossmark update chain. Older records carry `updated-by` entries naming the works that updated them; by default only `("new_version", "new_edition")` entries are followed so retractions and corrections are not mistaken for newer versions. Pass `update_types=None` to follow all Crossmark update types, or pass a custom collection of update-type names. A DOI without matching update data is returned unchanged.

## Facets, sample, agency

```python
facets = await client.works.facets(filters, facets=("type-name",), count=10)
# {"type-name": {"journal-article": 123, ...}}
```

`facets()` returns `{facet_name: {value: count}}` and drops Crossref's `value-count` per facet. `count` caps the values per facet (the API allows up to 1,000).

```python
page = await client.works.sample(50)  # random draw, max 100
agency = await client.works.agency("10.1038/nature12373")
agency.agency.id  # "crossref"
```

`sample(n)` sends `sample=n` without `rows` or `offset`, so the result is a random draw rather than the head of the result set.

## Scoped works

Every parent resource exposes a `works()` method that returns a `ScopedWorksResource` with the full works list, search, iterate, count, facets, sample, and batch methods (single-work methods such as `get`, `exists`, `agency`, and `latest_version` are omitted because Crossref serves them only at `/works/{doi}`):

```python
page = await client.journals.works("20493630").search(sort="score")
page = await client.funders.works("10.13039/100000001").search()
page = await client.members.works(297).search()
page = await client.types.works("journal-article").search()
page = await client.prefixes.works("10.1038").search()
```

Identifiers are normalized: ISSNs are hyphenated, DOIs are lowercased with URL prefixes stripped, and integer member ids are accepted.

See the [API reference](reference.md) for the full signatures.
