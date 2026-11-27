# Wave 1 Client Specs & Core Enablers

This guide provides actionable starter specifications for the **6 targeted
`bibliofabric` core additions**, **2 immediate extensions to existing clients**,
and the **10 Wave 1 candidate client libraries**.

For the step-by-step recipe to scaffold, type-check, generate sync twins, and
test any client package in this workspace, see
[Building a client on `bibliofabric`](../bibliofabric/writing-a-client.md).

## `bibliofabric` Core Enablers

`bibliofabric` 0.7 already provides `retry=bool`, `_fetch_batch_chunk()`,
`page_size_param: str | None`, `max_offset`, per-instance `dialect=`,
`BasicAuth`, `ClientCredentialsAuth(token_auth_method="post")`,
`RefreshTokenAuth`, automatic 401 token refresh, `on_response()`, `stream()`,
`follow_redirects`, `connect_timeout`, and cached `TypeAdapter(list[E])`
validation.

Six lightweight, backwards-compatible core additions unlock the rest of Wave 1
and Wave 2 cleanly without per-client workarounds:

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
  `max_page_size=20`, `default_page_size=20`, `max_offset=10_000`,
  `query_param="query"`, `sort_param=None`, `select_param=None`.
- **`ResponseUnwrapper`:** `results -> body["items"]`,
  `total -> body["number_of_results"]`, `item -> body`, `next_cursor -> None`,
  `meta -> body["meta"]`.
- **Batching & Rate Limits:** No native multi-ID batch endpoint; use bounded
  concurrent `get()` or local Zenodo dump lookup. **2,000 req / 5 min**
  registered (~50 / 5 min unregistered).
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
- **Batching & Rate Limits:** Batch DOIs via `query=doi:(...)` or comma
  `ids=` filter in `build_batch_params()`. **500 unid / 1,000 identified /
  3,000 member per 5 min** per IP.
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - Deep pagination past 10,000 records requires `page[cursor]=1` on the first
    request (not `*`) and following `links.next`.
  - Normalize DOIs with `normalize_doi`; preserve `relatedIdentifiers` and
    `version` fields for dataset/software lineage.

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

### 5. DOAJ API v4 (Gold & Diamond OA Journals)

- **Base URL:** `https://doaj.org/api/v4` (paths: `journals`, `articles`,
  `search/journals`, `search/articles`)
- **Auth:** `NoAuth()` for public read/search.
- **`QueryDialect`:**
  `page_param="page"`, `page_start=1`, `page_size_param="pageSize"`,
  `max_page_size=100`, `default_page_size=25`, `sort_param="sort"`,
  `query_param=None` (search query is embedded in the path).
- **`ResponseUnwrapper`:** `results -> body["results"]`, `item -> body`,
  `total -> body.get("total")`, `next_cursor -> None`, `meta ->` envelope
  minus `results`.
- **Batching & Rate Limits:** Batch ISSN lookups via Lucene `OR` query
  (`issn:1234-5678 OR issn:8765-4321`) in `/search/journals/{query}`. Rate:
  **~2 req/s** (`max_requests_per_second=1.5` conservative default).
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - API v1–v3 are deprecated; always target `/api/v4/`.
  - Search encodes the Lucene query as a URL-encoded path segment
    (`/search/journals/{query}`); handle via a resource method or path-building
    override.
  - Capture `bibjson.apc`, `bibjson.license`, `bibjson.preservation`,
    `bibjson.editorial.review_process`, and `bibjson.seal` for canonical Venue
    records.

### 6. OpenCitations (Index v2 + Meta v1)

- **Base URL:** `https://api.opencitations.net/index/v2` and
  `https://api.opencitations.net/meta/v1`
- **Auth:** `NoAuth()` by default; optional `HeaderAuth("authorization", token)`
  for an anonymous OpenCitations Access Token.
- **`QueryDialect`:** Unpaged dialect: `page_size_param=None`,
  `page_param=None`, `offset_param=None`, `cursor_param=None`,
  `sort_param=None`, `query_param=None`, `select_param=None`.
- **`ResponseUnwrapper`:** Endpoints return a top-level JSON `list[dict]`:
  `results -> body`, `item -> body[0]` (raising `NotFoundError` when empty),
  `total -> len(body)`, `next_cursor -> None`, `meta -> {}`.
