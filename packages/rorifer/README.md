# rorifer: Python client for the ROR API v2 (async and sync)

Samuel Mok -- 2026

rorifer is a Python client for the [ROR API v2](https://ror.readme.io/docs/rest-api),
built on [bibliofabric](https://github.com/utsmok/bibliofabric). The async client is
the source of truth; a generated sync twin (`RoriferSyncClient`,
`OrganizationsSyncClient`, `DumpsSyncClient`) offers the same API without an event
loop. The API needs no credentials.

The package is not yet published on PyPI. Until the first release, use it from a
checkout of the `bibliofabric` workspace, where `uv sync --all-packages` installs it
together with the `bibliofabric` 0.8 it needs.

**Docs:** [utsmok.github.io/bibliofabric/rorifer](https://utsmok.github.io/bibliofabric/rorifer/) -- **License:** MIT

Requires Python 3.12 or newer.

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same API.
- **Every read route of the API**: one record (`get`, `exists`), search (`search`,
  `iterate`, `collect`, `first`, `count`), the affiliation matcher
  (`match_affiliation`), and the lookups by external id (`find_by_external_id`,
  `find_by_funder_doi`).
- **Typed models**: Pydantic v2 models for organizations, affiliation matches, and
  dumps. Every field that ROR returns is kept. PEP 561 `py.typed` marker.
- **Data dumps**: `dumps.list()` lists the ROR releases on Zenodo,
  `dumps.download()` streams one to disk, and `iter_dump_records()` reads its
  150,000 records one at a time.
- **Rate limits**: the client paces itself to 6 requests per second on the ROR API
  and to 30 per minute on the Zenodo search that lists the dumps.

## Quick Start

```python
import asyncio
from rorifer import RoriferClient


async def main():
    async with RoriferClient() as client:
        # Get one record; https://ror.org/006hf6230 and ror.org/006hf6230 also work
        org = await client.organizations.get("006hf6230")
        print(org.display_name, org.status)

        # Keyword search over names and external ids (20 records per page)
        page = await client.organizations.search(query="university of twente")
        print(page.total, [o.display_name for o in page.results])

        # Filter by type and country; page through every match
        async for org in client.organizations.iterate(
            {"types": ["education", "nonprofit"], "country.country_code": "NL"},
            advanced="established:[1900 TO 2000]",
            limit=60,
        ):
            print(org.id, org.established)


asyncio.run(main())
```

### Sync quick start

```python
from rorifer import RoriferSyncClient

with RoriferSyncClient() as client:
    org = client.organizations.get("https://ror.org/006hf6230")
    print(org.display_name)
    for match in client.organizations.match_affiliation(
        "University of Twente, Enschede, Netherlands"
    ):
        print(match.score, match.chosen, match.organization.display_name)
```

## Affiliation matching

```python
matches = await client.organizations.match_affiliation("Dept of Physics, MIT")
chosen = next(m.organization for m in matches if m.chosen)
```

ROR returns up to 10 candidates with a `score` between 0 and 1 and marks one of them `chosen`.

## Identifier lookup and funder crosswalk

```python
from rorifer import fundref_doi_from_id, fundref_id_from_doi

# A Crossref Funder Registry DOI leads to the ROR record that carries it
nsf = await client.organizations.find_by_funder_doi("10.13039/100000001")

fundref_id_from_doi("https://doi.org/10.13039/100000001")  # "100000001"
fundref_doi_from_id("100000001")  # "10.13039/100000001"

# Any spelling: the ISNI also matches in its grouped form "0000 0004 0399 8953"
await client.organizations.find_by_external_id("0000000403998953", id_type="isni")
```

## Data dumps

The API serves at most 500 pages of 20 records per query. To read the whole registry, download a dump:

```python
dumps = await client.dumps.list()
latest = await client.dumps.latest()
path = await client.dumps.download(latest, "ror-data.zip")

from rorifer import index_external_ids, iter_dump_records

records = list(iter_dump_records(path))
fundref = index_external_ids(records, "fundref")
```

`dumps.list()` reads the Zenodo search with `all_versions=true`, so every release is one record. `dumps.latest()` reads the Zenodo concept record of the dumps, which Zenodo redirects to the newest release.

## Upstream behavior to know

- **Rejected requests return HTTP 200.** An unknown filter key, a page above 500, or malformed `query.advanced` syntax produces `{"errors": [...]}` with status 200. The client raises `ConfigurationError` with ROR's messages.
- **`query` and `query.advanced` exclude each other.** ROR rejects a request that carries both. The keyword search does not find an ISNI, so the identifier lookup goes through `query.advanced`.
- **Pages hold 20 records and stop at page 500.** One query reaches at most 10,000 records. A query with more results raises `ConfigurationError` when page 501 would be needed. ROR also warns that paging a query without a filter can duplicate or skip records, so use the dump for complete lists.
- **No page size, sorting, field selection, cursors, or batch route.** Passing `page_size=`, `sort=`, `select=`, or `cursor=` raises `ConfigurationError` without a request.
- **Only active records answer a search by default.** Pass `all_status=True` to include inactive and withdrawn records. `get()` returns any status.
- **`id` is a URL.** Records carry `https://ror.org/<id>`; the client accepts that form, `ror.org/<id>`, and the bare id everywhere.
- **`HEAD` is blocked.** The gateway answers `HEAD` with 403, so `exists()` sends `GET`.
- **Rate limit.** ROR documents a limit of 2,000 requests per 5 minutes per IP address. Registration for a client id is paused. `RORIFER_MAX_REQUESTS_PER_SECOND` sets the pace (default 6).
