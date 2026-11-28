# quiddita: Python client for Wikidata (async and sync)

`quiddita` is not yet published on PyPI; until its first release it installs
from the bibliofabric workspace.

quiddita is a Python client for [Wikidata](https://www.wikidata.org),
built on [bibliofabric](https://github.com/utsmok/bibliofabric). It covers all
three read interfaces: the MediaWiki Action API (`wbgetentities`,
`wbsearchentities`, `wbgetclaims`), the Wikibase REST API (items, properties,
statements, term routes), and the SPARQL query service on
`query.wikidata.org`. The async client is the source of truth; a generated
sync twin (`QuidditaSyncClient`) offers the same API without an event
loop. The API needs no credentials.

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same API
- **Typed throughout**: Pydantic v2 models for entities, claims, snaks, REST
  statements, search hits, and SPARQL 1.1 JSON results, PEP 561 `py.typed`
- **Batches and iteration**: `wbgetentities` at the API's 50-id limit, chunked
  `batch_get()`, and ordered `iterate_ids()` over unbounded id lists
- **Two hosts, one pace**: the SPARQL client shares the settings object and
  the rate limiter with the main client through rate classes
- **Search everywhere**: `wbsearchentities` with `continue` paging plus the
  REST `search/items` and `search/properties` routes and the REST
  `suggest/items` and `suggest/properties` routes
- **Every entity serialization**: `Special:EntityData` per format (`json`
  parsed into the typed model, RDF formats as text) with revision support
  and the `/entity/{id}` content-negotiation route
- **Lexemes**: the WikibaseLexeme REST read route with forms and senses
- **Utility modules**: badges, HTML formatting (`wbformatentities`,
  `wbformatvalue`), value parsing (`wbparsevalue`), property suggestions
  (`wbsgetsuggestions`), and constraint checks (`wbcheckconstraints`)
- **Polite defaults**: serial requests at 2 per second and one SPARQL query
  every 2 seconds, per Wikidata's own data access guides, with a descriptive
  `User-Agent`

## Installation

```bash
uv add quiddita
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from quiddita import QuidditaClient


async def main():
    async with QuidditaClient() as client:
        entity = await client.entities.get("Q42")
        print(entity.description(), entity.claims["P31"][0].mainsnak.property)

        batch = await client.entities.batch_get(["Q42", "P31", "L1"])
        print(sorted(batch))

        page = await client.search.search(query="douglas adams")
        print([hit.id for hit in page.results])

        result = await client.sparql.query(
            "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 } LIMIT 5"
        )
        print(result.rows())


asyncio.run(main())
```

## Documentation

- Package docs: [utsmok.github.io/bibliofabric/quiddita](https://utsmok.github.io/bibliofabric/quiddita/)
- [Upstream quirks](https://github.com/utsmok/bibliofabric/blob/main/docs/quiddita/upstream-quirks.md)

## License

MIT
