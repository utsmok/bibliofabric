# OpenAIRE API Bug Report

**Date:** 2026-06-04
**Reporter:** AIREloom client library maintainers  
**APIs tested:** OpenAIRE Graph API v1/v2, Scholexplorer v3  
**Method:** All bugs verified against live API endpoints using OAuth2 client credentials authentication, cross-referenced against OpenAPI specifications and official documentation at `graph.openaire.eu/docs`.

---

## General Note: Version Numbering Confusion

The OpenAIRE API ecosystem has a deeply confusing version numbering scheme that makes it difficult for API consumers to understand what version they are using:

- **OpenAPI spec URLs** live under `/graph/v3/api-docs/` — the `v3` here does **not** refer to the API version. It appears to be a documentation/Swagger UI version.
- **Actual API paths** use `/v1/` and `/v2/` (e.g., `/graph/v1/researchProducts`, `/graph/v2/researchProducts`).
- The **Graph itself** may have its own version. The spec server URL is `https://api.openaire.eu/graph` with no version, while the spec URL has `/v3/`.
- **Scholexplorer** has its own separate versioning (`/v3/Links`) with no stated relationship to Graph API versions.
- **V2** of the Graph API only covers `researchProducts` — no other entities. This is not clearly documented.
- None of the three OpenAPI specs include an `info.version` field.

**Recommendation:** Adopt a single, clear versioning scheme. Document which version covers which endpoints. Include `info.version` in all OpenAPI specs.

---

## 1. Server Errors (Documented Parameters That Cause 500 Errors)

### BUG-S1: `givenName` filter on `/v1/persons` returns HTTP 500

**Endpoint:** `GET /v1/persons`  
**Parameter:** `givenName`  
**Expected:** 200 with filtered results (parameter is documented in OpenAPI spec)  
**Actual:** HTTP 500 — `"undefined field givenName"`

```
GET https://api.openaire.eu/graph/v1/persons?givenName=John&pageSize=1
→ 500 {"message":"Error from server at [...]. undefined field givenName","error":"Internal Server Error","code":500}
```

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/persons?givenName=John&pageSize=1"`  
**Spec reference:** `givenName` is listed as a parameter in the `/v1/persons` OpenAPI spec with `type: string`.

---

### BUG-S2: `lastName` filter on `/v1/persons` returns HTTP 500

**Endpoint:** `GET /v1/persons`  
**Parameter:** `lastName`  
**Expected:** 200 with filtered results (parameter is documented in OpenAPI spec)  
**Actual:** HTTP 500 — `"undefined field lastName"`

```
GET https://api.openaire.eu/graph/v1/persons?lastName=Smith&pageSize=1
→ 500 {"message":"Error from server at [...]. undefined field lastName","error":"Internal Server Error","code":500}
```

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/persons?lastName=Smith&pageSize=1"`  
**Spec reference:** `lastName` is listed as a parameter in the `/v1/persons` OpenAPI spec with `type: string`.

---

## 2. Missing or Wrong Documentation

### BUG-D1: `debugQuery` parameter documented on website but does not exist

**Location:** `graph.openaire.eu/docs/apis/graph-api/searching-entities/filtering-search-results`  
**Affected entities:** Research products, organizations, data sources, projects (all listed in the docs table)

The documentation website lists `debugQuery` as a valid parameter with description "Retrieve debug information for the search query. (Boolean)". However:

1. The parameter is **not in the OpenAPI spec** for any endpoint.
2. The live API **rejects it** with: `"Unknown parameter: debugQuery"`

```
GET https://api.openaire.eu/graph/v1/researchProducts?debugQuery=true&pageSize=1
→ 400 {"message":"Unknown parameter: debugQuery; valid parameters are: [...]"}
```

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/researchProducts?debugQuery=true&pageSize=1"`

---

### BUG-D2: `rorId` parameter missing from documentation website

**Location:** `graph.openaire.eu/docs/apis/graph-api/searching-entities/filtering-search-results`  
**Section:** Research products parameter table

The `rorId` parameter is in the OpenAPI spec and works on the live API, but is **not listed** in the documentation website's parameter table for research products.

```
GET https://api.openaire.eu/graph/v1/researchProducts?rorId=https://ror.org/0576by029&pageSize=1
→ 200 (returns results)
```

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/researchProducts?rorId=https://ror.org/0576by029&pageSize=1"`

---

### BUG-D3: `logicalOperator` parameter missing from documentation website

**Location:** `graph.openaire.eu/docs/apis/graph-api/searching-entities/filtering-search-results`

The `logicalOperator` parameter is documented in the OpenAPI spec for **all five entities** (research products, projects, organizations, data sources, persons) and works on the live API, but is **not mentioned** in the documentation website's parameter tables for any entity.

