# AIREloom: Python client for the OpenAIRE API

<p align="center"><img src="https://github.com/user-attachments/assets/54a7de2e-9469-4d81-ba33-788a5a0aa753" alt="AIREloom logo" height="393" width="500" /></p>

*Samuel Mok · s.mok@utwente.nl · 2025–2026*

AIREloom is a Python client for the [OpenAIRE Graph API](https://graph.openaire.eu/) and [Scholexplorer API](https://scholexplorer.openaire.eu/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It ships an async client and a generated sync twin (`AireloomSyncClient`) with the same API surface.

**Docs:** [utsmok.github.io/bibliofabric/aireloom](https://utsmok.github.io/bibliofabric/aireloom/) · **PyPI:** [aireloom](https://pypi.org/project/aireloom/) · **License:** MIT

## Features

- **Graph API V4 for list operations** — the recommended filter-based queries (`filter=field:value`, `sort=field:dir`, `select`, `facets`, `group_by`, `page_size` up to 100 and cursor paging with no depth cap); single-entity lookups use the stable V3 by-id routes
- **Async first, sync everywhere** — async built on `httpx` + `asyncio` with retries, a client-side rate limiter (2 req/s, concurrency 4), and typed errors; the generated sync twin runs on `httpx.Client`, `time.sleep`, and threads, and works in scripts, notebooks, and inside a running event loop
- **Typed throughout** — Pydantic models for all inputs and outputs, PEP 561 `py.typed`; `search()` returns `bibliofabric.Page[E]`
- **Scholix V3 (V2 for `linkProvider`)** — typed link records through a dedicated internal client for the Scholexplorer host
- **Anonymous or OAuth2** — client credentials or refresh token against the Keycloak endpoint, or no auth at all

## Installation

```bash
uv add aireloom
```

Requires Python ≥3.12.

## Quick Start

```python
import asyncio
from aireloom import AireloomClient, ResearchProductsFilters


async def main():
    async with AireloomClient() as client:
        # Search publications (V4 filter-based query)
        filters = ResearchProductsFilters(
            type="publication",
            title_search="climate change",
            from_publication_year=2024,
        )
        page = await client.research_products.search(
            filters,
            sort="publication_date:desc",
            page_size=5,
        )
        for product in page.results:
            print(f"{product.mainTitle} — DOI: {product.doi or 'N/A'}")

        # Iterate all results (cursor-based, resumable)
        async for product in client.research_products.iterate(
            ResearchProductsFilters(type="dataset", authorships_countries=["NL"]),
            page_size=100,
        ):
            print(product.mainTitle)
            break  # stop whenever you want

        # Get a single entity by OpenAIRE id (V3 by-id route)
        product = await client.research_products.get(
            "dedup_wf_002::016e036dfe4204781ee9bf94c8b06c1b"
        )

        # Batch-fetch by DOI (one OR filter per chunk of 50)
        products = await client.research_products.batch_get_by_doi(
            ["10.5281/zenodo.15069438", "10.1038/s41586-023-06221-2"]
        )

        # Aggregations
        counts = await client.research_products.group_by("type")
        print(counts)  # {'publication': 241566601, ...}


asyncio.run(main())
```

### Sync

The same operations without `asyncio`, for scripts, notebooks, and code that
already runs inside an event loop:

```python
from aireloom import AireloomSyncClient

with AireloomSyncClient() as client:
    page = client.research_products.search(
        query="quantum dots",
        page_size=5,
    )
    for product in page.results:
        print(product.mainTitle)

    for product in client.research_products.iterate(page_size=100):
        print(product.mainTitle)
        break

    products = client.research_products.batch_get_by_doi(
        ["10.5281/zenodo.15069438", "10.1038/s41586-023-06221-2"]
    )
```

Both variants take the same parameters, raise the same errors, retry and page
the same way, and enforce the same rate limits. Resource attributes expose the
matching `Sync*` resource classes (`SyncResearchProductsResource`, ...).

No authentication required — the Graph API works without it. For higher rate limits, set credentials (see [Authentication](#authentication)).

## Core API

### Retrieval methods

Every entity resource (`client.research_products`, `client.projects`,
`client.organizations`, `client.data_sources`, `client.persons`) provides:

| Method | Description |
|--------|-------------|
| `get(id)` | Retrieve a single entity by OpenAIRE id (V3 by-id route) |
| `search(filters, query, sort, select, page, page_size, cursor)` | One page as `Page[E]` |
| `iterate(filters, page_size=100, limit, cursor, on_page)` | Auto-paginate all results (cursor-based, resumable) |
| `collect(limit, ...)` | Collect results into a list |
| `count(filters)` | Count matching entities cheaply |
| `first(filters)` | Get first matching entity or `None` |
| `facets(*fields, filters)` | Facet counts per field: `{field: {value: count}}` |
| `group_by(field, filters)` | Counts per value without fetching records |
| `batch_get(ids, field, batch_size)` | Fetch many ids via OR filters |

`client.research_products` additionally has `batch_get_by_doi(dois)`,
`by_orcid(orcid, limit=100)`, `get_fields(ids, fields)`, `search_links()`,
`iterate_links()`, and `get_relations_info()`.
`client.persons` has `batch_get_by_orcid(orcids)`, and `client.organizations`
has `find_variants(names)`.

### Filters and sorting

Filters are typed Pydantic models in `aireloom.filters`, one per entity. Field
names follow the V4 filter syntax; dotted API fields use underscores with
aliases (`ids_doi` sends `ids.doi`). Lists become pipe-separated ORs, booleans
become `true`/`false`, and string values pass through operators such as
`">100"` or `"!other"`:

```python
from aireloom.filters import ResearchProductsFilters

filters = ResearchProductsFilters(
    type="publication",
    title_search="machine learning",
    from_publication_year=2024,
    authorships_countries=["NL", "BE"],
    impact_citation_count=">100",
)
```

Sort with `sort="citation_count:desc"` (`asc`/`desc`, comma-separate several
fields). Valid fields are validated client-side per entity and raise
`ConfigurationError`.

Full-text search is a separate parameter: `search(filters, query="...")`.

## Authentication

AIREloom reads `AIRELOOM_`-prefixed environment variables or a `.env` file.
Without credentials the client is anonymous:

```dotenv
AIRELOOM_OPENAIRE_CLIENT_ID=your_id
AIRELOOM_OPENAIRE_CLIENT_SECRET=your_secret
```

Both set → OAuth2 client credentials against the OpenAIRE Keycloak endpoint
(`https://aai.openaire.eu/auth/realms/openaire/protocol/openid-connect/token`;
the legacy `oidc/token` endpoint is retired). Setting only one of the two raises
`ConfigurationError`. Alternatively, set `AIRELOOM_OPENAIRE_REFRESH_TOKEN` (or
pass `refresh_token=`) to use `RefreshTokenAuth`. You can also pass any
`bibliofabric` auth strategy explicitly with `auth_strategy=` (`auth=` is a
deprecated alias):

```python
from bibliofabric.auth import NoAuth, StaticTokenAuth

client = AireloomClient(auth_strategy=StaticTokenAuth(token="..."))
```

## Scholix

`client.scholix` searches the Scholexplorer host (own rate limit: 1 req/s):

```python
from aireloom.filters import ScholixFilters

page = await client.scholix.search_links(
    ScholixFilters(sourcePid="10.1038/s41586-023-06221-2")
)
async for link in client.scholix.iterate_links(
    ScholixFilters(sourcePid="10.1038/s41586-023-06221-2")
):
    rel = link.relationship_type.name if link.relationship_type else ""
    title = link.target.title if link.target else ""
    print(rel, title)
```

V3 serves default queries. Queries with `linkProvider` are routed to V2
automatically because V3 silently ignores `linkProvider`. Passing `from_date`
or `to_date` to Scholix search/iterate methods raises `ConfigurationError`
immediately: V3 returns zero rows for date filters, and V2 ignores date
parameters (upstream limitation; see `docs/aireloom/quirks.md`).
`search_links_v2` / `iterate_links_v2` target V2 directly, and
`list_link_providers` / `list_link_publishers` cover the V2 directory endpoints.
The V1 endpoints were removed.

## Error Handling

```python
from aireloom import (
    BibliofabricError,
    APIError,
    AuthError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
```

`request()` raises on every status ≥ 400 (404 → `NotFoundError`, 429 →
`RateLimitError`), and validation failures raise `ValidationError` carrying
the raw payload.

## Known OpenAIRE API Issues

- **V4 `page_size` max is 100** (even with cursor paging), offset paging is
  capped at `offset <= 10,000` (`max_offset=10_000`), and each filter field
  accepts at most 50 pipe-separated OR values.
- **Links and Scholix page sizes ≥ 100** silently return 10 results; AIREloom
  caps both at 99.
- **V4 `group_by` eligibility** is decided server-side per field: some fields
  return 400 ("not eligible"), others (e.g. projects `funder_short_name`)
  silently return empty counts.
- **Page-based routes (`links`, Scholix) have no cursor or sort**, so page
  windows can shift between requests during long iterations.
- **Scholix date filters & `linkProvider`**: `/v3/Links` returns zero rows for
  `from`/`to` and silently ignores `linkProvider`, while `/v2/Links` honors
  `linkProvider` but has no `from`/`to` support (ignores date parameters).

## Development

AIREloom lives in the bibliofabric uv workspace at `packages/aireloom`. From the repository root:

```bash
uv sync --all-packages --all-groups   # install dev deps
uv run pytest packages/aireloom/tests -x -q  # run tests
uv run ruff check                     # lint (workspace-wide)
uv run ty check packages/*/src        # type check
```
