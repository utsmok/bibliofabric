# Stavrophora: Asynchronous Python client for the Crossref API

Samuel Mok -- s.mok@utwente.nl -- 2026

Stavrophora is an async Python client for the [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), built on [bibliofabric](https://github.com/utsmok/bibliofabric).

**License:** MIT

## Features

- **Async by design** -- built on `httpx` + `asyncio` with proper connection pooling
- **Typed end-to-end** -- Pydantic v2 models with `extra="allow"` (the Crossref spec is incomplete; extra fields are preserved, never dropped)
- **Cursor pagination** -- `async for work in client.works.iterate(...)` over `next-cursor`
- **Polite pool by default** -- one `mailto=` line triples your rate limit
- **Batch DOI lookup** -- comma-separated repeated `filter=doi:` keys (Crossref's supported OR form)
- **Scoped works** -- `client.journals.works(issn)`, `client.funders.works(id)`, `client.members.works(id)`, `client.prefixes.works(prefix)`, `client.types.works(type)`
- **Facets and sampling** -- `client.works.facets(...)` returns `{facet: {value: count}}`; `client.works.sample(n)` draws up to 100 random works
- **Route-aware parameters** -- works-only parameters (`sort`, `select`, filters) are rejected client-side on routes that would answer 400

## Installation

```bash
uv add stavrophora
```

Or with pip: `pip install stavrophora`. Requires Python >=3.12.

## Quick Start

```python
import asyncio
from stavrophora import StavrophoraClient, WorksFilters


async def main():
    async with StavrophoraClient(mailto="you@example.org") as client:
        # Get a single work by DOI (bare or doi.org-prefixed, mixed case)
        work = await client.works.get("10.1038/nature12373")
        print(work.title[0], work.issued.date_parts)

        # Search: filters, sort/order split, field selection
        page = await client.works.search(
            WorksFilters(type="journal-article"),
            query="crow nesting",
            sort="is-referenced-by-count:desc",
            select=["DOI", "title", "is-referenced-by-count"],
            page_size=5,
        )
        for item in page.results:
            print(item.doi, item.is_referenced_by_count)

        # Facet distributions
        facets = await client.works.facets(
            WorksFilters(type="journal-article"), facets=("published",)
        )


asyncio.run(main())
```

`search()` returns a `bibliofabric.Page`: `.results` (typed models), `.total`, `.next_cursor`, and `.meta` (the raw envelope minus results, e.g. facets). 

No authentication required. Pass a `mailto` (parameter or `STAVROPHORA_MAILTO` env var) to enter the polite pool: 3 requests/s for works lists, 10/s for single records and scoped works routes, 3 concurrent (since the 2026-07 split; the client paces everything at 3/s to stay under the works-list ceiling). A Metadata Plus key (`STAVROPHORA_PLUS_TOKEN` or `plus_token=`) is sent as `crossref-api-key: Bearer <key>` and replaces the query-parameter mailto as the auth strategy; the mailto still rides the User-Agent.

## Basic Usage

### Get a single entity

```python
work = await client.works.get("10.1038/nature12373")  # DOI (bare or doi.org-prefixed)
journal = await client.journals.get("0028-0836")  # ISSN or eISSN
funder = await client.funders.get("10.13039/501100000923")
member = await client.members.get("78")  # e.g. Elsevier
prefix = await client.prefixes.get("10.1016")  # no /prefixes list route exists
```

### Search, sort, filter, select

```python
from stavrophora import WorksFilters

response = await client.works.search(
    filters=WorksFilters(type="journal-article", from_pub_date="2026-01-01"),
    sort="is-referenced-by-count:desc",
    select=["DOI", "title", "is-referenced-by-count"],
    page_size=20,
)
```

Crossref has **no publisher filter** (400, verified live); scope by `prefix`, `member` or `ror-id` instead.

### Iterate all results (cursor)

```python
async for work in client.works.iterate(
    filters={"from-created-date": "2026-08-01"}, page_size=1000, on_page=checkpoint,
):
    process(work)
```

Iteration defaults to 1000 rows per page and follows `next-cursor` until an empty page. Since 2026-08-24 cursor result sets are not stable and cursors must be re-read from every page (the client always repeats all parameters). Combining iteration with the `issued` / `published*` sorts raises a client-side error: the API rejects that combination with 400. For incremental sync prefer `from-created-date` / `until-created-date` windows over `from-index-date` (index-date windows drift); pass `on_page(page_number, next_cursor)` to checkpoint and resume with `cursor=`.

### Scoped works

```python
nature_works = client.journals.works("0028-0836")
response = await nature_works.search(page_size=5)

ut_works = client.prefixes.works("10.3990")  # UT student theses
async for w in ut_works.iterate():
    ...
```

### Batch DOI lookup

```python
found = await client.works.batch_get_by_doi(
    ["10.1038/nature12373", "10.1103/PhysRevLett.116.061102"]
)
```

Keys are normalized bare lowercase DOIs; misses are absent from the dict. Requests are batched 50 DOIs per call via repeated `filter=doi:` keys (the pipe form `doi:a|b` returns **zero** results -- verified live).

### Registration agency

```python
agency = await client.works.agency("10.1038/nature12373")
print(agency.agency.label)  # "Crossref"
```

## Configuration

Settings load from env vars prefixed `STAVROPHORA_` (or `.env` / `secrets.env`):

```dotenv
STAVROPHORA_MAILTO=s.mok@utwente.nl
```

Generic settings are inherited under the same prefix: `STAVROPHORA_TIMEOUT`, `STAVROPHORA_MAX_RETRIES`, `STAVROPHORA_MAX_REQUESTS_PER_SECOND` (default 3), `STAVROPHORA_MAX_CONCURRENCY` (default 3), `STAVROPHORA_USER_AGENT`. `STAVROPHORA_PLUS_TOKEN` holds a Metadata Plus key (sent as `crossref-api-key: Bearer <key>`).

## Known Crossref API Quirks

- **No pipe-OR in filters.** `filter=doi:a|b` silently returns 0 results (OpenAlex-style). Repeated `key:value` pairs (`filter=doi:a,doi:b`) are the supported OR form.
- **Unknown query parameters are rejected with 400** (no silent ignoring). The client therefore sends only `rows`, `offset`, `query`, `filter`, `sort`, `order`, `select`, `cursor`, `mailto`.
- **`page` is not a parameter** -- paging is `offset` with `offset + rows <= 10000` (the client raises before requesting past the cap; use `iterate()`) + `rows` (max 1000, 400 otherwise). Deep paging must use `cursor`.
- **Cursor requests reject publication-date sorts** (400 `sort-criteria-incompatible-with-cursor`, since 2026-08-24): `iterate(sort="published")` raises client-side; sort by `is-referenced-by-count` or iterate unsorted.
- **`sample` (max 100) cannot combine with `rows`/`offset`**; `client.works.sample(n)` handles that for you.
- **Cursor exhaustion is implicit**: the last non-empty page still returns a `next-cursor`; only the following request returns an empty `items` and no cursor.
- **`/prefixes` has no list route** (404) -- only `/prefixes/{prefix}` and `/prefixes/{prefix}/works`. **`/licenses` has no single-item route** (404) -- only the list.
- **The `message` envelope is one level deep** for everything: single items live in `message`, lists in `message.items` with totals in `message.total-results`.
- **Rate limits changed 2025-12-01, split by request type 2026-07-21**: polite pool 3 req/s for top-level `/works` lists (`x-api-pool: polite-array`), 10 req/s for single records and scoped works routes (`polite-single`), 3 concurrent; limits apply per `mailto` address. Metadata Plus: 150/s via the `crossref-api-key` header. On 429 back off (the client retries with `Retry-After`/exponential backoff); 403 means blocked.
- **API is served at both `https://api.crossref.org` and `.../v1`** with identical payloads (verified 2026-09); stavrophora pins `/v1`, the versioned form.
- **The Crossref spec is incomplete** -- several returned fields are missing from the official schema. All models use `extra="allow"`, same defense as aletheca.
- **Schemas differ between list and single-item routes** (verified live): `/journals/{issn}` returns `title` as a bare string while `/journals` returns a list; member `prefix` entries are `{name, value}` objects. The models normalize both shapes (`SafeStrList`, dict-typed prefix entries).
- **`/types` ignores `rows`/`offset`** (verified live 2026-09): the route always returns the complete list (~30 types) regardless of paging parameters.
- **`/prefixes/{prefix}` returns `member` and `prefix` as full `https://id.crossref.org/member/297`-style URIs** (verified live 2026-09). The `Prefix` model normalizes both the URI and bare forms to bare values (`"297"`, `"10.1038"`).

## Development

```bash
uv sync
uv run pytest                    # mocked tests (live tests excluded by default)
uv run pytest -m live_api        # live API smoke tests
uv run ruff check .
uvx ty check src/
```

## License

MIT
