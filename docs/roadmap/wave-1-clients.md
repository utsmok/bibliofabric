# Wave 1 Client Specs & Core Enablers

This guide provides the starter specifications that the **11 Wave 1 client
libraries** were built from, the **6 targeted `bibliofabric` core additions**,
and the **2 extensions to existing clients** that were planned with them.

For the step-by-step recipe to scaffold, type-check, generate sync twins, and
test any client package in this workspace, see
[Building a client on `bibliofabric`](../bibliofabric/writing-a-client.md).

Status on 2026-11-28: all eleven libraries are built under their final names
(see [Wave 1 libraries](wave-1-libraries.md)). These specs were the starting
point. Where the live API differs from a spec, the client follows the live
API, and the upstream-quirks page of the package records the difference.
Corrections carry the date on which they were verified.

## `bibliofabric` Core Enablers

`bibliofabric` 0.8 already provides `retry=bool`, `_fetch_batch_chunk()`,
`page_size_param: str | None`, `max_offset`, per-instance `dialect=`,
`BasicAuth`, `ClientCredentialsAuth(token_auth_method="post")`,
`RefreshTokenAuth`, automatic 401 token refresh, `on_response()`, `stream()`,
`follow_redirects`, `connect_timeout`, and cached `TypeAdapter(list[E])`
validation.

