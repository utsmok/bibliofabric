# Deferred work

This page lists everything that Wave 1 left out, with the reason and the condition that unblocks it. An item leaves this page only when it is done.

## Core framework

Wave 1 needed two of the six planned core additions. `BaseApiClient.default_headers` sends per-client headers such as an `Accept` type, and `JsonApiUnwrapper` reads JSON:API envelopes. `bibliofabric.ids` gained normalizers for ISBN, ISNI, Wikidata, GND, and VIAF. The rest stays open.

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| RFC 5988 `Link` header parser for paging | No Wave 1 read route pages through headers only. DOAJ and Zenodo carry their page links in the response body. | A Wave 2 client that pages through headers, such as Software Heritage, OSF, or GLEIF. |
| POST-body search dialect | Every Wave 1 read route works with `GET`. The Semantic Scholar batch routes are `POST` requests that only read, and its client sends them directly. | NIH RePORTER, Figshare, CORE, or SPARQL endpoints with a `POST` interface. |
| Window limiter and daily quota hooks | No Wave 1 API enforces a window or daily quota that the per-second limiter cannot respect. | LoC, GLEIF, or NASA ADS, which ban or throttle by minute or by day. |
| Pluggable non-JSON decoder | The DOI client returns XML and BibTeX representations as text and parses the JSON ones. | arXiv Atom, PubMed `efetch`, SRU, or a generic OAI-PMH harvester. |
| Identifier normalizers for LEI, ARK, RAiD, SWHID, and SPDX | No Wave 1 payload carries these identifiers as first-class fields. | GLEIF LEI, arXiv, DataCite (RAiD), or Software Heritage clients. |

