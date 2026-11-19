# Funders

`client.funders` covers `/funders` and `/funders/{doi}`.

```python
from stavrophora import FunderFilters

funder = await client.funders.get("10.13039/100000001")
funder.hierarchy_names       # child funder ids and names, on single records only
funder.hierarchy             # nested child tree, on single records only

page = await client.funders.search(
    FunderFilters(location="Netherlands"), query="university"
)
```

`location` is a case-sensitive country name. The route accepts `query` plus `filter`; `sort` and `select` raise `ConfigurationError` client-side.

`funders.works(doi)` returns a works client bound to `/funders/{doi}/works`; see [Works](works.md#scoped-works).