- **Batching & Rate Limits:** Override `item_path()` and `_fetch_batch_chunk()`
  for prefixed path IDs (`doi:10.1186/...`, `omid:br/...`) and `__`-delimited
  multi-ID path batching (`/metadata/doi:a__doi:b`). Rate: **180 req/min/IP**
  (`max_requests_per_second=2.5`).
- **License:** **CC0 1.0**.
- **Upstream Quirks:**
  - Legacy `COCI`, `POCI`, and `/index/v1` are deprecated/archived; target only
    `/index/v2` and `/meta/v1`.
  - Missing IDs return HTTP `200` with an empty JSON list `[]` rather than
    `404`; map empty responses cleanly in `get()` / `unwrapper.item()`.
  - Index v2 exposes `oci`, `citing`, `cited`, `creation`, `timespan`,
    `journal_sc`, and `author_sc` (self-citation flags).

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

### 8. Zenodo / InvenioRDM (Datasets & Software Releases)

- **Base URL:** `https://zenodo.org/api` (generalizable to any InvenioRDM
  instance by swapping `base_url`)
- **Auth:** `NoAuth()` for public read (mandatory `User-Agent`, otherwise
  `403`); optional `StaticTokenAuth(token)` for higher page size (`100` vs
  `25`) and private/deposit access.
- **`QueryDialect`:** Use per-instance `dialect=` based on auth presence:
  `page_param="page"`, `page_start=1`, `page_size_param="size"`,
  `max_page_size=25` (unauth) or `100` (auth), `default_page_size=25`,
  `max_offset=10_000`, `query_param="q"`, `sort_param="sort"`.
- **`ResponseUnwrapper`:** `results -> body["hits"]["hits"]`, `item -> body`,
  `total -> body["hits"]["total"]`, `next_cursor -> None` (or `links.next`),
  `meta -> {"aggregations": body.get("aggregations", {})}`.
- **Batching & Rate Limits:** Batch concept/version DOIs via Lucene `OR` query.
  Rate: **~30 req/min** on search (`max_requests_per_second=0.5`, stricter
  2025–2026 anti-scraping limits).
- **License:** Metadata **CC0**; record files per declared SPDX license
  (default CC-BY 4.0).
- **Upstream Quirks:**
  - Always distinguish `conceptdoi` (all versions) vs. `doi` (specific version)
    and preserve `files[].checksum` (`md5:...`).
  - Use `BaseApiClient.stream()` for downloading dataset/software archives so
    auth, throttling, and typed errors apply automatically.

### 9. DOI RA / Content Negotiation + ISSN Portal ConNeg

Lightweight router & lookup package (`doi-conneg` / `pid-resolvers`) critical
for canonical fusion Stage 1 routing:

- **Base URLs:**
  - `https://doi.org/ra/{doi1},{doi2}` — batch DOI Registration Agency lookup
    (returns JSON list of `{"DOI": ..., "RA": "Crossref" | "DataCite" | ...}`).
  - `https://doi.org/api/handles/{doi}` — raw Handle.net JSON record.
  - `https://doi.org/{doi}` — HTTP Content Negotiation with
    `follow_redirects=True` and `Accept: application/vnd.citationstyles.csl+json`
    (or `application/vnd.schemaorg.ld+json`, `application/x-bibtex`).
  - `https://portal.issn.org/resource/ISSN/{issn}?format=json` — JSON-LD
    `@graph` lookup returning authoritative **ISSN-L**, key title, ROAD OA, and
    **Keepers** archival preservation metadata.
- **Auth:** `NoAuth()`.
- **Batching & Rate Limits:** `/ra/{doi1},{doi2}` batches ~50–100 DOIs per
  call via comma-joined path override; ISSN Portal free ConNeg is individual
  lookup only (polite pacing, aggressive local caching).
- **License:** Open resolution infrastructure; individual DOI metadata license
  follows its Registration Agency; ISSN Portal free ConNeg is non-bulk.
- **Upstream Quirks:**
  - Set `follow_redirects=True` on `BaseApiSettings` for DOI ConNeg (doi.org
    redirects to RA content-negotiation servers; verify `Accept` header is
    preserved across cross-host redirects).
  - ISSN Portal JSON-LD returns a `@graph` array containing separate nodes for
    the `ISSN`, `ISSN-L`, `Organization`, and `ArchivalResource` (Keepers);
    index nodes by `@id`/`@type` inside the unwrapper/parser.

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
