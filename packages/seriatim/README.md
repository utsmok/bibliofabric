# seriatim: Python client for the ISSN Portal (async and sync)

`seriatim` is not yet published on PyPI; until its first release it installs
from the bibliofabric workspace.

seriatim is a Python client for the [ISSN Portal](https://portal.issn.org/),
built on [bibliofabric](https://github.com/utsmok/bibliofabric). It reads
ISSN and ISSN-L records as JSON-LD through content negotiation, wraps the
free search over the Portal's HTML result page, and reads the list of Title
Word Abbreviations. It ships an async client and a generated sync twin with
the same API. All wrapped routes are free and need no credentials.

## Install

```bash
uv add seriatim
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from seriatim import SeriatimClient


async def main():
    async with SeriatimClient() as client:
        record = await client.records.get("0028-0836")
        print(record.main_title, record.format)  # Nature. medium:Print
        print(record.issn_l, record.key_title)

        cluster = await client.issn_l.get("0028-0836")
        print([(part.identifier, part.format) for part in cluster.has_part])

        page = await client.search.page("0028-0836")
        print(page.total, [hit.title for hit in page.hits])


asyncio.run(main())
```

The client sends `Accept: application/ld+json` on every request. Every
record model keeps unknown keys, and `record.raw` holds the untouched JSON-LD
node when the Portal publishes a field the model does not know yet.

## Sync usage

The generated sync twin has the same API and works without an event loop.

```python
from seriatim import SeriatimSyncClient

with SeriatimSyncClient() as client:
    record = client.records.get("0028-0836")
    page = client.search.page("nature", page_size=50)
    entries = [e for e in client.ltwa.iterate(limit=100)]
```

## Search and the LTWA table read HTML

The Portal search and the Title Word Abbreviation table have no
machine-readable variant. The clients fetch the public HTML pages and parse
them with the standard library, one page per paced request. See the
[search page](https://utsmok.github.io/bibliofabric/seriatim/search/) and the
[LTWA page](https://utsmok.github.io/bibliofabric/seriatim/ltwa/) for the
parameter reference and the known limits.

## Settings

Settings come from environment variables prefixed with `SERIATIM_` or a
`.env` file. There is no credential field; the SRU Search API and OAI-PMH
need a paid subscription and are not wrapped.

```python
from seriatim import SeriatimSettings

settings = SeriatimSettings(max_requests_per_second=0.5, mailto="your contact address")
```

| Field | Default | Meaning |
|---|---|---|
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Automatic retries for idempotent requests |
| `max_requests_per_second` | `1.0` | Courtesy pace; the Portal publishes no limit |
| `max_concurrency` | `2` | Parallel request bound |
| `user_agent`, `mailto` | `None` | Contact information for the `User-Agent` |

## Development

Regenerate the sync twins with `uv run python scripts/unasync.py --package
seriatim`. Run the suite with `uv run pytest packages/seriatim/tests`; the
live tests run with `uv run pytest -m live_api packages/seriatim/tests` and
cost about a dozen paced requests.
