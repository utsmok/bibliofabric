# zenotheca: Python client for the Zenodo REST API (async and sync)

Samuel Mok -- 2026

The package is not yet published on PyPI. Until the first release, use it
from a checkout of the `bibliofabric` workspace, where `uv sync
--all-packages` installs it together with the `bibliofabric` 0.8 it needs.

zenotheca is a Python client for the
[Zenodo REST API](https://developers.zenodo.org/), built on
[bibliofabric](https://github.com/utsmok/bibliofabric). The async client is
the source of truth; a generated sync twin (`ZenothecaSyncClient`,
`ZenothecaRecordsSyncClient`, `ZenothecaCommunitiesSyncClient`) offers the
same API without an event loop. Public reads need no credentials.

**Docs:** [utsmok.github.io/bibliofabric/zenotheca](https://utsmok.github.io/bibliofabric/zenotheca/) -- **License:** MIT

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same API
- **Typed throughout**: Pydantic v2 models for records, files,
  communities, vocabularies, and the OAI-PMH answers, PEP 561 `py.typed`
  marker
- **Search and page**: Elasticsearch `q` clause builders, sort options, the
  `all_versions` switch, and page-by-page iteration with the 10,000-result
  window checked client-side
- **Versions**: list every version of a concept and resolve the newest one
- **Files and downloads**: list the files of a record and stream one file to
  disk through Zenodo's `content` route
- **Vocabularies**: the reference lists (`resourcetypes`, `licenses`,
  `languages`, `communitytypes`) with search, iteration, and entry fetch
- **OAI-PMH**: the six verbs of `https://zenodo.org/oai2d`, with typed
  envelopes and iteration over resumption tokens
- **Subcommunities**: list the children of one community
- **Optional token**: `ZENOTHECA_API_TOKEN` sends `Authorization: Bearer`
  and raises the page size cap from 25 to 100

## Installation

```bash
uv sync --all-packages
```

The command runs in a checkout of the `bibliofabric` workspace and installs
zenotheca with the `bibliofabric` 0.8 it needs. `uv add zenotheca` works once
the package is on PyPI. Requires Python >=3.12.

## Quick Start

```python
import asyncio
from zenotheca import ZenothecaClient, community, resource_type


async def main():
    async with ZenothecaClient() as client:
        # One record by version id, DOI, or URL; a concept id answers the
        # newest version
        record = await client.records.get("10.5281/zenodo.24378467")
        print(record.title, record.metadata.version)

        # Search: the ROR community datasets, newest update first
        page = await client.records.search(
            {"type": "dataset"},
            query=community("ror-data"),
            sort="mostrecent",
        )
        print(page.total, [record.title for record in page.results])

        # Every version of a concept, newest first
        versions = await client.records.versions(record.id, page_size=5)
        print(versions.total, [record.metadata.version for record in versions.results])


asyncio.run(main())
```

### Sync quick start

```python
from zenotheca import ZenothecaSyncClient

with ZenothecaSyncClient() as client:
    record = client.records.get(24378467)
    print(record.title)

    for record in client.communities.records("ror-data", limit=3):
        print(record.id, record.title)
```

## Records, files, and communities

`client.records` exposes `get()`, `exists()`, `search()`, `iterate()`,
`collect()`, `first()`, `count()`, `versions()`, `latest()`, `files()`, and
`download_file()`. `client.communities` exposes `search()`, `get()`,
`iterate()`, `records()`, and `subcommunities()`. `client.vocabularies`
exposes `search()`, `iterate()`, and `get()`. `client.oai` exposes
`identify()`, `list_metadata_formats()`, `list_sets()`,
`list_identifiers()`, `list_records()`, `get_record()`,
`iterate_records()`, and `iterate_identifiers()`. See the usage pages for
details.

## Upstream behavior to know

- **No token needed for reads.** Some routes need an account
  (`/api/deposit/depositions` answers 403 without one), but everything this
  client wraps is public. With `ZENOTHECA_API_TOKEN` set, requests carry
  a bearer header and the page size cap rises to 100 (documented, not
  verified live).
- **Page size caps at 25** without an access token; larger values answer
  HTTP 400. A `page * size` product above the Elasticsearch window of
  10,000 also answers 400; the client rejects it before sending.
- **Zenodo rejects requests without a `User-Agent` header.** The client
  always sends one.
- **Search routes are throttled harder.** Without a token, the record
  search and the search over the records of one community allow 30
  requests per minute; every other route allows 133. The client paces the
  search routes at one request every 2 seconds and everything else at 2
  requests per second (`ZENOTHECA_RATE_LIMITS` sets the classes).
- **A concept id redirects.** `GET /api/records/{conceptrecid}` answers 302
  for the newest version, and `versions/latest` answers 301; the client
  follows both.

See [upstream quirks](https://utsmok.github.io/bibliofabric/zenotheca/upstream-quirks/)
for the full list.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package-specific bits:

```bash
uv run python scripts/unasync.py --package zenotheca   # regenerate _sync twins
uv run pytest packages/zenotheca/tests                 # offline suite
uv run pytest -m live_api packages/zenotheca/tests     # live smoke tests
```
