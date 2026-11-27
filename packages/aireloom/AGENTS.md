# AIREloom

Python client (async source + generated sync twin) for the OpenAIRE Graph API
(V4) and the Scholexplorer API, built on the shared bibliofabric core (auth,
retries, rate limiting, pagination). AIREloom supplies the OpenAIRE query
dialect, typed filter models, response unwrapping, and pydantic models.

## Layout

```
src/aireloom/
  __init__.py           # Public exports (async + sync clients, resources, filters, models)
  _async/               # Single source of truth for I/O modules
    client.py           # AireloomClient(BaseApiClient): auth resolution, two hosts,
                        # resources as cached properties, mailto on V4 requests
    resources.py        # GraphResource, entity resources, LinksResource, ScholixResource
  _sync/                # Generated sync twins (scripts/unasync.py; never edit by hand)
    client.py           # AireloomSyncClient(SyncBaseApiClient)
    resources.py        # SyncGraphResource, Sync*Resource
  config.py             # AireloomSettings(BaseApiSettings), env prefix AIRELOOM_
  dialect.py            # GRAPH_DIALECT (max_page_size=100, offset cap 10_000, OR cap 50),
                        # LINKS_DIALECT and SCHOLIX_DIALECT (0-indexed, cap 99)
  filters.py            # V4 filter models -> one filter= expression; encode_filter_value
  unwrapper.py          # OpenAireUnwrapper (header/results/nextCursor), ScholixUnwrapper
  relations.py          # Static relation vocabulary & inverse lookup (RelationName, etc.)
  _helpers.py           # PID / ORCID extraction helpers for model computed fields
  models/               # Pydantic models aligned with Graph API 1.6.0 + Scholix V2/V3
```

Both hosts share credentials: `openaire_client_id` + `openaire_client_secret`
resolve to `ClientCredentialsAuth` against the Keycloak token endpoint,
otherwise `NoAuth`. An explicit `auth=` strategy wins. The Scholix host runs
on a second internal client throttled to 1 request per second.

Iteration over graph entities defaults to 100 per page
(`GRAPH_DIALECT.iterate_page_size`) and stops when the API stops returning
`nextCursor` or echoes the request cursor; the core handles both.

## Commands

Tooling is shared at the workspace root (see the root `AGENTS.md`). After
editing anything under `src/aireloom/_async/` or `tests/_async/`, regenerate
the sync twins:

```bash
uv run python scripts/unasync.py --package aireloom
uv run pytest packages/aireloom/tests
uv run pytest -m live_api packages/aireloom/tests   # needs .env credentials for higher quota
uv run ruff check packages/aireloom
uv run ty check packages/aireloom/src
```

Conventional commits, `uv` only, no AI attribution.

## Upstream behavior to remember

See `docs/aireloom/quirks.md` for the full list. The ones that bite during
development: V4 `page_size` is capped at 100 (offset paging capped at
`page * page_size <= 10_000`, OR lists capped at 50 values per field), Scholix
V3 silently ignores `linkProvider` (routed to V2) and returns zero rows for
`from`/`to` date filters while V2 has no date parameters at all (ignores them),
the links and Scholix routes silently truncate page sizes ≥ 100 to 10 results,
pages there are not pinned, and V3 by-id paths 404 when the `::` in identifiers
is percent-encoded.
