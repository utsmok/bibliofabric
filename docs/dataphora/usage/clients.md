# Clients

The `clients` resource reads the [repository accounts](https://support.datacite.org/reference/get_clients.md) that register DOIs. Ids are lowercase symbols such as `datacite.datacite` or `cern.zenodo`.

```python
record = await client.clients.get("datacite.datacite")
record.symbol
record.clientType  # "repository" or "periodical"
record.issn.electronic
record.domains
```

## Searching

```python
from dataphora import ClientFilters

page = await client.clients.search(
    ClientFilters(client_type="repository", year="2024"),
    query="zenodo",
    select=["name", "symbol"],
)
```

`page.meta` carries the facet counts (years, providers, client types).

## DOIs of one client

```python
page = await client.clients.dois("cern.zenodo", page_size=25)
```

`dois()` sends the same request as the `/clients/{id}/dois` route: a
`/dois` search filtered by `client-id`. All `search()` keyword arguments
(`query`, `sort`, `select`, `cursor`, and friends) forward.

## Production statistics

```python
totals = await client.clients.totals()
totals[0].id
totals[0].count
totals[0].temporal["this_year"][0].count
totals[0].states[0].count
```

`totals()` reads `/clients/totals`. The response is one unpaged entry per
client (several megabytes), so cache it if you call it repeatedly.

## Prefix assignments

Each prefix assignment pairs one prefix with one client. The prefix and the
account are relationships; the resource itself only carries timestamps.

```python
page = await client.client_prefixes.search(page_size=50)
assignment = page.results[0]
assignment.relationships["prefix"].data.id
assignment.relationships["client"].data.id
```
