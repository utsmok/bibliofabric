# DOIs

The `dois` resource reads [DataCite DOI records](https://support.datacite.org/docs/api-get-lists). Anonymous reads see `findable` records only; `registered` and `draft` states need a login.

## Fetching one DOI

```python
doi = await client.dois.get("10.5438/0012")
doi.title
doi.resource_type  # resourceTypeGeneral, for example "Text"
doi.publicationYear
doi.client_id  # repository account that registered the DOI
doi.provider_id  # DataCite member behind that account
doi.creators[0].name
doi.relationships["references"]
```

`get()` accepts bare DOIs and `https://doi.org/` links, in any case.
`exists()` answers `True` or `False` with one `HEAD` request. An unknown DOI
raises `NotFoundError`.

## Searching

```python
page = await client.dois.search(
    {"client-id": "cern.zenodo", "resource-type-id": "dataset"},
    query="photosynthesis",
    sort="-updated",
    select=["doi", "titles", "publicationYear"],
    page_size=100,
)
page.total, page.results, page.next_cursor, page.meta
```

`search()` pages with `page[number]`, which DataCite limits to the first
10,000 records of a query. `page.meta` carries the raw envelope with its
facet counts.

### Filters

Pass a `DoiFilters` model or a plain mapping. Values that are lists join
with commas, which DataCite reads as OR; different keys AND.

```python
from dataphora import DoiFilters

filters = DoiFilters(
    prefix=["10.5438", "10.5281"],
    resource_type_id="text",
    schema_version="4",
    affiliation_id="https://ror.org/006hf6230",
    funded_by="https://ror.org/01cwqze88",
    created="2024,2025",
    has_affiliation=True,
)
page = await client.dois.search(filters)
```

DataCite silently ignores unknown query parameters, so a typo in a mapping
returns an unfiltered result. The typed model fields are the safety net.
Date filters take years, not ISO timestamps.

### Paging deep result sets

`iterate()` and `collect()` walk with `page[cursor]`, which has no depth
limit. Cursor walks always run in `created` ascending order, whatever
`sort` says.

```python
async for record in client.dois.iterate(filters):
    ...

records = await client.dois.collect(filters, limit=1000)
```

`count()` returns `meta.total` with a one-record request.

## Per-DOI activities

```python
activities = await client.dois.activities("10.5438/0012")
activities[0].action  # "create", "update"
activities[0].version
activities[0].changes  # attribute name -> [old, new]
```

The global `/activities` route is available through `client.activities` with
the same generic operations. The `prov:*` attribute keys land in
`model_extra`.

## Extras the API trims by default

DataCite omits some attributes unless the request asks for them. Forward the
flags with `params=`:

```python
doi = await client.dois.get("10.5438/0012", params={"detail": "true"})
page = await client.dois.search(params={"affiliation": "true", "publisher": "true"})
```

`detail=true` adds `xml`, `viewsOverTime`, `citationsOverTime`, and the
relationship counts; `affiliation=true` and `publisher=true` add
identifier details that schema 4.3+ records carry.
