# Upstream quirks

Findings from about 60 requests against the live DOI System proxy (doi.org) on 2026-11-27, plus the reference pages. Where a quirk affects hodoi, the behavior of the client is noted.

Reference pages used:

- DOI Foundation factsheet, [DOI Resolution Documentation](https://www.doi.org/the-identifier/resources/factsheets/doi-resolution-documentation) (proxy routes, `/ra/` and the REST API, response codes, query parameters).
- DOI Foundation, [DOI content negotiation](https://citation.doi.org/docs.html) (format matrix, response codes, redirect behavior).
- Crossref, [Content negotiation](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/).

## The `/ra/` lookup

- The answer is a JSON list with one `{DOI, RA}` object per requested DOI, even for a single DOI. The factsheet documents the route as `https://doi.org/doiRA/`; `/ra/` answers identically, and both were verified. hodoi uses `/ra/`.
- Every answer has HTTP 200. A known DOI carries `RA`; an unknown DOI carries `status: "DOI does not exist"`, a malformed string `status: "Invalid DOI"`, and an unknown prefix `status: "Unknown"` (the last one from the factsheet; not exercised live). hodoi models both shapes in `AgencyAnswer` and raises nothing.
- Prefix-only strings work: `/ra/10.7334` answers `RA: "Crossref"`, `/ra/10.3205` answers `RA: "DataCite"`.
- Comma-separated DOIs go into one path segment. Lists of 100, 150, and 200 short DOIs were accepted (entries echoed in request order, mixed known and unknown). A 500-DOI URL answered HTTP 414 with an HTML error page. hodoi chunks at 100.
- Agency names observed live: `Crossref`, `DataCite`, `mEDRA` (the mEDRA DOI 10.1400/56174 was found by probing known mEDRA prefixes).

## Content negotiation

- A metadata request (any `Accept` except `text/html`) answers 302 with a small HTML body titled "Handle Redirect" whose only link is the agency data server: `https://api.crossref.org/v1/works/{urlencoded doi}/transform` for Crossref, `https://data.crosscite.org/{urlencoded doi}` for DataCite. hodoi's `content()` follows this redirect; `raw()` returns the 302 body itself unless `follow_redirects=True`.
- Without an `Accept` header (or with `text/html`), the 302 points at the publisher landing page instead. The redirect body is the same small HTML page.
- `HEAD` behaves like `GET` at the resolver: it answers 302 with the same `Location` header and no body, for both metadata and landing-page requests.
- Crossref DOI (10.1038/nature12373) verified: CSL JSON 200, Unixref XML 200, BibTeX 200, RIS 200, schema.org JSON-LD 406 (`No acceptable resource available.`), DataCite JSON 406.
- DataCite DOI (10.5281/zenodo.1238808) verified: CSL JSON 200, DataCite JSON 200, schema.org JSON-LD 200, BibTeX 200, RIS 200.
- mEDRA DOI (10.1400/56174) verified: CSL JSON 200, BibTeX 200, RIS 200; schema.org JSON-LD and Unixref XML 406 with an HTML error body from the mEDRA server.
- Crossref BibTeX answers start with a leading space (` @article{...}`). hodoi returns the text unchanged; strip before parsing.
- Content negotiation returns one record at a time; there is no batch form.
- The mEDRA redirect goes to the mEDRA server directly (`406` answers come from its Tomcat); Crossref redirects again to `api.crossref.org`, DataCite to `data.crosscite.org`.

## The Handle REST API

- `GET /api/handles/{doi}` answers `{responseCode, handle, values}` with HTTP 200. Values carry `index`, `type`, `data` (`{format, value}`), `ttl` (seconds, here always 86400), and an ISO 8601 `timestamp`. Types seen: `URL` (index 1), `HS_ADMIN` (index 100 or 700050-adjacent), and a numeric type `700050`.
- `HS_ADMIN` data is `{"format": "admin", "value": {"handle": "0.na/10.1038", "index": 200, "permissions": "111111110010"}}` on Crossref and `{"handle": "10.admin/codata", "index": 300}` on the DataCite record. hodoi parses it into `HandleAdminValue`.
- `?type=URL` and `?index=1` each restrict the values (verified; both returned only the URL entry). `?recursive=true` was accepted and returned the full record. The factsheet documents repeated `type` and `index` parameters, `auth`, `cert`, and a `callback` JSONP parameter. hodoi sends `type`, `index`, and `auth` only.
- Unknown prefix: HTTP 404 with `{"responseCode": 100, "message": "HandleException (SERVICE_NOT_FOUND) ...", "handle": ...}`. A malformed handle string (`/api/handles/nonsense`): HTTP 404 with `{"responseCode": 100, "handle": "nonsense"}` and no message. hodoi raises `NotFoundError` on both; `normalize_doi()` rejects malformed strings client-side for `handle()`.
- Response code 200 (values not found) is documented as HTTP 200 with no `values`; not exercised live.

## Politeness and limits

- doi.org publishes no rate limit. The factsheet asks only for the standard proxy etiquette; there is no `mailto` polite pool for doi.org itself (unlike Crossref). hodoi defaults to 2 requests per second and concurrency 2.
- The proxy caches handle values with a 24-hour TTL; a changed URL can be stale without `auth=True`.

## Quirks in the client's own tests

- The live mEDRA sample (10.1400/56174) has no `RA` change; its landing redirect went to `digital.casalini.it`, not to a medra.org page. `landing_url()` reads the handle record, so it is unaffected.
- The DOI Foundation HTML handbook pages moved under `/doi-handbook/`; the old `/doi_handbook/3_Resolution.html` URL now redirects to a landing page. The content-negotiation factsheet at `citation.doi.org/docs.html` is the stable format matrix.
