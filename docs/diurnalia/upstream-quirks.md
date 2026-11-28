# Upstream quirks

Findings from about 65 requests against the live DOAJ API on 2026-11-27, with the [API documentation](https://doaj.org/api/docs) and its [Swagger page](https://doaj.org/api/v4/docs) as the reference. Where a quirk affects diurnalia, the behavior of the client is noted.

## One search envelope, two route prefixes

`/api/search/journals/{query}` (legacy) and `/api/v4/search/journals/{query}` answer the same envelope: `total`, `page`, `pageSize`, `timestamp`, `query`, `results`, and `last` (plus `next` and `prev` from page 2 on). diurnalia wraps v4 only.

## Paging is capped at 1000 records

The API answers `(page - 1) * pageSize + pageSize <= 1000` and rejects anything beyond with HTTP 400: "You cannot access results beyond 1000 records via this API" (it points to the public data dump). Verified: page 20 at `pageSize=50` answers, page 21 answers 400, page 500 at `pageSize=2` answers, page 501 answers 400, page 1000 at `pageSize=1` answers. The cap is independent of the matched total; the match-all journal query reports 23831 records and the article query 14038837. diurnalia sets `max_offset` to 999 and raises `ConfigurationError` before sending a request beyond the cap.

`pageSize` is clamped silently: 51 and 100 both answer with `pageSize: 50`. The default is 10. `page=0` is treated as page 1.

## The query lives in the path

The search query is a path segment. A missing query is not allowed as an empty segment; `*` (URL-encoded `%2A`) works as match-all on both resources. `bibliofabric` carries queries as query parameters by default, so diurnalia overrides `search_path()`.

## Query syntax

- Fielded queries work with the short names `title`, `issn`, `publisher`, `license` (journals) and `title`, `doi`, `issn`, `publisher`, `abstract` (articles), and with full dot notation such as `bibjson.title`. `license:"CC BY"` matches 12395 journals on 2026-11-27; `license:cc-by` matches none, so the license value needs its stored spelling.
- `AND`, `OR`, `ANDNOT`, quoted phrases, and ranges (`created_date:[2015-01-01 TO 2016-01-01]`, 889 journals) work.
- Wildcards answer 400 with "Query contains disallowed Lucene features". The documentation also disables regex, fuzzy (`~`), and proximity searches.
- `issn:1932-6203` finds PLoS ONE, which carries it as an eISSN, so the field covers both ISSN kinds.
- A syntactically strange query such as `title:::x` does not error; it answers 200 with 27 results.
- `sort` takes `field` or `field:direction` and is echoed in the envelope. An unknown sort field answers 400. Sorting articles by `bibjson.year` answers 400 (verified 2026-11-27); `title:asc` on journals sorts case-insensitively.

## Identifier lookups go through search

There is no journal listing or article listing route, and no ISSN or DOI route. `GET /api/v4/search/articles/doi:10.3389/fpubh.2020.00115` answers the article, and a made-up DOI answers 200 with `total: 0`, not 404. diurnalia raises `NotFoundError` on an empty envelope.

The record routes `GET /api/v4/journals/{id}` and `GET /api/v4/articles/{id}` take the DOAJ record id and answer 200 without a key (verified 2026-11-27). They hold more than a search result. A journal search result carries `admin.ticked` and `es_type: null`, and an article search result carries `admin: null`. A record from the record route carries `es_type` (`journal` or `article`) and `admin` with `in_doaj`, and an article record also carries `publisher_record_id`. An id without a record answers 404 with `{"status": "not_found"}`. `get_by_id()` wraps both routes.

## Rate limit

The documentation states a rate limit of two requests per second on all API routes, with bursts of up to five queued requests. diurnalia defaults to 1 request per second and concurrency 2.

## Write routes and admin key

`POST /api/applications`, `GET/PUT/DELETE /api/applications/{id}`, `POST /api/articles`, `GET/PUT/DELETE /api/articles/{id}`, and the bulk upload routes (`/api/bulk/articles`, `/api/bulk/applications`) need an API key that only publishers have. The applications search route answers 401 without a key ("An API Key is required to access this"). diurnalia wraps none of these.

## Records

- Search results and id-route records carry `id`, `bibjson`, `admin`, `created_date`, `last_updated`; search results also carry `es_type: null`.
- Journal ISSNs are top-level `bibjson.pissn`/`bibjson.eissn`; article ISSNs live in `bibjson.identifier` (type `doi`, `eissn`, `pissn`) and in `bibjson.journal.issns`.
- The journal `bibjson.publisher` is an object (`name`, `country`); the article `bibjson.journal.publisher` is a plain string.
- The v4.0.1 release notes state that the article API normalizes identifier types to lower case and ignores unmanaged types.
