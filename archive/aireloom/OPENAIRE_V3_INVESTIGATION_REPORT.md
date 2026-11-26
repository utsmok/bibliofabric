# OpenAIRE Graph API V3 — Fresh Investigation Report

**Date:** 2026-07-15
**Reporter:** AIREloom client library maintainers
**Scope:** Verify resolution of the 21 issues reported in `OPENAIRE_BUG_REPORT.md` (2026-06-04); identify new V3 functionality; assess documentation correctness; catalog any remaining/new issues.
**APIs tested:** OpenAIRE Graph API **V3** (`/graph/v3/*`), Scholexplorer V3 (`/v3/Links`). V1/V2 spot-checked for deprecation status.
**Method:** Every server/behavioral claim below was verified against the **live API** using OAuth2 client-credentials auth on 2026-07-15. Documentation/OpenAPI-spec claims were verified against the published OpenAPI JSON (`/graph/v3/api-docs/<group>`) and the Docusaurus docs site (`graph.openaire.eu/docs`). The exact reproduction commands and observed responses are quoted inline.

---

## Executive Summary

OpenAIRE released **Graph API V3** on/around 2026-07-15. V1 and V2 are now officially **deprecated** (still functional, slated for removal in ~6 months). V3 is the recommended version.

**Scorecard against the original 21 issues:**

| Outcome | Count | IDs |
|---------|-------|-----|
| ✅ **Fixed / N/A** | 9 | S1, S2, D1, D2, D3, D4, D10, D11, O5 |
| 🟡 **Improved (likely data, not a bug)** | 1 | O6 |
| ❌ **Still broken** | 11 | D5, D6, D7, D8, D9, O1, O2, O3, O4, O7, O8, O9 |

**Headlines:**
- The two **Critical server errors** (persons `givenName`/`lastName` → HTTP 500) are **FIXED**.
- V3 is a genuine improvement: kebab-case URLs, many new filters, full cursor pagination, inline logical operators, proper `pageSize` validation on regular endpoints (now correctly accepts ≤100, rejects >100 instead of silently capping).
- However, **all 7 behavioral/consistency bugs on the links & Scholix endpoints persist unchanged** in V3. The links endpoint (`/v3/research-products/links`) is still a second-class citizen: different header envelope, 0-indexed pages, silent `pageSize=100`→10 cap, no cursor support.
- Several copy-paste documentation/spec errors (datasources described as "organizations") persist in both the OpenAPI spec *and* runtime error messages.
- A **V4 BETA ("unified filters")** is now publicly listed — a major forthcoming redesign (OpenAlex-style `filter=` predicates).

---

## 1. Master Status Table — All 21 Prior Issues