## Release

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| PyPI trusted publishers for the new names | PyPI registers a pending publisher only through its web interface, signed in as the owner. | Adding a pending publisher for each name, as described in [Wave 1 libraries](wave-1-libraries.md#release). |
| Release of the new libraries | They depend on `bibliofabric>=0.8`, which is not released. | Publishing `bibliofabric` 0.8.0 first, then `aireloom`, `aletheca`, and `stavrophora` with their new pins, then the new libraries. |

## Existing clients

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| `stavrophora`: Crossref Data Citation API (`/beta/datacitations/`) | The route is live but still in beta upstream. | Crossref declaring the route stable, or a decision to ship a beta client. |
| `stavrophora`: Retraction Watch helpers | The data is in the Crossref `updated-by` fields, which `stavrophora` already returns as fields on a work. | Typed helpers once the fusion layer defines what it needs. |

## ROR (`rorifer`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Client identification | ROR paused registration for client ids. The API needs no credentials and documents a limit of 2,000 requests per 5 minutes per IP address; the client paces itself to 6 requests per second. | ROR reopening registration. The client id then goes into `default_headers`. |
| Complete lists through the API | The API reaches at most 10,000 records per query and cannot OR two different filter keys. This is an upstream limit. | Nothing on our side. Use the data dumps, which the client reads. |
| Searching external ids that contain a quote, a backslash, or a colon | The query parser of ROR rejects such values. | An upstream change. Pass bare ids. |

## Zenodo (`zenotheca`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Write routes (deposits, drafts, file upload, publish, community management) | Wave 1 covers reads only. Anonymous requests answer 403, so there is no way to test a write. | An access token in `.env` and a decision to support writes. |
| Typed facet aggregations | Search answers `aggregations` with a different bucket shape per facet. The client returns them as plain dicts in `Page.meta`, so no data is lost. | A decision on which facets need typed models. |
| Typed models for OAI-PMH metadata schemas | The metadata element depends on the metadata prefix (eight prefixes on 2026-11-27). Each record carries the metadata as raw XML. | A decision on which prefixes need typed models. |
| Live check of the token settings | No Zenodo token exists. The `Authorization` header and the page size of 100 with a token are covered by offline tests only. | A Zenodo access token in `.env`. |

## DataCite (`dataphora`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| DOI writes (create, update, delete, publish) and media mutations | Wave 1 covers reads only. The write routes belong to the MDS API and need repository credentials. | A DataCite repository account and a decision to support writes. |
| Read routes `media`, `url`, `views`, and `downloads` under `/dois/{id}` | They answer 404 without a login (verified 2026-11-27). | A DataCite account. The client then sends its credentials. |
| Usage Reports API and API-key management | Both need a login, and no account exists. | A DataCite account. |
| GraphQL mutations | Queries are public and wrapped. Mutations need a bearer token, and none exists. | A DataCite account and a decision to support writes. |

## OpenCitations (`opcitato`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Access Token in the `authorization` header | No token exists to test, and both APIs answer without one. The token is free, counts unique users, and does not change the limit. A caller can send one through a prepared `httpx.AsyncClient`, which an offline test covers. | A token from OpenCitations, then an optional setting and a live check. |
| `json=array(...)` and `json=dict(...)` row transformations | The plain rows carry every field. These parameters only reshape a row. | A caller that needs the reshaped rows. |
| Database dumps at `download.opencitations.net` | The dumps are many gigabytes and serve bulk harvest, not lookups. | A decision to ship a dump loader, as the ROR client has. |
| Legacy Index API v1 (`/index/v1/...`) | It is the predecessor of v2. Its rows carry bare DOIs and a subset of the v2 fields, and it still answers 200 (verified 2026-11-28). | A caller that needs a field only v1 returns. |
| OCI Resolver (`oci.opencitations.net`) | It is a web page that returns information about one citation for any OCI. `index.citation()` covers the citations of the Index. | A caller that must resolve the OCIs of other datasets. |

## DOI (`hodoi`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Resolver parameters `noredirect`, `urlappend`, `locatt`, `ignore_aliases`, and `nols` | `noredirect` answers an HTML page, not an API (verified 2026-11-28). The other four reshape the redirect for multiple-resolution links. `locations()` lists the redirect targets, and `handle()` returns the record that holds them. | A caller that needs the reshaped redirect. |
| Handle API parameters `callback` and `recursive` | `callback` asks for a JSONP body, which no Python client needs. `recursive` is not in the factsheet, and the proxy accepted it without changing the answer (verified 2026-11-27). | A decision to expose them. |
| `?pretty=true` on `/ra/` and on the Handle API | It only indents the JSON (verified 2026-11-28). | A caller that reads the raw JSON text. |
| Content negotiation for EIDR, JaLC, and OP | These agencies answer `/ra/`, but no sample DOI was exercised, so `AGENCY_SUPPORT` does not list them. | A sample DOI from each agency and a few live requests. |

## Semantic Scholar (`scholiast`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Live check of the keyed paths | The API key on hand answers HTTP 403. | A new key, then one live run with `SCHOLIAST_API_KEY` set. |
| Live check of `/paper/search`, `/snippet/search`, and the `URL:` id form | The anonymous pool answered 429 for these three on 2026-11-27 and 2026-11-28. The client wraps them from the published specification. `/paper/search/match`, `/paper/autocomplete`, `/patent/search`, the recommendations, and the release listing passed a live check without a key on 2026-11-28. | A key, or a quiet hour on the anonymous pool. |
| Dataset file downloads and diffs | The file listing answers 401 without a key. A download is a plain HTTP GET of a pre-signed URL. | A key, then a decision to wrap the download. |
| Live check of the paper fields `openAccessDoi` and `embedding` and the author fields `normalizedAffiliations` and `aliases` | They answer 400 without a key. The models carry the fields. | A key with access to those fields. |

## ORCID (`orchis`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Member API on `api.orcid.org` | The token and the client credentials on hand are public API credentials: the member API answered 403 for both on 2026-11-28. The member read routes have the same paths as the public ones. | ORCID member credentials, then a base URL setting and a live run. |
| Token minting (`POST https://orcid.org/oauth/token` with `ORCHIS_CLIENT_ID` and `ORCHIS_CLIENT_SECRET`) | The client sends a token from `ORCHIS_ACCESS_TOKEN`, and that path passed a live check on 2026-11-28 with a token minted from the client credentials (scope `/read-public`). The token lifts the daily read quota from 25,000 to 100,000. Minting is an OAuth call that stays outside the client. | A decision on whether the client should mint and cache tokens itself. |
| Write routes (`POST`, `PUT`, and `DELETE` on record sections) | They need a member token and are out of scope for this wave. | A member token. |
| `application/ld+json` representations | The API answers 406 for that media type. | The API serving JSON-LD. |
| The `/{orcid}/invited-to-peer-review` route | The activities summary lists peer reviews under `peer-reviews`, which the client wraps. | A decision on whether the standalone route adds anything. |
| Download of the public data file | The 2025 edition is a 17.4 GB archive of XML files. | A decision to ship a bulk loader, as the ROR client has. |

## Europe PMC (`europaea`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| `format=xml` and `format=dc` on the search, and `format=xml` on the per-article routes | The client requests `format=json`. The other formats return the same records in XML or Dublin Core. | A caller that needs those formats, then typed wrappers for them. |
| Typed parsing of the JATS full text and the book XML | The XML routes return the document as text in `XmlDocument`. | A decision on which JATS elements need models. |
| The `/preprint/{source}/{id}` routes of older documentation | The service answers 404 for all of them (verified 2026-11-27). A preprint record is available through `/article/PPR/{id}` and the `SRC:PPR` search, which the client wraps. | The service adding the routes. |
| Bulk downloads of the full-text corpus and the supplementary files | They are archives for bulk harvest, not REST routes. | A decision to ship a bulk loader. |
| Annotation writes on the annotations API | Wave 1 covers reads only. They need an OAuth token. | An account and a decision to support writes. |

## Wikidata (`quiddita`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Action API write modules (`wbeditentity`, `wbsetlabel`, `wbsetdescription`, `wbsetaliases`, `wbsetclaim`, `wbremoveclaims`, `wbsetreference`, `wbmergeitems`, `wbcreateredirect`, `wblinktitles`, and the lexeme `wbl*` writes) | Wave 1 covers reads only. They need a bot account. | An account and a decision to support writes. |
| REST write methods (`POST`, `PUT`, `PATCH`, and `DELETE` on items, properties, lexemes, forms, senses, and statements) | Wave 1 covers reads only. They need a bot account. | An account and a decision to support writes. |
| Batches above 50 ids on `wbgetentities` | The API answers `toomanyvalues` above 50 ids, and the client chunks at 50. | The higher limit needs an approved bot flag. |
| Several entities per `Special:EntityData` request | The route serves one entity per request. | The service adding a multi-id JSON route. |
| Per-form and per-sense REST routes | The lexeme REST API has no route for a single form or sense (404 on 2026-11-28). The lexeme payload carries its forms and senses. | The lexeme REST API adding the routes. |
| SPARQL UPDATE | The query service is read-only. | Nothing on our side. The service has no update endpoint. |
| Linked-data endpoint of the query service (`/bigdata/ld/...`) | The endpoint is gone (404 on 2026-11-28). | Nothing on our side. |

## DOAJ (`diurnalia`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| Applications search (`GET /api/v4/search/applications/{query}`) | The route answers 401 without an admin key (verified 2026-11-27). | A DOAJ admin key in `.env`. |
| Write routes (`POST /api/articles`, `PUT` and `DELETE` on `/api/articles/{id}` and `/api/journals/{id}`, `POST /api/applications`, and `GET`, `PUT`, `DELETE` on `/api/applications/{id}`) | Wave 1 covers reads only. They need an admin key. | A DOAJ admin key and a decision to support writes. |
| Bulk upload routes (`POST` and `DELETE` on `/api/bulk/articles`, `GET /api/bulk/articles/{upload_id}`, and `POST` and `DELETE` on `/api/bulk/applications`) | They manage article uploads by publishers and need a publisher key. | A DOAJ publisher account. |
| Download of the public data dump | The dump holds every journal and article and serves bulk harvest, not lookups. | A decision to ship a dump loader, as the ROR client has. |

## ISSN Portal (`seriatim`)

| Item | Why it is deferred | Unblocked by |
|---|---|---|
| SRU Search API | It is a paid service. `/sru` answers 404 without an account. | A subscription and its API key. |
| OAI-PMH access | It is a paid service. `/oai` and `oai.issn.org` answer 404 without an account. | A subscription. |
| ISSN-H families (`/resource/ISSN-H/{issn}`) | The page says they are reserved to subscribers (verified 2026-11-28). | A subscription. |
| Download of the ISSN-L Table (`/public/issnltables.zip`, about 25 MB) | It is a bulk file. | A decision to ship a loader for it. |
| `/ltwa-export` CSV export | The route answers 502 with the page parameters (2026-11-27 and 2026-11-28). The HTML table is wrapped. | The portal serving the export again. |
| Search export and browse (`/internal/search/export`, `/internal/browse`) | Both answer 404 without a session. | A full-access account. |
| ROAD record views and `publishers.issn.org` | They answer HTML only and add no machine-readable read route. | The ISSN Centre publishing machine-readable answers for them. |
