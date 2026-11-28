# rorifer: Python client for the ROR API v2 (async and sync)

Samuel Mok -- 2026

`rorifer` is a placeholder name. The package will be renamed before its
first release.

rorifer is a Python client for the [ROR API v2](https://ror.readme.io/docs/rest-api),
built on [bibliofabric](https://github.com/utsmok/bibliofabric). The async client is
the source of truth; a generated sync twin (`RoriferSyncClient`,
`OrganizationsSyncClient`) offers the same API without an event loop. The
API needs no credentials.

**Docs:** [utsmok.github.io/bibliofabric/rorifer](https://utsmok.github.io/bibliofabric/rorifer/) -- **License:** MIT

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same API
- **Typed throughout**: Pydantic v2 models for organizations and affiliation
  matches, PEP 561 `py.typed` marker
- **Search, filter, and page**: keyword search, Elasticsearch `query.advanced`,
  filters, and page-by-page iteration with the 500-page cap checked client-side
- **Affiliation matching**: `match_affiliation()` wraps ROR's affiliation matcher
- **Identifier lookup**: `find_by_external_id()` and `find_by_funder_doi()` find a
  record by FundRef, GRID, ISNI, or Wikidata id
- **Data dumps**: list the ROR dumps on Zenodo, stream one to disk, and read its
  150,000 records one at a time with `iter_dump_records()`

## Installation

```bash
uv add rorifer
```

Requires Python >=3.12.

## Quick Start

```python
import asyncio
from rorifer import RoriferClient


async def main():
    async with RoriferClient() as client:
        # Get one record; URL forms like https://ror.org/006hf6230 also work
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

ROR returns up to 10 candidates with a `score` between 0 and 1 and marks one
of them `chosen`.

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

The API serves at most 500 pages of 20 records per query. To read the whole
registry, download a dump:

```python
dumps = await client.dumps.list()
latest = await client.dumps.latest()
path = await client.dumps.download(latest, "ror-data.zip")

from rorifer import index_external_ids, iter_dump_records

records = list(iter_dump_records(path))
fundref = index_external_ids(records, "fundref")
```

## Upstream behavior to know

- **Rejected requests return HTTP 200.** An unknown filter key, a page above
  500, or malformed `query.advanced` syntax produces `{"errors": [...]}` with
  status 200. The client raises `ConfigurationError` with ROR's messages.
- **`query` and `query.advanced` exclude each other.** ROR rejects a request
  that carries both. The keyword search does not find an ISNI, so the
  identifier lookup goes through `query.advanced`.
- **Pages hold 20 records and pages stop at 500.** One query reaches at most
  10,000 records. ROR also warns that paging a query without a filter can
  duplicate or skip records, so use the dump for complete lists.
- **Only active records answer by default.** Pass `all_status=True` to include
  inactive and withdrawn records. `get()` returns any status.
- **`id` is a URL.** Records carry `https://ror.org/<id>`; the client accepts
  that form and the bare id everywhere.
- **`HEAD` is blocked.** The gateway answers `HEAD` with 403, so `exists()`
  sends `GET`.
- **No sorting, field selection, cursors, or batch route.** Passing `sort=`,
  `select=`, or `cursor=` raises `ConfigurationError` without a request.