| ID | Sev | Category | Endpoint | Issue (original) | V3 Status | Evidence |
|----|-----|----------|----------|------------------|-----------|----------|
| **S1** | Critical | Server | `/persons` | `givenName` → 500 | ✅ **FIXED** | `GET /v3/persons?givenName=John` → **200**, `numFound=35018` |
| **S2** | Critical | Server | `/persons` | `lastName` → 500 | ✅ **FIXED** | `GET /v3/persons?lastName=Smith` → **200**, `numFound=12917` |
| **D1** | High | Docs | All | `debugQuery` documented but doesn't exist | ✅ **N/A** | Parameter removed from all public V3 endpoints (survives only in internal `SolrQueryParams` schema) |
| **D2** | Med | Docs | RP | `rorId` works but undocumented | ✅ **FIXED** | Now a documented param with examples on `/v3/research-products` |
| **D3** | Med | Docs | All | `logicalOperator` undocumented | ✅ **FIXED** | Now documented on all 5 entities, enum `[AND, OR, NOT]` (V3 adds `NOT`) |
| **D4** | High | Docs | Persons | Filtering docs 404 | ✅ **FIXED** | Page exists at `/docs/apis/graph-api/persons/` |
| **D5** | High | Docs | Links | Entire endpoint undocumented | ❌ **STILL BROKEN** | `/docs/apis/graph-api/research-products/links` → **404**. Only in OpenAPI spec. |
| **D6** | Low | Docs | DS | `legalShortName` says "organization" | ❌ **STILL BROKEN** | Docusaurus datasources page + OpenAPI spec both still say "The legal name of the **organization** in short form" |
| **D7** | Low | Docs | Scholix spec | Title typo "ScholeExplorer" | ❌ **STILL BROKEN** | `info.title` still `"ScholeExplorer APIs"` |
| **D8** | Low | Docs | Scholix spec | `page` marked required, actually optional | ❌ **STILL BROKEN** | Spec still has `page.required = true`; runtime returns 200 without it (`currentPage=0`) |
| **D9** | Low | Docs | DS spec | sortBy description says "organizations" | ❌ **STILL BROKEN** | `/v3/datasources` sortBy spec: "…**organizations** can be only sorted by the 'relevance'." |
| **D10** | High | Docs | Persons spec | sortBy includes non-functional startDate/endDate | ✅ **FIXED** | V3 persons sortBy pattern is now `(relevance)` only; desc says "persons can be only sorted by the 'relevance'" |
| **D11** | Med | Docs | V2 | V2 not documented as separate version | ✅ **FIXED** | Overview states "V3 … superseding V1 and V2"; V1/V2 marked "(deprecated)" in spec |
| **O1** | Critical | Behavior | `/links` | `pageSize=100` silently → 10 | ❌ **STILL BROKEN** | `pageSize=100` → 10 results, `totalPages=13`; `pageSize=99` → 99 results, `totalPages=2` |
| **O2** | Critical | Behavior | Scholix | `size=100` silently → 10 | ❌ **STILL BROKEN** | `size=100` → 10 results; `size=99` → 99 results |
| **O3** | Med | Behavior | RP | sortBy error omits `popularity` | ❌ **STILL BROKEN** | Error lists `relevance, publicationDate, dateOfCollection, influence, citationCount, impulse` — omits `popularity` (which **does** work) |
| **O4** | Low | Behavior | DS | sortBy error says "organizations" | ❌ **STILL BROKEN** | Error: "…**organizations** can be only sorted by the 'relevance'." |
| **O5** | Med | Data | Scholix | Publisher `IDURL` always null | ✅ **FIXED** | 0/30 null (all populated) in sampled links |
| **O6** | Med | Data | Scholix | Creator `identifier` ~94% empty | 🟡 **IMPROVED (likely data)** | 16/19 empty in sample. Likely reflects real ORCID coverage, not a bug. |
| **O7** | Med | Consistency | Links | Different response header format | ❌ **STILL BROKEN** | Links header = `{page, totalPages, totalLinks}` — no `numFound`, `pageSize`, `maxScore`, `nextCursor` |
| **O8** | High | Consistency | Graph | Page indexing 0 vs 1 inconsistent | ❌ **STILL BROKEN** | Regular V3 endpoints: `page=0` → 400 (1-indexed). Links & Scholix: `page=0` = first page (0-indexed). |
| **O9** | High | Behavior | Links | Default pageSize=10, spec says 100 | ❌ **STILL BROKEN** | No `pageSize` → 10 results, `totalPages=13` (would be 2 if default were 100) |

---

## 2. Remaining Issues — Detailed (with reproduction)

### Persistent: Links & Scholix silent page-size cap (O1, O2, O9) — **Critical**

The single most impactful remaining defect. Requesting the documented maximum page size silently truncates results with no error and no indication. Effective maximum is **99**.

```
# Graph links (V3)
GET /graph/v3/research-products/links?sourcePid=10.1016/j.respol.2021.104226&pageSize=100&page=0
→ 200 {"header":{"page":0,"totalPages":13,"totalLinks":121}, "results":[ ...10 items... ]}

GET /graph/v3/research-products/links?sourcePid=10.1016/j.respol.2021.104226&pageSize=99&page=0
→ 200 {"header":{"page":0,"totalPages":2,"totalLinks":121}, "results":[ ...99 items... ]}

# Scholix (V3)
GET /v3/Links?sourcePid=10.1016/j.respol.2021.104226&size=100
→ 200 {"currentPage":0,"totalLinks":121,"totalPages":13,"result":[ ...10 items... ]}
```

Note: the **regular** Graph endpoints (`/v3/research-products`, etc.) now handle this **correctly** — `pageSize=100` returns 100, `pageSize=200` returns a proper `400`. The defect is isolated to the links and Scholix endpoints.

### Persistent: Inconsistent page indexing (O8) — **High**