The website has a "Using logical operators" section describing `AND`/`OR`/`NOT` syntax within filter values, but does not document the separate `logicalOperator` query parameter that controls how multiple filter parameters are combined.

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/researchProducts?search=covid&logicalOperator=OR&pageSize=1"`

---

### BUG-D4: Persons endpoint has no documentation page

**Location:** `graph.openaire.eu/docs/apis/graph-api/searching-entities/filtering-search-results/persons`  
**Expected:** Filtering documentation for the persons endpoint  
**Actual:** HTTP 404

The persons endpoint (`/v1/persons`) exists in the API and is fully documented in the OpenAPI spec, but the filtering documentation page returns 404. The main filtering page only has sections for research products, organizations, data sources, and projects — persons is completely absent.

---

### BUG-D5: Links endpoint has no documentation

**Endpoint:** `GET /v1/researchProducts/links` and `GET /v1/researchProducts/links/relations-info`

Two endpoints exist in the OpenAPI spec and work on the live API, but are **not documented anywhere** on `graph.openaire.eu/docs`. There is no mention of the links endpoint or relations-info endpoint in the navigation, searching, or filtering documentation.

---

### BUG-D6: Data sources `legalShortName` description is wrong

**Location:** `graph.openaire.eu/docs/apis/graph-api/searching-entities/filtering-search-results` (Data sources section)

The documentation describes `legalShortName` as: *"The legal name of the organization in short form."* But this is a **data source** parameter — it should say "The legal name of the data source in short form."

This is a copy-paste error from the organizations section.

---

### BUG-D7: Scholix OpenAPI spec title has typo

**Location:** Scholexplorer OpenAPI spec (`/api-docs/Scholexplorer%20API%20V3.0`)

The spec title is `"ScholeExplorer APIs"` — should be `"ScholeXplorer APIs"` or `"Scholexplorer APIs"` (the correct name used elsewhere).

Additionally, the spec description contains `"TThe Scholexplorer API"` — should be `"The Scholexplorer API"` (double 'T').

---

### BUG-D8: Scholix `page` parameter marked as required but is actually optional

**Location:** Scholexplorer OpenAPI spec, `/v3/Links` endpoint

The `page` parameter has `"required": true` in the spec, but the API works fine without it (returns page 0 by default).

```
GET https://api.scholexplorer.openaire.eu/v3/Links?sourcePid=10.1016/j.respol.2021.104226&size=2
→ 200 {"currentPage": 0, "totalLinks": 118, ...}
```

**Reproduction:** `curl "https://api.scholexplorer.openaire.eu/v3/Links?sourcePid=10.1016/j.respol.2021.104226&size=2"`

---

### BUG-D9: Data sources `sortBy` OpenAPI spec description says "organizations"

**Location:** Graph API v1 OpenAPI spec, `/v1/dataSources` sortBy parameter

The `sortBy` parameter description reads: *"The field should be in the format 'fieldname ASC|DESC', organizations can be only sorted by the 'relevance'."*

This is a copy-paste error from the organizations endpoint. Should say "data sources" instead of "organizations".

---

### BUG-D10: Persons `sortBy` spec documents `startDate` and `endDate` but they don't work

**Location:** Graph API v1 OpenAPI spec, `/v1/persons` sortBy parameter

The spec description and regex pattern both include `startDate` and `endDate` as valid sort fields:

```json
{
  "description": "...fieldname is one of 'relevance', 'startDate', 'endDate'...",
  "schema": {
    "pattern": "^((relevance|startDate|endDate)\\s+(ASC|DESC),?\\s*)+$"
  }
}
```

But the live API **rejects both** with 400:

```
GET /graph/v1/persons?sortBy=startDate+DESC&pageSize=1
→ 400 {"message":"Invalid field name in sortBy parameter: startDate"}

GET /graph/v1/persons?sortBy=endDate+DESC&pageSize=1
→ 400 {"message":"Invalid field name in sortBy parameter: endDate"}
```

Only `relevance` actually works. This appears to be the projects sortBy spec copied to persons without adjusting the valid fields.

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/persons?sortBy=startDate+DESC&pageSize=1"`

---

### BUG-D11: V2 API is not documented as a separate version

**Location:** `graph.openaire.eu/docs`

The Graph API V2 (`/v2/researchProducts`) provides enriched research product responses (includes `projects`, `organizations`, `communities`, `collectedFrom` fields not available in V1). However:

- The documentation website does not explain what V2 is or when to use it
- There is no changelog or migration guide between V1 and V2
- The filtering documentation uses V2 URLs in some examples but doesn't explain why
- V2 only covers research products — this limitation is not documented

---

## 3. Other Issues

### BUG-O1: `pageSize=100` silently returns 10 results on links endpoint

**Endpoint:** `GET /v1/researchProducts/links`  
**Affected parameter:** `pageSize`

