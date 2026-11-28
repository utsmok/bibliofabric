# Repositories

The `repositories` resource is a view of the [client accounts](https://support.datacite.org/reference/get_repositories.md) restricted to `clientType: repository`. Periodicals are excluded, so this is the catalog for indexing repositories. Ids are lowercase symbols such as `cern.zenodo`.

```python
record = await client.repositories.get("cern.zenodo")
record.symbol
record.re3data  # re3data id, for example "r3d100010468"
record.opendoar
record.software  # repository software, when known
record.certificate  # for example "Core Certified Repository"
record.issn.print
```

## Searching

```python
from dataphora import RepositoryFilters

page = await client.repositories.search(
    RepositoryFilters(year="2024"),
    query="arxiv",
    select=["name", "re3data", "opendoar"],
)
```

`page.meta` carries facet counts by year, certificate, software, and
country.

## DOIs of one repository

```python
page = await client.repositories.dois("cern.zenodo", page_size=25)
```

`dois()` sends a `/dois` search filtered by `client-id`, the same request
the `/repositories/{id}/dois` route serves. All `search()` keyword
arguments forward. For periodical accounts use
[`client.clients.dois()`](clients.md#dois-of-one-client) instead.
