# seriatim: Python client for the ISSN Portal (async and sync)

`seriatim` is not yet published on PyPI; until its first release it installs
from the bibliofabric workspace.

seriatim is a Python client for the [ISSN Portal](https://portal.issn.org/),
built on [bibliofabric](https://github.com/utsmok/bibliofabric). It reads
ISSN and ISSN-L records as JSON-LD, wraps the free search over the Portal's
HTML result page, and reads the list of Title Word Abbreviations. It ships
an async client and a generated sync twin with the same API. All wrapped
routes are free and need no credentials.

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

        cluster = await client.issn_l.get("0028-0836")
        print([(p.identifier, p.format) for p in cluster.has_part])

        page = await client.search.page("0028-0836")
        print(page.total, [hit.title for hit in page.hits])

        entry = await client.ltwa.page(search="journal")
        print(entry.entries[0])


asyncio.run(main())
```

The client sends `Accept: application/ld+json` on every request. Record
models keep unknown keys, and `record.raw` holds the untouched JSON-LD node
when the Portal publishes a field the model does not know yet.

## Sync usage

The generated sync twin has the same API and works without an event loop.

```python
from seriatim import SeriatimSyncClient

with SeriatimSyncClient() as client:
    record = client.records.get("0028-0836")
    for hit in client.search.iterate("nature", limit=20):
        print(hit.issn, hit.title)
```

## Settings

Settings come from environment variables prefixed with `SERIATIM_` or a
`.env` file. There is no credential field; the SRU Search API and OAI-PMH
need a paid subscription and are not wrapped.

| Field | Default | Meaning |
|---|---|---|
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Automatic retries for idempotent requests |
| `max_requests_per_second` | `1.0` | Courtesy pace; the Portal publishes no limit |
| `max_concurrency` | `2` | Parallel request bound |
| `user_agent`, `mailto` | `None` | Contact information for the `User-Agent` |

## Package pages

- [ISSN and ISSN-L records](records.md)
- [Free search](search.md)
- [Title Word Abbreviations](ltwa.md)
- [Upstream quirks](upstream-quirks.md)
- [Reference](reference.md)
