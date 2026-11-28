# Prefixes

The `prefixes` resource lists the [DOI prefixes](https://support.datacite.org/reference/get_prefixes.md) (10-prefixed strings such as `10.5438`) and their assignment ledger. A prefix record itself carries almost nothing; its assignments point at the provider and clients that use it.

## Browsing prefixes

```python
record = await client.prefixes.get("10.5438")
record.prefix
```

```python
from dataphora import PrefixFilters

page = await client.prefixes.search(PrefixFilters(state="unallocated"))
page = await client.prefixes.search(prefix="10.52")
```

## DOIs of one prefix

```python
page = await client.prefixes.dois("10.5438", page_size=25)
```

`dois()` sends a `/dois` search filtered by `prefix`, the same request the
`/prefixes/{id}/dois` route serves. All `search()` keyword arguments
forward.

## Who holds a prefix

The ledger lives in two resources, and both carry only `createdAt` and
`updatedAt`; the prefix, the client, and the provider are relationships.

```python
page = await client.client_prefixes.search(page_size=50)
assignment = page.results[0]
assignment.relationships["prefix"].data.id
assignment.relationships["client"].data.id
```

```python
page = await client.provider_prefixes.search(page_size=50)
page.results[0].relationships["provider"].data.id
```

## Production statistics

```python
totals = await client.prefixes.totals("cern.zenodo")
totals[0].id  # "10.5281"
totals[0].count
totals[0].states[0].count
```

`totals()` reads `/prefixes/totals` with the required `client-id`
parameter: one unpaged entry per prefix of the client, with the same
`count`, `temporal`, and `states` fields as the client and provider totals.
Pass a list of client ids to cover several clients. Without `client-id` the
route answers `204 No Content`, so the method requires it.
