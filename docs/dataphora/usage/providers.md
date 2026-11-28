# Providers

The `providers` resource reads the [DataCite members and consortium organizations](https://support.datacite.org/reference/get_providers.md) that manage clients and prefixes. Ids are lowercase symbols such as `datacite` or `cern`.

```python
record = await client.providers.get("datacite")
record.displayName
record.memberType  # "direct_member", "consortium", ...
record.region  # "EMEA", "AMER", "APA"
record.rorId
```

## Searching

```python
from dataphora import ProviderFilters

page = await client.providers.search(
    ProviderFilters(member_type="consortium", region="EMEA"),
    select=["symbol", "displayName", "country"],
)
```

## DOIs of one provider

```python
page = await client.providers.dois("datacite", page_size=25)
```

`dois()` sends a `/dois` search filtered by `provider-id`, the same request
the `/providers/{id}/dois` route serves. All `search()` keyword arguments
forward.

## Production statistics

```python
totals = await client.providers.totals()
totals[0].id
totals[0].temporal["last_year"][0].count
```

`totals()` reads `/providers/totals`. The response is one unpaged entry per
provider, several hundred kilobytes.

## Prefix assignments

The provider side of the prefix ledger lives in
`client.provider_prefixes`; each record carries only timestamps, with the
prefix and provider as relationships.

```python
page = await client.provider_prefixes.search(page_size=50)
page.results[0].relationships["prefix"].data.id
```
