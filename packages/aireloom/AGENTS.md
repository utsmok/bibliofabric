# AIREloom

Async Python client for the OpenAIRE Graph API (V4) and the Scholexplorer
API, built on the shared bibliofabric core (auth, retries, rate limiting,
pagination). AIREloom supplies the OpenAIRE query dialect, typed filter
models, response unwrapping, and pydantic models.

## Layout

```
src/aireloom/
  client.py             # AireloomClient(BaseApiClient): auth resolution, two hosts,
                        # resources as cached properties, mailto on V4 requests
  config.py             # AireloomSettings(BaseApiSettings), env prefix AIRELOOM_
  dialect.py            # GRAPH_DIALECT (cursor, page_size, iterate 100/page),
                        # LINKS_DIALECT and SCHOLIX_DIALECT (0-indexed, cap 99)
  filters.py            # V4 filter models -> one filter= expression; encode_filter_value
  unwrapper.py          # OpenAireUnwrapper (header/results/nextCursor), ScholixUnwrapper
  models/               # pydantic models aligned with Graph API 1.6.0 + Scholix V2/V3
  resources/
    base.py             # GraphResource: filter expression, sort validation, V3 by-id
                        # item_path (colons unencoded), facets/group_by, batch OR chunks
    research_products.py # batch_get_by_doi, links helpers
    links.py            # /v3/research-products/links, relations-info
    scholix.py          # ScholixResource facade: V3 default, V2 for date filters
```

Both hosts share credentials: `openaire_client_id` + `openaire_client_secret`
resolve to `ClientCredentialsAuth` against the Keycloak token endpoint,
otherwise `NoAuth`. An explicit `auth=` strategy wins. The Scholix host runs
on a second internal client throttled to 1 request per second.

Iteration over graph entities defaults to 100 per page
(`GRAPH_DIALECT.iterate_page_size`) and stops when the API stops returning
`nextCursor` or echoes the request cursor; the core handles both.

## Commands

Tooling is shared at the workspace root (see the root `AGENTS.md`). The
package-specific bit: live smoke tests need OpenAIRE credentials from a
`.env` file, and the suite is `packages/aireloom/tests`.

Conventional commits, `uv` only, no AI attribution.

## Upstream behavior to remember

See `docs/quirks.md` (workspace path `docs/aireloom/quirks.md`) for the full
list. The ones that bite during
development: Scholix V3 accepts date filters but returns zero rows (route
those queries to V2), the links route silently truncates `pageSize >= 100`
to 10 results, pages there are not pinned, and V3 by-id paths 404 when the
`::` in identifiers is percent-encoded.
