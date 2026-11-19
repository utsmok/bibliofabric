# Funders

`client.funders` covers `/funders` and `/funders/{doi}`.

```python
from stavrophora import FunderFilters

funder = await client.funders.get("10.13039/100000001")
funder.hierarchy_names  # child funder ids and names, on single records only
funder.hierarchy  # nested child tree, on single records only

page = await client.funders.search(
    FunderFilters(location="Netherlands"), query="university"
)
```

`location` is a case-sensitive country name. The route accepts `query` plus `filter`; `sort` and `select` raise `ConfigurationError` client-side.

`funders.works(doi)` returns a works client bound to `/funders/{doi}/works`; see [Works](works.md#scoped-works). The scoped route already includes descendants' works. With `include_descendants=True`, the funder's id plus its descendant registry ids are ORed into every request's `funder` filter, which pins the result set to the listed ids:

```python
scope = client.funders.works("10.13039/100000002", include_descendants=True)
page = await scope.search(page_size=5)
```

The id set comes from the funder record and is fetched once per scope. Requests that carry their own `funder` filter raise `ConfigurationError`, since the two would silently AND together.

`funders.descendants(doi)` returns the descendant registry ids from the funder record, in Crossref's bare form (`"100000025"`); it returns an empty list for funders without a hierarchy:

```python
descendants = await client.funders.descendants("10.13039/100000002")
```
