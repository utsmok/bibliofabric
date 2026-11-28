# prodromus: Project Guide

prodromus is an async + generated-sync Python client for the bioRxiv and medRxiv API (`https://api.biorxiv.org`), built on bibliofabric 0.8. Not yet published. It is a Wave 2 library.

## Architecture

| Path | Contents |
|---|---|
| `_async/client.py` | `ProdromusClient(BaseApiClient)`: the four resources |
| `_async/routes.py` | `DetailsClient`, `PublishedClient`, `FundersClient`, `StatisticsClient` on a private `_RoutesClient` with request, page, and iterate helpers |
| `unwrapper.py` | `ProdromusUnwrapper` (`collection` or the `... content statistics` key, `messages[0]` totals and cursor) and `check_status()` |
| `models.py` | `Preprint`, `FunderDeclaration`, `PublishedArticle`, `ContentStatistic`, `UsageStatistic` (`extra="allow"`) |
| `dialect.py` | Base URL, servers, page sizes, `date_range()`, `server_segment()` |
| `config.py` | `ProdromusSettings` (`PRODROMUS_` prefix), 1 request per second, concurrency 1 |

The routes page by an offset in the path, not by a query parameter, so the clients do not subclass `ResourceClient`.

## Upstream facts (verified 2026-11-28)

- The API answers HTTP 200 for errors and puts the reason in `messages[0].status`, for example `Both dates must be in yyyy-mm-dd format` or `funder value not found`. Empty answers say `no posts found` or `no articles found for ...`. `check_status()` raises `ConfigurationError` for the first kind and passes the second.
- The "N most recent" (`/details/biorxiv/45`) and "last N days" (`/details/biorxiv/2d`) forms take no cursor: with one the API answers the date-format error. `recent()` sends them without a cursor; `/details/biorxiv/45` answered 30 records, `/2d` answered 270 at once.
- The funder route accepts date ranges only (from 2025-04-10 on); `30d` answers the date-format error.
- `messages[0].total` and `count_new_papers` are strings on some routes and numbers on others. `cursor` is a number on the first page and a string on later pages; the unwrapper reads both (a full walk of 724 bioRxiv posts on 2026-11-02 and 03 validated).
- `authors` is one string with `;` between names; `published` is a DOI or `NA`; `version` is a string.
- The statistics routes put their records under `bioRxiv content statistics` or `medRxiv content statistics`, and `messages` is an object there, not a list.

## Testing

- Offline tests use trimmed real answers in `tests/fixtures` and pytest-httpx.
- Live tests run with `pytest -m live_api`.