Requesting `pageSize=100` (the documented maximum) silently falls back to 10 results. No error is returned. The `totalPages` value confirms the server is using `pageSize=10` internally.

| pageSize | Results returned | totalPages | Expected |
|----------|-----------------|------------|----------|
| 10 | 10 | 12 | 12 |
| 50 | 50 | 3 | 3 |
| 99 | 99 | 2 | 2 |
| 100 | **10** | **12** | 2 |

The OpenAPI spec says default is 100, but the actual default is 10. And the documented maximum of 100 silently fails.

```
GET https://api.openaire.eu/graph/v1/researchProducts/links?sourcePid=10.1016/j.respol.2021.104226&pageSize=100&page=0
→ 200 {"header":{"page":0,"totalPages":12,"totalLinks":118},"results":[...10 items...]}
```

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/researchProducts/links?sourcePid=10.1016/j.respol.2021.104226&pageSize=100&page=0"`

**Effective maximum:** 99

---

### BUG-O2: `size=100` silently returns 10 results on Scholix

**Endpoint:** `GET /v3/Links` (Scholexplorer)  
**Affected parameter:** `size`

Identical behavior to BUG-O1. Requesting `size=100` (the documented maximum: *"max is 100"*) silently returns 10 results.

| size | Results returned | totalPages | Expected |
|------|-----------------|------------|----------|
| 50 | 50 | 3 | 3 |
| 99 | 99 | 2 | 2 |
| 100 | **10** | **12** | 2 |
| 200 | **10** | **12** | 2 |

```
GET https://api.scholexplorer.openaire.eu/v3/Links?sourcePid=10.1016/j.respol.2021.104226&size=100
→ 200 {"currentPage":0,"totalLinks":118,"totalPages":12,"result":[...10 items...]}
```

**Reproduction:** `curl "https://api.scholexplorer.openaire.eu/v3/Links?sourcePid=10.1016/j.respol.2021.104226&size=100"`

**Effective maximum:** 99

---

### BUG-O3: Research products sortBy error message omits `popularity`

**Endpoint:** `GET /v1/researchProducts` (also affects `/v2/researchProducts`)

When providing an invalid `sortBy` value, the error message lists valid fields as:

> *'relevance', 'publicationDate', 'dateOfCollection', 'influence', 'citationCount', 'impulse'*

But `popularity` is also a valid sort field (confirmed working with `sortBy=popularity DESC`). The error message is missing `popularity`, which makes it appear invalid when users encounter it via the error message.

```
GET /graph/v1/researchProducts?sortBy=invalid+DESC&pageSize=1
→ 400 {"message":"...research products can be only sorted by the 'relevance', 'publicationDate', 'dateOfCollection', 'influence', 'citationCount', 'impulse'."}
```

Note: The OpenAPI spec correctly includes `popularity` in the regex pattern. Only the error message is wrong.

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/researchProducts?sortBy=invalid+DESC&pageSize=1"`

---

### BUG-O4: Data sources sortBy error message says "organizations"

**Endpoint:** `GET /v1/dataSources`

When providing an invalid `sortBy` value, the error message reads:

> *"organizations can be only sorted by the 'relevance'"*

This is the data sources endpoint, not organizations. Copy-paste error in the error message.

```
GET /graph/v1/dataSources?sortBy=invalid+DESC&pageSize=1
→ 400 {"message":"...organizations can be only sorted by the 'relevance'."}
```

**Reproduction:** `curl -H "Authorization: Bearer $TOKEN" "https://api.openaire.eu/graph/v1/dataSources?sortBy=invalid+DESC&pageSize=1"`

---

### BUG-O5: Scholix Publisher `IDURL` field is consistently `null`

**Endpoint:** `GET /v3/Links` (Scholexplorer)  
**Field:** `source.Publisher[].identifier[].IDURL` and `target.Publisher[].identifier[].IDURL`

The OpenAPI spec describes `IDURL` as *"An internet resolvable form of the identifier"*. In practice, **all** Publisher identifier `IDURL` values are `null`. Source and target entity identifiers have valid URLs — only Publisher identifiers are affected.

Test result from 100 links (sourcePid=10.1016/j.respol.2021.104226):
- Source entity `IDURL`: 85/85 non-null
- Target entity `IDURL`: 34/34 non-null
- **Publisher `IDURL`: 0/58 non-null (all null)**

Example:
```json
{
  "name": "Research Policy",
  "identifier": [{
    "ID": "10|issn___print::a22009529648a2b4127d366f747e0391",
    "IDScheme": "OpenAIRE Identifier",
    "IDURL": null
  }]
}
```

---

### BUG-O6: Scholix Creator `identifier` field is consistently empty

