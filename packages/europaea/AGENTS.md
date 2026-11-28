# europaea: Project Guide

europaea is a placeholder name. Rename the distribution name, the import
name, the environment prefix (`EUROPAEA_`), the class prefix
(`Europaea`), and the directories `packages/europaea`,
`src/europaea`, and `docs/europaea` together.

europaea is an async + generated-sync Python client for the Europe PMC
REST web services (plus the annotations API and the grants Grist API), built
on bibliofabric 0.8. Not yet published.

## Architecture

One generic framework layer (bibliofabric) plus a Europe PMC-specific
overlay. Async I/O modules under `_async/` are the single source of truth;
`scripts/unasync.py --package europaea` generates the `_sync/` twins:

```
EuropaeaClient / EuropaeaSyncClient
 ├─ search        # /search + /fields (cursor paging)
 ├─ articles      # /article/{source}/{id} and the per-article routes
 ├─ annotations   # https://www.ebi.ac.uk/europepmc/annotations_api
 ├─ grants        # https://www.ebi.ac.uk/europepmc/GristAPI/rest/get
 ├─ profiles      # /profile + /fields
 └─ preprints     # /search scoped to SRC:PPR
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `EuropaeaClient(BaseApiClient)`. No credentials. `default_headers` sends `Accept: application/json`; the XML routes and the Grist API override it per request. Resources are cached properties. |
| `_async/resources.py` | `EUROPEPMC_API_BASE_URL`, `ANNOTATIONS_API_BASE_URL`, `GRIST_API_BASE_URL`, the two `QueryDialect` instances (cursor search dialect and page-numbered list dialect, `pageSize` cap 1000), and `EuropepmcResourceClient` (adds `format=json` to every search request). |
| `_async/search.py` | `SearchClient`: `search` and `iterate` gain `result_type` (`idlist`, `lite`, `core`, `json`, `xml`, `dc`) and `synonym`; sort is checked against the known sort fields; `fields()` returns the `/fields` terms. |
| `_async/articles.py` | `ArticlesClient`: `get("MED:23903748")` (core record), `full_text_xml`, `book_xml` (both return `XmlDocument`), `supplementary_files` (ZIP bytes), `references`, `citations`, `database_links` (paged via the framework), `data_links`, `labs_links`, `evaluations`, and `exists()` through `GET` (the gateway answers `HEAD` with 405). `split_article_id()` parses combined ids. A miss on the XML routes answers HTTP 200 with a wrapper document; `_parse_xml_wrapper()` reads its `message` and `isOpenAccess` and raises `NotFoundError`. |
| `_async/annotations.py` | `AnnotationsClient` against the separate annotations API: `by_article_ids` (returns a list), `by_entity`, `by_provider`, `by_relationship`, `by_section` (each returns an `AnnotationPage`; a repeated negative cursor means exhaustion and maps to `next_cursor_mark=None`). |
| `_async/grants.py` | `GrantsClient` against the Grist API. The parameters are glued to the query path (`get/query=malaria&format=json&page=2`); with a `?` query string the route content-negotiates and answers 406 for `Accept: application/json`. `search()` returns the typed envelope, `iterate()` walks pages until the record list empties. |
| `_async/profiles.py` | `ProfilesClient.profile()` (single response, not paged) and `.fields()`. |
| `_async/preprints.py` | `PreprintsClient` subclasses `SearchClient` and wraps every query in `SRC:PPR AND (...)`. |
| `_async/unwrapper.py` | `EuropaeaUnwrapper`: reads `resultList.result`, `referenceList.reference`, `citationList.citation`, `databaseLinkList.databaseLink`, `hitCount`, and `nextCursorMark` (a repeated cursor means exhaustion, which the framework cursor iteration already stops on). `item()` unwraps the `result` key of `/article/{source}/{id}`. |
| `config.py` | `EuropaeaSettings(BaseApiSettings)`, env prefix `EUROPAEA_`. Defaults: 3 requests per second, concurrency 2, timeout 30 (the framework default; a search can take about ten seconds). The documentation publishes no rate limit. |
| `models/` | Pydantic v2 models, `extra="allow"`, camelCase aliases, `populate_by_name` where a key is not a valid identifier. |

## Conventions

- Base URLs: REST `https://www.ebi.ac.uk/europepmc/webservices/rest`,
  annotations `https://www.ebi.ac.uk/europepmc/annotations_api`,
  Grist `https://www.ebi.ac.uk/europepmc/GristAPI/rest/get`.
- Every JSON route sends `format=json`. XML answers are returned as text in
  `XmlDocument`; typed JATS parsing is out of scope.
- Combined article ids use `SOURCE:ID` (`MED:23903748`, `PMC:PMC4221854`);
  the XML and supplementary routes take bare ids (`PMC13810549`, `NBK32884`).
- Search pages with `cursorMark` tokens (`pageSize` at most 1000). References
  and citations page with `page` and `pageSize`.
- Live facts and dates live in `docs/europaea/upstream-quirks.md`.
- stdlib logging only; errors raise bibliofabric exceptions.

## Testing

- Offline tests mock HTTP with pytest-httpx; every request needs a registered
  response. They run once in `tests/` (no I/O) and in both variants under
  `tests/_async/` and the generated `tests/_sync/`.
- Live smoke tests: `tests/_async/test_live_api.py` with the `live_api`
  marker. They stay small (about 15 requests) to respect the shared host.
- Gate commands run from the repo root with `PYTHONPATH=packages/europaea/src`:
  `ruff check`, `ruff format --check`, `ty check src tests`,
  `scripts/unasync.py --check --package europaea`, `pytest`, and
  `pytest -m live_api`.
