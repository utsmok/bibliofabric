# Scholix

`client.scholix` searches Scholexplorer, the OpenAIRE service for
scholarly links. It talks to `api.scholexplorer.openaire.eu` through a
second internal client that shares the Graph client's credentials and
throttles itself to one request per second, because the host sends no
rate-limit headers.

```python
from aireloom import ScholixFilters

page = await client.scholix.search_links(
    ScholixFilters(sourcePid="10.1038/nature12373"), page_size=25
)
page.results  # list[ScholixRelationship]
```

The API requires one of `sourcePid`, `targetPid`, `sourcePublisher`,
`targetPublisher`, `sourceType`, or `targetType`; a bare query returns 400.

## Versions

V3 is the default endpoint. Queries with `from_date` or `to_date` are
routed to V2 automatically, because the V3 endpoint accepts date parameters
but returns zero rows for every value (see [upstream quirks](../quirks.md)):

```python
page = await client.scholix.search_links(
    ScholixFilters(sourcePid="10.1038/nature12373", from_date="2020-01-01")
)
```

`search_links_v2` and `iterate_links_v2` force the V2 endpoint.

## Providers and publishers

```python
providers = await client.scholix.list_link_providers()
publishers = await client.scholix.list_link_publishers(in_target=True, name="Elsevier")
kpi = await client.scholix.get_kpi()  # Prometheus text
```

The provider and publisher helpers use the V2 routes.