```
GET /graph/v3/research-products?search=covid&page=0   → 400  (regular endpoints are 1-indexed)
GET /graph/v3/research-products?search=covid&page=1   → 200  (first page)
GET /graph/v3/research-products/links?...&page=0      → 200  (links are 0-indexed — first page)
GET /v3/Links?...&page=0                              → 200  (Scholix is 0-indexed)
```

### Persistent: Links endpoint response envelope divergence (O7) — **Medium**

| Field | Regular V3 endpoint | Links endpoint | Scholix |
|-------|---------------------|----------------|---------|
| `numFound` | ✅ | ❌ | ❌ |
| `pageSize` | ✅ | ❌ | ❌ |
| `maxScore` | ✅ | ❌ | ❌ |
| `nextCursor` | ✅ (with cursor) | ❌ | ❌ |
| `totalPages` | ❌ | ✅ | ✅ |
| `totalLinks` | ❌ | ✅ | ✅ |
| page indexing | 1-indexed | 0-indexed | 0-indexed |

The links endpoint still has **no cursor pagination** support.

### Persistent: Copy-paste "organizations" on datasources (D6, D9, O4) — **Low–Medium**

Three related manifestations of the same copy-paste error, all unfixed:
- **D6 (docs + spec):** `legalShortName` described as "the legal name of the **organization**".
- **D9 (spec):** datasources `sortBy` description says "**organizations** can be only sorted…".
- **O4 (runtime):** the `400` error message from `/v3/datasources` for a bad sortBy also says "**organizations**".

### Persistent: RP sortBy error omits `popularity` (O3) — **Medium**

`popularity` is a valid, working sort field (`sortBy=popularity DESC` → 200), but the invalid-sort error message lists only `relevance, publicationDate, dateOfCollection, influence, citationCount, impulse` — omitting `popularity`. The OpenAPI spec pattern correctly includes it; only the error message is wrong.

### Persistent: Scholix OpenAPI spec defects (D7, D8) — **Low**
- **D7:** `info.title` is `"ScholeExplorer APIs"` (should be `Scholexplorer`).
- **D8:** `page` is declared `required: true` but is optional at runtime.

### Persistent: Links endpoint has no Docusaurus docs page (D5) — **High**
`/docs/apis/graph-api/research-products/links` → 404. The endpoints exist in the OpenAPI spec but have no documentation-site page.

---

## 3. New Issues Discovered in V3

### NEW-1: `info.version` still missing from every OpenAPI spec
None of the V1, V3, V4-BETA, or Scholix specs include an `info.version` field. The original report's "version numbering confusion" general note is unresolved. (Note: the api-docs path is still `/graph/v3/api-docs/` where the `v3` is a Springdoc group name, not the API version — the same confusion persists.)

### NEW-2: Scholexplorer `/v3/api-docs` returns HTTP 500
The standard Springdoc root path `https://api.scholexplorer.openaire.eu/v3/api-docs` returns **500**. The spec is only reachable via the group path `/api-docs/Scholexplorer%20API%20V3.0`.

### NEW-3: V3 filter values containing spaces/parens must be double-quoted
This is a **behavioral change that affects every V3 client**, not strictly a bug, but it is under-documented and easy to hit. Filter values containing spaces, parentheses, or logical operators must be wrapped in double quotes (URL-encoded `%22`):

```
GET /v3/research-products?accessRightLabel=Open Access     → 400  "must be wrapped in double quotes"
GET /v3/research-products?accessRightLabel=%22Open+Access%22 → 200   ✅
```

Most filter params now support **inline logical operators** with the `("a" OR "b") AND NOT "c"` syntax, e.g. `countryCode=("US" OR "GB") AND NOT "DE"`.

### NEW-4: Some V3 filters accept only specific enumerated values (not in spec enums)
`accessRightLabel`, `sdgLabel`, `openAccessColor`, and the `*Class` impact filters accept only specific string values. The spec describes them as plain `type: string` without an `enum`, so clients only learn valid values from the `400` error. Discovered enums:
- `accessRightLabel`: `Open Access`, `Closed Access`, `Restricted`, `Open Source`, `Embargo`, `Unknown`
- `sdgLabel`: `1. No poverty` … `16. Peace & justice` (full SDG labels)
- `openAccessColor`: `bronze`, `gold`, `hybrid`
- `influenceClass` / `popularityClass` / `impulseClass` / `citationCountClass`: `C1`–`C5`

---

## 4. New V3 Functionality (verified working)

