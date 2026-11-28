# archeion: Project Guide

archeion is an async + generated-sync Python client for the arXiv API, built on bibliofabric 0.8. Not yet published. It is the first Wave 2 library.

## Architecture

| Path | Contents |
|---|---|
| `_async/client.py` | `ArcheionClient(BaseApiClient)`: base URL, `Accept: application/atom+xml`, the `query` resource |
| `_async/query.py` | `QueryClient`: `search`, `iterate`, `get`, `batch_get`, `count` on `/api/query` |
| `atom.py` | `parse_feed()`: Atom XML to plain dicts with the stdlib `xml.etree` parser; error feeds raise `ConfigurationError` |
| `unwrapper.py` | `ArcheionUnwrapper` over the parsed feed dict |
| `models.py` | `ArxivEntry`, `ArxivAuthor`, `ArxivLink` (`extra="allow"`) |
| `dialect.py` | Base URL, page size limits, sort values |
| `config.py` | `ArcheionSettings` (`ARCHEION_` prefix), 1/3 request per second, concurrency 1 |

`QueryClient` does not subclass `ResourceClient`: the API answers XML and pages by `start` offset, so the client parses the feed itself and builds `Page` objects. `iterate()` validates entry by entry instead of re-yielding a list, because the generated sync twin would otherwise trip ruff's `UP028`.

## Upstream facts (verified 2026-11-28)

- `/api/query` takes `search_query`, `id_list` (comma-separated), `start`, `max_results`, `sortBy` (`relevance`, `lastUpdatedDate`, `submittedDate`), and `sortOrder` (`ascending`, `descending`).
- A malformed id answers HTTP 400 with an Atom error feed whose entry `id` starts with `https://arxiv.org/api/errors`; an unknown well-formed id answers 200 with `totalResults` 0.
- `id_list` results do not come back in request order, so `batch_get()` maps them by versioned and base id.
- `max_results=3000` was accepted, but the documentation caps one slice at 2000 and one query at 30,000 results; the client keeps the documented caps.
- `max_results=0` answers one entry, not a bare total, so `count()` asks for one result.
- Titles carry line breaks and indentation; the parser collapses them.

## Testing

- Offline tests use real Atom fixtures in `tests/fixtures` and pytest-httpx.
- Live tests (`pytest -m live_api`) take about half a minute because of the three-second pace.
- Test settings pass `_env_file=None`; the client has no credential fields.