**Endpoint:** `GET /v3/Links` (Scholexplorer)  
**Field:** `source.Creator[].identifier` and `target.Creator[].identifier`

The OpenAPI spec describes Creator.identifier as *"A List of unique string that identifies the creator"*. In practice, **94% of creators** have empty identifier arrays.

Test result from 10 links: 34/36 creator identifier arrays were empty `[]`.

---

### BUG-O7: Links endpoint uses different response header format

**Endpoints:** `GET /v1/researchProducts/links` vs all other Graph API endpoints

The links endpoint returns a **completely different header structure** from other Graph API endpoints:

| Field | Regular endpoints | Links endpoint | Scholix |
|-------|------------------|----------------|---------|
| `numFound` | ✅ | ❌ | ❌ |
| `maxScore` | ✅ | ❌ | ❌ |
| `queryTime` | ✅ | ❌ | ❌ |
| `page` | ✅ (1-indexed) | ✅ (0-indexed) | ✅ (as `currentPage`, 0-indexed) |
| `pageSize` | ✅ | ❌ | ❌ |
| `totalPages` | ❌ | ✅ | ✅ |
| `totalLinks` | ❌ | ✅ | ✅ |
| `nextCursor` | ✅ (with cursor param) | ❌ | ❌ |

The links endpoint also lacks cursor-based pagination support, despite being a Graph API endpoint.

---

### BUG-O8: Page indexing is inconsistent between endpoints

**Affected endpoints:** All Graph API endpoints

- **Regular Graph API** (`/v1/researchProducts`, `/v1/projects`, etc.): **1-indexed** (`page=1` is the first page, `page=0` returns 400)
- **Links endpoint** (`/v1/researchProducts/links`): **0-indexed** (`page=0` is the first page)
- **Scholix** (`/v3/Links`): **0-indexed** (`page=0` is the first page)

This is particularly confusing because the links endpoint is a Graph API v1 endpoint but uses different indexing than other v1 endpoints.

---

### BUG-O9: Links endpoint default `pageSize` is 10, not 100 as spec claims

**Endpoint:** `GET /v1/researchProducts/links`  
**Spec says:** `"default": 100`  
**Actual:** Default is 10

```
GET /graph/v1/researchProducts/links?sourcePid=10.1016/j.respol.2021.104226&page=0
→ 200 {"header":{"page":0,"totalPages":12,...},"results":[...10 items...]}
```

With 118 total links and `totalPages=12`, the effective page size is 10 (118/12 ≈ 10). The spec claims the default is 100, which would produce `totalPages=2`.

---

## Summary Table

| ID | Severity | Category | Endpoint | Issue |
|----|----------|----------|----------|-------|
| BUG-S1 | **Critical** | Server Error | `/v1/persons` | `givenName` filter → 500 |
| BUG-S2 | **Critical** | Server Error | `/v1/persons` | `lastName` filter → 500 |
| BUG-D1 | High | Wrong Docs | All entities | `debugQuery` documented but doesn't exist |
| BUG-D2 | Medium | Missing Docs | Research products | `rorId` works but not documented |
| BUG-D3 | Medium | Missing Docs | All entities | `logicalOperator` works but not documented |
| BUG-D4 | High | Missing Docs | Persons | No filtering docs (404) |
| BUG-D5 | High | Missing Docs | Links | Entire endpoint undocumented |
| BUG-D6 | Low | Wrong Docs | Data sources | `legalShortName` description says "organization" |
| BUG-D7 | Low | Wrong Docs | Scholix spec | Title typo "ScholeExplorer", desc typo "TThe" |
| BUG-D8 | Low | Wrong Docs | Scholix spec | `page` marked required but optional |
| BUG-D9 | Low | Wrong Docs | Data sources spec | sortBy description says "organizations" |
| BUG-D10 | High | Wrong Docs | Persons spec | `sortBy` includes non-functional `startDate`/`endDate` |
| BUG-D11 | Medium | Missing Docs | V2 API | V2 not documented as separate version |
| BUG-O1 | **Critical** | Behavior | `/v1/.../links` | `pageSize=100` silently returns 10 |
| BUG-O2 | **Critical** | Behavior | Scholix | `size=100` silently returns 10 |
| BUG-O3 | Medium | Behavior | Research products | Error message omits `popularity` sort field |
| BUG-O4 | Low | Behavior | Data sources | Error message says "organizations" |
| BUG-O5 | Medium | Data Quality | Scholix | Publisher `IDURL` always null |
| BUG-O6 | Medium | Data Quality | Scholix | Creator `identifier` always empty |
| BUG-O7 | Medium | Consistency | Links | Different response header format |
| BUG-O8 | High | Consistency | Graph API | Inconsistent page indexing (0 vs 1) |
| BUG-O9 | High | Behavior | Links | Default pageSize=10, spec says 100 |