Six lightweight, backwards-compatible core additions unlock Wave 2 without
per-client workarounds. Two of them are in `bibliofabric` 0.8: the
`default_headers` property of `BaseApiClient` (addition 1) and
`JsonApiUnwrapper` (the JSON:API part of addition 2), together with five of
the identifier normalizers (ISBN, ISNI, Wikidata, GND, and VIAF from
addition 6). The [deferred list](deferred.md#core-framework) has the rest with
the reason for each:

1. **Default per-client `Accept` / static headers:** Add an optional
   `default_headers: Mapping[str, str] | None` parameter (or `Accept` default on
   `BaseApiSettings`/`BaseApiClient`) merged into owned and caller-supplied
   requests unless overridden per call.
   - *Unlocks:* ORCID (`Accept: application/vnd.orcid+json`), UKRI GtR
     (`Accept: application/vnd.rcuk.gtr.json-v7`), GLEIF
     (`Accept: application/vnd.api+json`), DOI Content Negotiation
     (`Accept: application/vnd.citationstyles.csl+json`).
2. **Header-aware `ResponseUnwrapper` & RFC 5988 `Link` parser:** Allow
   `ResponseUnwrapper.next_cursor()` (or an optional companion method) to read
   `httpx.Headers`, and ship a small `parse_link_header()` helper plus a
   reusable JSON:API unwrapper mixin (`data[].attributes` + `links.next`).
   - *Unlocks:* Software Heritage (`Link: <...>; rel="next"`), DataCite REST,
     OSF v2, Zenodo `links.next`, GLEIF LEI, and ARC NCGP.
3. **POST-body search & pagination dialect:** Allow `ResourceClient` subclasses
   to declare `search_method = "POST"` with a `build_search_body()` hook that
   places filters, page size, and offset/cursor in the JSON request body instead
   of query parameters (with `retry=True` for read-only search POSTs).
   - *Unlocks:* NIH RePORTER v2, Figshare `/articles/search`, ETER v4, CORE v3
     POST search, Lens.org, and SPARQL endpoints.
4. **Fixed / sliding-window rate limiter & daily quota hooks:** Extend
   `Limiter` alongside `req/s` spacing to enforce explicit `(max_requests,
   window_seconds)` caps and optional daily budget/quota callbacks.
   - *Unlocks:* LoC (`20 req/min` to prevent 1h–72h IP bans), GLEIF
     (`60 req/min`), ROR (`2,000 / 5 min`), DataCite (`500–3,000 / 5 min`),
     ORCID (`25k–100k / day`), NASA ADS (`5,000 / day`).
5. **Pluggable non-JSON decoder hook:** Generalize `BaseApiClient.parse_json()`
   with a pluggable decoder hook (`parse_response(response)` defaulting to JSON)
   for XML, Atom 1.0, OAI-PMH, SRU, ANVL, and BibTeX/plain text.
   - *Unlocks:* arXiv Atom XML, PubMed `efetch`, re3data, VIAF/LoC SRU,
     DOI BibTeX ConNeg, ARK/N2T, and generic OAI-PMH harvesting.
6. **Expanded `bibliofabric.ids` normalizers:** Add canonical normalizers and
   check-digit validators alongside existing `normalize_doi`, `normalize_orcid`,
   `normalize_ror`, and `normalize_issn`:
   - `normalize_isbn` (ISBN-10 ↔ ISBN-13 + check digits)
   - `normalize_isni`, `normalize_lei`, `normalize_wikidata_qid`
   - `normalize_gnd`, `normalize_viaf`, `normalize_ark`
   - `normalize_raid`, `normalize_swhid`, `normalize_spdx`

## Immediate Extensions to Existing Clients

Before starting new packages, two high-value additions belong in existing
packages:

- **`stavrophora` (Crossref):**
  - Add a resource client for the **Crossref Data Citation API**
    (`/beta/datacitations/` → GA late 2026), replacing the sunset Event Data
    API.
  - Add typed helpers for **Retraction Watch** records embedded in Crossref
    `/works` (`updated-by` / `update-type:retraction` with
    `source: retraction-watch`).
- **`aletheca` (OpenAlex):**
  - Document and optionally surface OpenAlex credit/budget headers
    (`X-RateLimit-Credits-Used`, `cost_usd`) via `BaseApiClient.on_response()`
    alongside existing `daily_budget` 429 retry vetoing.

## Wave 1 Candidate Client Starter Specs

### 1. ROR v2 (Organizations & Funders)

- **Base URL:** `https://api.ror.org/v2` (primary path: `organizations`)
- **Auth:** `NoAuth()` by default; optional `HeaderAuth("Client-Id", ...)` for
  the registered 2,000 req / 5 min tier.
- **`QueryDialect`:**
  `page_param="page"`, `page_start=1`, `page_size_param=None` (fixed 20/page),
  `max_page_size=20`, `default_page_size=20`, `max_offset=9980`,
  `query_param="query"`, `sort_param=None`, `select_param=None`.
- **`ResponseUnwrapper`:** `results -> body["items"]`,
  `total -> body["number_of_results"]`, `item -> body`, `next_cursor -> None`,
  `meta -> body["meta"]`.
- **Batching & Rate Limits:** No native multi-ID batch endpoint; use bounded
  concurrent `get()` or the Zenodo dump. Verified 2026-11-27: ROR publishes
  no limit for anonymous callers and has paused registration, so the client
  sends no client identification.
- **License:** **CC0 1.0** (API and Zenodo data dumps).
- **Upstream Quirks:**
  - API/schema v1 was sunset in late 2025; target v2.1 fields (`names`,
    `locations`, `domains`, `external_ids` incl. `fundref`).
  - Expose a dedicated `match_affiliation(affiliation: str)` method using
    `?affiliation=...` (mid-2026 default `single_search`), trusting entries with
    `chosen: true`.
  - Provide an optional Zenodo JSON dump loader (~115k records) for offline
    `<1 ms` lookups and legacy Crossref Funder ID (`10.13039/...`) → ROR
    crosswalks.
  - Verified 2026-11-27: the dump holds about 152,000 records. A rejected
    request (unknown filter key, page above 500, malformed `query.advanced`)
    answers HTTP 200 with an `errors` body. `query` and `query.advanced`
    cannot be combined. The keyword search does not find an ISNI, so the
    external-id lookup goes through `external_ids.all` in `query.advanced`.

### 2. ORCID API v3.0 (Researchers)

- **Base URL:** `https://pub.orcid.org/v3.0` (Public) or
  `https://api.orcid.org/v3.0` (Member)
- **Auth:** `NoAuth()` for anonymous public reads, or
  `ClientCredentialsAuth(client_id, client_secret, "https://orcid.org/oauth/token", scope="/read-public", token_auth_method="post")`
  for Public/Member clients.
- **`QueryDialect`:** Search (`/expanded-search` or `/search`):
  `offset_param="start"`, `page_size_param="rows"`, `max_page_size=200`,
  `default_page_size=25`, `max_offset=10_000`, `query_param="q"`,
  `page_param=None`, `sort_param=None`.
- **`ResponseUnwrapper`:** Search returns `body["expanded-result"]` (or
  `body["result"]`) and `total -> body["num-found"]`; single profile sub-routes
  (`/{orcid}/record`, `/works`, `/employments`, `/educations`,
  `/external-identifiers`) return `item -> body`.
- **Batching & Rate Limits:** No multi-ID batch GET. **12 req/s** public
  (**24 req/s** member), burst 40/s returns `503`; daily caps **25k/day** anon,
  **100k/day** Public Client, unlimited Member.
- **License:** ORCID Public API Terms (**non-commercial** restriction on Public
  API); annual public data file is **CC0**. Tag accordingly in fusion policies.
- **Upstream Quirks:**
  - **Requires `Accept: application/vnd.orcid+json`** (default is XML; relies on
    core Enabler #1 or explicit per-request headers until landed).
  - JSON preserves XML-derived `{"value": "..."}` wrapper dicts throughout;
    normalize cleanly inside Pydantic field validators.
  - Normalize IDs with `bibliofabric.ids.normalize_orcid`.
  - Verified 2026-11-27: `Accept: application/json` and `application/vnd.orcid+json`
    both answer JSON, and `application/ld+json` answers 406. The client sends
    `application/json` on every request.
  - Verified 2026-11-27: `/expanded-search/` answers
    `{"expanded-result": [...], "num-found": N}` and `/search/` answers
    `{"result": [...], "num-found": N}`. `rows=1000` answers HTTP 500, as does
    an unknown field name in `q`, so the client caps `rows` at 100.
  - Verified 2026-11-27: `/{orcid}/biography` and `/{orcid}/emails` answer 404
    with error code 9041 when the record has none, and an unused activities
    section answered 404 in one run and 200 with an empty group in another.
    Every section reader maps 404 to `None`.
  - Verified 2026-11-27: the member API token on hand was rejected with 403 on
    `api.orcid.org`, so the client is not built for the member API and does
    not mint tokens. It sends an optional `ORCHIS_ACCESS_TOKEN` as a bearer
    header. The member read routes have the same paths as the public ones.

### 3. DataCite REST API (Datasets, Software, Preprints & PID Graph)

- **Base URL:** `https://api.datacite.org` (paths: `dois`, `clients`,
  `providers`, `prefixes`, `events`; optional GraphQL at `/graphql`)
- **Auth:** `NoAuth()` for public read (send descriptive `User-Agent` / `mailto`
  for identified tier); `BasicAuth(repository_id, password)` for Member
  writes/drafts.
- **`QueryDialect`:**
  `page_size_param="page[size]"`, `max_page_size=1000`, `default_page_size=25`,
  `page_param="page[number]"`, `max_offset=10_000`,
  `cursor_param="page[cursor]"`, `cursor_start="1"`, `query_param="query"`,
  `sort_param="sort"`, `select_param=None`.
- **`ResponseUnwrapper`:** JSON:API envelope: `results -> body["data"]`,
  `item -> body["data"]`, `total -> body["meta"]["total"]`,
  `next_cursor ->` extract `page[cursor]` query param from
  `body.get("links", {}).get("next")`, `meta -> body.get("meta", {})`.
- **Batching & Rate Limits:** Verified 2026-11-27: filters take one parameter
  per criterion, and a comma list inside one filter means OR. Rate:
  **500 unid / 1,000 identified / 3,000 member per 5 min** per IP; the API
  sends no rate-limit headers. The client defaults to 1.5 requests per second.
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - Deep pagination past 10,000 records requires `page[cursor]=1` on the first
    request (not `*`) and following `links.next`.
  - Normalize DOIs with `normalize_doi`; preserve `relatedIdentifiers` and
    `version` fields for dataset/software lineage.
  - Verified 2026-11-27: `page[size]` accepts 1 to 1000 (1001 is cut to
    1000); numbered paging stops at 10,000 records with a 400; a cursor walk
    always orders by `created` ascending, whatever `sort` says; `sort`
    accepts `relevance`, `name`, `created`, `updated`, `published`,
    `view-count`, `download-count`, `citation-count`, and `title` (a `-`
    prefix reverses it); date filters take years; `fields[dois]` silently
    drops `resourceTypeGeneral`. `/dois/{id}/media`, `/views`, `/downloads`,
    and `/url` answer 404 without a login, and `/prefixes/totals` answers
    204.

### 4. Semantic Scholar (Graph, Bulk Search & Batch)

- **Base URL:** `https://api.semanticscholar.org/graph/v1` (plus optional
  `/recommendations/v1`, `/datasets/v1`)
- **Auth:** `HeaderAuth("x-api-key", api_key)` strongly recommended (anonymous
  pool suffers frequent `429` throttling).
- **`QueryDialect`:**
  - Standard search (`/paper/search`): `offset_param="offset"`,
    `page_size_param="limit"`, `max_page_size=100`, `default_page_size=25`,
    `max_offset=1_000`, `query_param="query"`, `select_param="fields"`,
    `page_param=None`, `sort_param=None`.
  - Bulk search (`/paper/search/bulk`, via per-instance `dialect=`):
    `cursor_param="token"`, `cursor_start=None`, `page_size_param=None` (fixed
    1,000/page), `query_param="query"`, `select_param="fields"`,
    `sort_param="sort"`.
- **`ResponseUnwrapper`:** `results -> body["data"]`, `item -> body`,
  `total -> body.get("total")`, `next_cursor -> body.get("token")`,
  `meta ->` remaining keys.
- **Batching & Rate Limits:** Override `_fetch_batch_chunk()` to call
  `POST /paper/batch` (up to **500 IDs** per chunk, `json={"ids": chunk}`,
  `params={"fields": ...}`, `retry=True`) and `POST /author/batch`. Intro API
  key: **1 req/s** (`max_requests_per_second=1.0`).
- **License:** **ODC-By 1.0** (datasets/corpus); AI2 API License (attribution
  required; SPECTER2 embeddings Apache 2.0).
- **Upstream Quirks:**
  - Accepts prefixed IDs (`DOI:...`, `ARXIV:...`, `PMID:...`, `CorpusId:...`, or
    bare 40-char S2 paper ID); preserve prefix during `normalize_id()` and
    match back in `record_keys()`.
  - `POST /paper/batch` returns `null` entries in the JSON array for missing
    IDs; filter `None` items inside `_fetch_batch_chunk()`.
  - Always specify `select=` (`fields=`) explicitly; default response is
    minimal (`paperId`, `title`).
  - Verified 2026-11-27: the API key on hand answers HTTP 403, so the client
    was built and tested without a key. Without a key, `/paper/search`,
    `/paper/search/match`, `/snippet/search`, the `URL:` and `PubMedCentral:`
    id forms, and the patent search routes answered 429 during the whole
    study. The client wraps them from the published specification, and the
    docs page lists them as unverified.
  - Verified 2026-11-27: `POST /paper/batch` and `POST /author/batch` take a
    bare JSON array of ids and answer a bare array with `null` in the place
    of an unknown id. `fields` is a query parameter on both. The client sends
    at most 500 ids per paper call and 1000 ids per author call.
  - Verified 2026-11-27: `fields=openAccessDoi` and `fields=embedding` answer
    400 without a key, and a dataset file listing answers 401 without a key.
    `/paper/autocomplete` answers `{"matches": [...]}`, and
    `GET /dataset/releases` answers a plain array of release ids.
  - Verified 2026-11-27: the published limits are 1000 requests per second
    for the shared anonymous pool and 1 request per second for an
    introductory key. The pool is contended, so the client defaults to 1
    request per second and concurrency 1.

### 5. DOAJ API v4 (Gold & Diamond OA Journals)

- **Base URL:** `https://doaj.org/api/v4` (paths: `search/journals/{query}`,
  `search/articles/{query}`, `journals/{id}`, `articles/{id}`; verified
  2026-11-27 that `journals` and `articles` have no list route)
- **Auth:** `NoAuth()` for public read/search.
- **`QueryDialect`:**
  `page_param="page"`, `page_start=1`, `page_size_param="pageSize"`,
  `max_page_size=50`, `default_page_size=10`, `sort_param="sort"`,
  `query_param=None` (search query is embedded in the path).
- **`ResponseUnwrapper`:** `results -> body["results"]`, `item -> body`,
  `total -> body.get("total")`, `next_cursor -> None`, `meta ->` envelope
  minus `results`.
- **Batching & Rate Limits:** Batch ISSN lookups via Lucene `OR` query
  (`issn:1234-5678 OR issn:8765-4321`) in `/search/journals/{query}`. Rate:
  **~2 req/s** (`max_requests_per_second=1.5` conservative default).
  Verified 2026-11-27: `pageSize` above 50 is cut to 50 and the default is 10.
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - API v1–v3 are deprecated; always target `/api/v4/`.
  - Search encodes the Lucene query as a URL-encoded path segment
    (`/search/journals/{query}`); handle via a resource method or path-building
    override.
  - Capture `bibjson.apc`, `bibjson.license`, `bibjson.preservation`,
    `bibjson.editorial.review_process`, and `bibjson.seal` for canonical Venue
    records.
  - Verified 2026-11-27: `/api/search/...` and `/api/v4/search/...` answer
    the same envelope. The client wraps v4.
  - Verified 2026-11-27: the API answers 400 beyond the first 1000 records of
    a query, because `(page - 1) * pageSize + pageSize` must be at most 1000.
    `page=0` is treated as page 1.
  - Verified 2026-11-27: wildcards answer 400. `AND`, `OR`, `ANDNOT`, quoted
    phrases, and ranges work. A license filter needs the stored spelling,
    such as `license:"CC BY"`.
  - Verified 2026-11-27: an unknown DOI answers 200 with `total` of 0. The
    client raises `NotFoundError` on an empty envelope.
  - Verified 2026-11-27: the documentation states a limit of 2 requests per
    second with bursts of five. The client defaults to 1 request per second.
  - Verified 2026-11-27: `GET /api/journals/{id}` and `GET /api/articles/{id}`
    answer 200 without a key for a DOAJ record id, with more fields than a
    search result (`es_type`, `last_manual_update`, and a fuller `admin`
    section).

### 6. OpenCitations (Index v2 + Meta v1)

- **Base URL:** `https://api.opencitations.net/index/v2` and
  `https://api.opencitations.net/meta/v1`
- **Auth:** `NoAuth()`. The optional OpenCitations Access Token is not in
  the client yet (see the [deferred list](deferred.md)).
- **`QueryDialect`:** Unpaged dialect: `page_size_param=None`,
  `page_param=None`, `offset_param=None`, `cursor_param=None`,
  `sort_param=None`, `query_param=None`, `select_param=None`.
- **`ResponseUnwrapper`:** Endpoints return a top-level JSON `list[dict]`:
  `results -> body`, `item -> body[0]` (raising `NotFoundError` when empty),
  `total -> len(body)`, `next_cursor -> None`, `meta -> {}`.
- **Batching & Rate Limits:** Verified 2026-11-27: the Meta API accepts
  `__`-delimited ids (`/metadata/doi:a__doi:b`, one row per id); the Index
  API answers `[]` for a multi-id path, so it takes one id per request.
  Rate: **180 req/min/IP** documented; the client defaults to 3 requests per
  second.
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - Legacy `COCI`, `POCI`, and `/index/v1` are deprecated/archived; target only
    `/index/v2` and `/meta/v1`.
  - Missing IDs return HTTP `200` with an empty JSON list `[]` rather than
    `404`; map empty responses cleanly in `get()` / `unwrapper.item()`.
  - Index v2 exposes `oci`, `citing`, `cited`, `creation`, `timespan`,
    `journal_sc`, and `author_sc` (self-citation flags).
  - Verified 2026-11-27: Index v2 has six operations (`/citation/{oci}`,
    `/citations/{id}`, `/references/{id}`, `/citation-count/{id}`,
    `/reference-count/{id}`, `/venue-citation-count/{issn}`), and Meta v1
    has three (`/metadata/{ids}`, `/author/{id}`, `/editor/{id}`). The rows
    accept `require`, `filter`, `sort`, and `format=csv` (the `Accept`
    header alone does not switch the format). Counts arrive as strings.

### 7. Europe PMC (Articles, Preprints, Citations & Annotations)

- **Base URL:** `https://www.ebi.ac.uk/europepmc/webservices/rest` (plus
  `https://www.ebi.ac.uk/europepmc/annotations_api`)
- **Auth:** `NoAuth()`.
- **`QueryDialect`:** Search (`/search`):
  `cursor_param="cursorMark"`, `cursor_start="*"`,
  `page_size_param="pageSize"`, `max_page_size=1000`, `default_page_size=25`,
  `iterate_page_size=1000`, `query_param="query"`, `sort_param="sort"`,
  `page_param=None`, `select_param=None` (use `resultType="core"` or `"lite"`).
- **`ResponseUnwrapper`:** `results -> body["resultList"]["result"]`,
  `total -> body["hitCount"]`, `next_cursor -> body.get("nextCursorMark")`,
  `meta ->` `request`, `version`.
- **Batching & Rate Limits:** Batch PMIDs/DOIs via Lucene `OR` query
  (`EXT_ID:12345 OR EXT_ID:67890`) in `/search`; annotations API batches 1–8
  article IDs per request. No hard key cap; polite **~5–10 req/s**.
- **License:** Open metadata; full-text reuse governed by explicit per-article
  CC license field.
- **Upstream Quirks:**
  - Always pass `format=json` (XML is the default otherwise!).
  - `cursorMark` echoes the current cursor when exhausted — already handled
    automatically by `ResourceClient._iterate_cursor()`.
  - Pass `resultType="core"` to retrieve full abstracts, grants, MeSH headings,
    and full-text URLs (`lite` omits them).
  - Verified 2026-11-27: `pageSize` accepts at most 1000, and a larger value
    answers 404. `nextCursorMark` repeats unchanged when the list is
    exhausted. A search can take about ten seconds and answers transient 503
    errors, which the client retries.
  - Verified 2026-11-27: the data links route is `/{source}/{id}/datalinks`
    in lower case, and `dataLinks` answers 404. The routes `comments`,
    `correctionsAndErratum`, and `textMinedTerms` answer 404 and are absent
    from the OpenAPI document. Comments and corrections are part of the core
    record, and text-mined terms moved to the annotations API.
  - Verified 2026-11-27: `fullTextXML` and `supplementaryFiles` take a bare
    id such as `PMC13810549`. They answer 406 to `Accept: application/json`
    and need `application/xml`. `bookXML` answers 200 with a message element
    for a book without open access XML.
  - Verified 2026-11-27: the grants API is the Grist API at
    `https://www.ebi.ac.uk/europepmc/GristAPI/rest/get/query=<q>&format=json&page=N`.
    The parameters must follow `&` and not `?`, because `?` makes the route
    answer 406 to a JSON `Accept` header. `HitCount` is a JSON string.
  - Verified 2026-11-27: the annotations API has five routes. Four of them
    page with a float `cursorMark` and signal exhaustion with a
    `nextCursorMark` of `-1.0`. `annotationsBySectionAndOrType` without a
    filter returns about 24 MB.

### 8. Zenodo / InvenioRDM (Datasets & Software Releases)

- **Base URL:** `https://zenodo.org/api` (generalizable to any InvenioRDM
  instance by swapping `base_url`)
- **Auth:** `NoAuth()` for public read (mandatory `User-Agent`, otherwise
  `403`); optional `StaticTokenAuth(token)` for higher page size (`100` vs
  `25`) and private/deposit access.
- **`QueryDialect`:** Use per-instance `dialect=` based on auth presence:
  `page_param="page"`, `page_start=1`, `page_size_param="size"`,
  `max_page_size=25` (unauth) or `100` (auth), `default_page_size=25`, and
  `page * size` at most 10,000 (Elasticsearch `max_result_window`, verified
  2026-11-27), `query_param="q"`, `sort_param="sort"`.
- **`ResponseUnwrapper`:** `results -> body["hits"]["hits"]`, `item -> body`,
  `total -> body["hits"]["total"]`, `next_cursor -> None` (or `links.next`),
  `meta -> {"aggregations": body.get("aggregations", {})}`.
- **Batching & Rate Limits:** Batch concept/version DOIs with an `OR`
  clause in `q`, which uses the Elasticsearch query-string syntax. Rate:
  verified 2026-11-27, about 78 requests at 2 per second met no limit and the
  API sent no rate-limit headers. The client defaults to 2 requests per
  second.
- **License:** Metadata **CC0**; record files per declared SPDX license
  (default CC-BY 4.0).
- **Upstream Quirks:**
  - Always distinguish `conceptdoi` (all versions) vs. `doi` (specific version)
    and preserve `files[].checksum` (`md5:...`).
  - Use `BaseApiClient.stream()` for downloading dataset/software archives so
    auth, throttling, and typed errors apply automatically.
  - Verified 2026-11-27: the API serves the legacy record schema
    (`recid`, `conceptrecid`, `metadata`), not the InvenioRDM schema that
    the documentation describes. A concept id answers 302 to the newest
    version, `mostrecent` orders by last update, and `all_versions=true`
    returns every version instead of one record per concept.
  - Verified 2026-11-27: `/api/vocabularies/{vocabulary}` serves the
    `resourcetypes`, `licenses`, `languages`, `communitytypes`, `funders`,
    and `affiliations` vocabularies in a hits envelope;
    `/api/communities/{id}/subcommunities` answers the RDM-shaped hits
    envelope; and `https://zenodo.org/oai2d` answers all six OAI-PMH verbs
    (a `ListRecords` call without a match answers 422 with
    `noRecordsMatch`).

### 9. DOI RA / Content Negotiation + ISSN Portal ConNeg

Two small lookup clients: `hodoi` for the DOI proxy at doi.org and
`seriatim` for the ISSN Portal.

- **Base URLs:**
  - `https://doi.org/ra/{doi1},{doi2}` — batch DOI Registration Agency lookup
    (returns JSON list of `{"DOI": ..., "RA": "Crossref" | "DataCite" | ...}`).
  - `https://doi.org/api/handles/{doi}` — raw Handle.net JSON record.
  - `https://doi.org/{doi}` — HTTP Content Negotiation with
    `follow_redirects=True` and `Accept: application/vnd.citationstyles.csl+json`
    (or `application/vnd.schemaorg.ld+json`, `application/x-bibtex`).
  - Verified 2026-11-27: Crossref answers CSL JSON, Unixref XML, BibTeX, and
    RIS, and answers 406 for schema.org JSON-LD and DataCite JSON; DataCite
    answers all of them; mEDRA answers CSL JSON, BibTeX, and RIS. The
    client keeps the catalog in `hodoi.media_types`.
  - `https://portal.issn.org/resource/ISSN/{issn}` with
    `Accept: application/ld+json` — JSON-LD lookup. Verified 2026-11-27:
    without that `Accept` header `?format=json` answers with HTML, and the
    JSON-LD is a single node.
- **Auth:** `NoAuth()`.
- **Batching & Rate Limits:** `/ra/{doi1},{doi2}` accepted a list of 200
  DOIs and answered 414 for 500 (verified 2026-11-27), so the client chunks
  at 100. `/doiRA/` serves the same route. doi.org publishes no limit; the
  client defaults to 2 requests per second. ISSN Portal free ConNeg is
  individual lookup only (polite pacing, aggressive local caching).
- **License:** Open resolution infrastructure; individual DOI metadata license
  follows its Registration Agency; ISSN Portal free ConNeg is non-bulk.
- **Upstream Quirks:**
  - doi.org redirects content negotiation to the data server of the
    registration agency (Crossref `api.crossref.org/v1/works/{doi}/transform`,
    DataCite `data.crosscite.org/{doi}`). The `Accept` header survives the
    redirect. The client follows redirects on the content request only, so
    that a caller can still read the 302.
  - Verified 2026-11-27: without an `Accept` header the proxy redirects to
    the landing page; `HEAD` answers 302 with the same `Location`; the
    Handle REST API accepts `index`, `type`, `auth`, and `recursive`; the
    old Handbook URL for resolution now redirects to a landing page, and
    the current reference is the DOI resolution documentation that the
    package cites.
  - Verified 2026-11-27: the ISSN Portal JSON-LD is one node per resource,
    not a `@graph` array as this spec assumed.
  - Verified 2026-11-27: the ISSN Portal answers JSON-LD for
    `/resource/ISSN/{issn}` and `/resource/ISSN-L/{issn}` only. The free
    search (`/search`) and the Title Word Abbreviation list (`/ltwa`) are
    HTML pages, which the client reads with the standard library parser.
    The portal has no SPARQL endpoint. The SRU Search API, OAI-PMH access,
    and the ISSN-H families need a paid subscription.

### 10. Wikidata (Universal PID Crosswalk Hub)

- **Base URLs:**
  - REST API v1: `https://www.wikidata.org/w/rest.php/wikibase/v1`
  - Action API (batch): `https://www.wikidata.org/w/api.php`
  - Optional SPARQL: `https://query.wikidata.org/sparql`
- **Auth:** `NoAuth()` (optional OAuth2). **Descriptive `User-Agent` with
  contact URL/email is strictly mandatory** (`BaseApiSettings.mailto` handles
  this cleanly; generic user agents receive immediate `429`).
- **`QueryDialect`:** Action `wbsearchentities`: `offset_param="continue"`,
  `page_size_param="limit"`, `max_page_size=50`, `default_page_size=25`,
  `query_param="search"`, `page_param=None`, `sort_param=None`.
- **`ResponseUnwrapper`:** Action `wbgetentities` returns a dict keyed by QID
  (`body["entities"]`); convert `list(body["entities"].values())` (filtering
  `"missing" in item`) in `results()`.
- **Batching & Rate Limits:** Override `_fetch_batch_chunk()` to call Action
  `wbgetentities` with `ids=Q1|Q2|...` (up to **50 QIDs per request**). Honor
  `Retry-After`; keep SPARQL queries under the 60s timeout and ≤5 concurrent.
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - Extract external IDs from well-known properties (`P496` ORCID, `P6782` ROR,
    `P213` ISNI, `P214` VIAF, `P227` GND, `P244` LCCN, `P269` IdRef, `P1278`
    LEI, `P236` ISSN, `P356` DOI, `P6179` / `P10283` OpenAlex).
  - Cache entity responses aggressively with `ETag` / `If-None-Match` when
    revalidating crosswalks.
  - Verified 2026-11-27 and 2026-11-28: the Action API answers every error
    with HTTP 200 and an `error` object, and `wbgetentities` takes at most
    50 ids. `wbsearchentities` reports no total. `Special:EntityData/{id}.{format}`
    serves one entity as `json`, `jsonld`, `rdf`, `nt`, `ttl`, or `n3`, and
    `https://www.wikidata.org/entity/{id}` redirects to it. The REST API
    adds `/search/*`, `/suggest/*`, and `/statements/*`. The lexeme routes
    live under `/w/rest.php/wikibaselexeme/v0`, and the linked-data endpoint
    of the query service is gone. The client wraps all of these read routes.