### API surface
- **V3 kebab-case URLs:** `/v3/research-products`, `/v3/projects`, `/v3/persons`, `/v3/organizations`, `/v3/datasources` (note: `datasources` is all-lowercase; `research-products` is kebab-case). All 12 endpoints (search + get-by-id + links + relations-info) preserved.
- **Proper `pageSize` validation** on regular endpoints: accepts 1–100, rejects >100 with a clean 400 (replaces the old silent behavior).
- **Cursor pagination** on all regular V3 endpoints (`cursor=*` → `nextCursor`).
- **Max 10,000 records** for page-based pagination; cursor required beyond that.
- **`logicalOperator` now supports `NOT`** in addition to `AND`/`OR`.

### New research-product filters (20 added)
`accessRightLabel` (replaces `bestOpenAccessRightLabel`), `authorId` (replaces `authorOrcid`), `sdgLabel` (replaces `sdg`), `eoscIfGuidelines`, `excludePubDateRange`, `fromPublicationYear`, `toPublicationYear`, `publicationYear`, `hasLicense`, `language`, `relCommunityName`, `relFunder`, `relFundingLevel0Id`, `relFundingLevel1Id`, `relFundingLevel2Id`, `relHostingDataSource`, `relOrganization`, `relProject`, `source`, `subCommunity`.

### New project filters (13 added)
`activeYear`, `startYear`, `endYear`, `fromStartYear`, `toStartYear`, `fromEndYear`, `toEndYear`, `country`, `funder`, `fundinglevel0Id`, `fundinglevel1Id`, `fundinglevel2Id`, `projectOAMandatePublications`.

### New datasource filters (8 added)
`collectedFromName`, `compatibilityId`, `compatibilityName`, `country`, `eoscdatasourcetype`, `jurisdiction`, `odLanguages`, `thematic`.

### Forthcoming: V4 BETA — "Unified Filter API"
A redesigned API is publicly listed (BETA). Key differences from V3:
- Single `filter` parameter with comma-separated `field:value` predicates (OpenAlex-style); `|` for OR, `!` for negation, `>`/`<` for ranges.
- `sort` replaces `sortBy` (`citation_count:desc,publication_date:desc`).
- New `select` (sparse fieldsets), `facets`, `group_by`, `mailto` (polite pool) parameters.
- `page_size` replaces `pageSize`.
- Search-only (no get-by-id endpoints yet), 5 entities.

**Recommendation:** Track V4 but **target V3 now** — V4 is explicitly BETA and lacks get-by-id endpoints.

---

## 5. Documentation Correctness Assessment

The Docusaurus docs site (`graph.openaire.eu/docs`, v11.2.0) is substantially improved: per-entity sections (overview, filtering, sorting, examples) exist for all 5 entities, with dedicated SDG and Fields-of-Science pages. Remaining doc defects:
- **D5:** No links-endpoint page (404).
- **D6:** Datasources `legalShortName` copy-paste error persists on the page.
- The OpenAPI spec (the de-facto source of truth) still carries D7, D8, D9 copy-paste errors and is missing `info.version` everywhere.

Overall: documentation correctness is **good for the 5 primary entities**, **poor for the links/Scholix endpoints**, and the OpenAPI spec still needs copy-editing.

---

## 6. Recommendations to OpenAIRE

1. **Fix the links/Scholix page-size cap** (O1/O2/O9) — either honor `pageSize=100`/`size=100` or reject >99 with a 400. Silent truncation causes data loss.
2. **Unify the links endpoint envelope and pagination** (O7/O8) — bring it onto the same `header{numFound,pageSize,nextCursor}` + 1-indexed-page contract as the rest of V3, or document the divergence prominently.
3. **Fix the `popularity` omission in the RP sortBy error message** (O3).
4. **Fix the datasources "organizations" copy-paste** in spec description (D9), runtime error (O4), and `legalShortName` docs (D6).
5. **Add the missing links docs page** (D5).
6. **Add `info.version` to all OpenAPI specs** (NEW-1) and document the quoting requirement for filter values (NEW-3).
7. **Fix the Scholix spec** title typo (D7), `page.required` (D8), and the `/v3/api-docs` 500 (NEW-2).

---

*Generated alongside `V3_MIGRATION_PLAN.md`, which translates these findings into a concrete AIREloom implementation plan.*
