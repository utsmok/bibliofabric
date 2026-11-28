# quiddita

quiddita is a placeholder name. The package will be renamed before its first release.

quiddita is a Python client for [Wikidata](https://www.wikidata.org), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It covers Wikidata's three read interfaces: the MediaWiki Action API (`wbgetentities`, `wbsearchentities`, `wbgetclaims`), the Wikibase REST API (items, properties, statements, per-language term routes), and the SPARQL query service. It types every payload with Pydantic models, batches `wbgetentities` id requests at the API's 50-id limit, and ships an async client plus a generated sync twin with the same API. The API needs no credentials, but all three services ask for a descriptive `User-Agent` with contact information, which the client builds for you.

## Install

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
        print(entity.description(), entity.sitelinks["enwiki"].title)

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

`client.entities` exposes `get()`, `batch_get()`, and `iterate_ids()`. `client.search` exposes `search()`, `iterate()`, `collect()`, and the REST routes `search_items()` and `search_properties()`. `client.claims`, `client.sitelinks`, `client.items`, `client.properties`, and `client.statements` cover the Action API and REST read routes. `client.sparql` talks to the query service on `query.wikidata.org`.

## Sync usage

`QuidditaSyncClient` is generated from the async source and behaves the same. The sync client uses plain `httpx.Client` and never starts or touches an event loop, so it works in scripts, in Jupyter, in threads, and when called from inside a running event loop.

```python
from quiddita import QuidditaSyncClient

with QuidditaSyncClient() as client:
    entity = client.entities.get("Q42")
    print(entity.claims["P31"][0].mainsnak.datavalue)
```

## Settings

`QuidditaSettings` loads from environment variables prefixed with `QUIDDITA_` and from a `.env` file in the working directory. The defaults follow the pace Wikidata's own guides ask for: serial requests at 2 per second against `www.wikidata.org`, and one SPARQL query every 2 seconds in the separate `sparql` rate class. `QUIDDITA_USER_AGENT` and `QUIDDITA_MAILTO` feed the `User-Agent`; `QUIDDITA_TIMEOUT`, `QUIDDITA_MAX_RETRIES`, and the other shared fields of `bibliofabric.config.BaseApiSettings` also apply.

## Where to go next

- [Entities](entities.md) covers `wbgetentities`, batching, id iteration, and the `Special:EntityData` routes.
- [Search](search.md) covers `wbsearchentities`, the REST search routes, and the REST suggest routes.
- [Claims and statements](claims.md) covers `wbgetclaims` and the REST statement routes.
- [Site links](sitelinks.md) covers the site link resources.
- [Lexemes](lexemes.md) covers the WikibaseLexeme REST read routes.
- [SPARQL](sparql.md) covers the query service and how the two hosts share one rate limiter.
- [Utility modules](utilities.md) covers badges, HTML formatting, value parsing, property suggestions, and constraint checks.
- [Upstream quirks](upstream-quirks.md) lists what the live services do differently from their documentation.
- The [API reference](reference.md) is generated from the source.
