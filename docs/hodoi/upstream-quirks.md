# Upstream quirks

Findings from about 60 requests against the live DOI System proxy (doi.org) on 2026-11-27, from further requests on 2026-11-28 that checked the encoding of DOIs in the path, the handle filters, the redirect of a DOI, the redirect listing, and the full format matrix, and from the reference pages. Where a quirk affects hodoi, the behavior of the client is noted.

Reference pages used:

- DOI Foundation factsheet, [DOI Resolution Documentation](https://www.doi.org/the-identifier/resources/factsheets/doi-resolution-documentation) (proxy routes, `/ra/` and the REST API, response codes, query parameters).
- DOI Foundation, [DOI content negotiation](https://citation.doi.org/docs.html) (format matrix, response codes, redirect behavior).
- Crossref, [Content negotiation](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/).

## The `/ra/` lookup

- The answer is a JSON list with one `{DOI, RA}` object per requested DOI, even for a single DOI. The factsheet documents the route as `https://doi.org/doiRA/`; `/ra/` answers identically, and both were verified. hodoi uses `/ra/`.
- Every answer has HTTP 200. A known DOI carries `RA`; an unknown DOI carries `status: "DOI does not exist"`, a malformed string `status: "Invalid DOI"`, and an unknown prefix `status: "Unknown"` (the last one from the factsheet; not exercised live). hodoi models both shapes in `AgencyAnswer` and raises nothing.
- Prefix-only strings work. `/ra/10.7334` answers `RA: "Crossref"`, and `/ra/10.3205` answers `RA: "DataCite"`.
- Comma-separated DOIs go into one path segment. Lists of 100, 150, and 200 short DOIs were accepted (entries echoed in request order, mixed known and unknown). A 500-DOI URL answered HTTP 414 with an HTML error page. The proxy decodes each DOI after it splits the path, so a literal comma separates two DOIs and `%2C` inside one DOI does not. hodoi chunks at 100 DOIs and at 4000 path characters; the path limit of the proxy is not documented.
- `?pretty=true` answers the same JSON indented (verified 2026-11-28). hodoi does not send it.
- Agency names observed live: `Crossref`, `DataCite`, `mEDRA` (the mEDRA DOI 10.1400/56174 was found by probing known mEDRA prefixes).

## Encoding in the path

- The proxy percent-decodes the path before it matches the DOI (verified 2026-11-28). A DOI whose suffix has `<`, `>`, `;`, `(`, `)`, `#`, `?`, or a space resolves when those characters are percent-encoded, and a non-ASCII suffix travels as percent-encoded UTF-8. hodoi sends every DOI percent-encoded through `doi_path()`, and it decodes a DOI URL before it encodes the DOI again.

## Content negotiation

- A metadata request (any `Accept` except `text/html`) answers 302 with a small HTML body titled "Handle Redirect" whose only link is the data server of the agency. The link is `https://api.crossref.org/v1/works/{urlencoded doi}/transform` for Crossref, `https://data.crosscite.org/{urlencoded doi}` for DataCite, and `https://data.medra.org/{urlencoded doi}` for mEDRA. hodoi's `content()` follows this redirect; `raw()` returns the 302 body itself unless redirects are on.
- Without an `Accept` header, with `text/html`, or with `Accept: */*` (verified 2026-11-28), the 302 points at the publisher landing page instead. The redirect body is the same small HTML page. An unknown DOI answers 404 with an HTML page. hodoi's `resolve()` sends `Accept: text/html` and returns the 302.
- `HEAD` behaves like `GET` at the resolver. It answers 302 with the same `Location` header and no body, for both metadata and landing-page requests.
- The full format matrix was checked on 2026-11-28 with one DOI of each agency. The table of the DOI Foundation page differs for RIS, which mEDRA serves, and for RDF XML and Turtle, which DataCite does not serve. hodoi follows the live answers in `AGENCY_SUPPORT`.

| Agency | HTTP 200 | Other answers |
|---|---|---|
| Crossref (10.1038/nature12373) | CSL JSON, Unixref XML, Unixsd XML, BibTeX, RIS, `text/x-bibliography`, RDF XML, Turtle | 406 with a `text/plain` body (`No acceptable resource available.`) for DataCite JSON, DataCite XML, schema.org JSON-LD, and ONIX for DOI |
| DataCite (10.5281/zenodo.1238808) | CSL JSON, DataCite JSON, DataCite XML, schema.org JSON-LD, BibTeX, RIS, `text/x-bibliography` | 406 with an `application/json` body for Unixref XML, Unixsd XML, ONIX for DOI, and Turtle; 422 with a `text/plain` body (`The request could not be processed.`) for RDF XML |
| mEDRA (10.1400/56174) | CSL JSON, ONIX for DOI, BibTeX, RIS, `text/x-bibliography`, RDF XML, Turtle | 406 with an HTML error page from the mEDRA server for every other type |

- The content types carry parameters (`; charset=utf-8` or `charset=UTF-8`). hodoi reads the media type from the `Accept` header it sent, not from the content type of the answer.
- Crossref BibTeX answers start with a leading space (` @article{...}`). hodoi returns the text unchanged; strip before parsing.
- Content negotiation returns one record at a time; there is no batch form.
- An HTTP 204 answer was not observed live on either day. hodoi returns `None` for it.

## The Handle REST API

- `GET /api/handles/{doi}` answers `{responseCode, handle, values}` with HTTP 200. Values carry `index`, `type`, `data` (`{format, value}`), `ttl` (seconds, here always 86400), and an ISO 8601 `timestamp`. Types seen: `URL` (index 1), `HS_ADMIN` (index 100 or 700050-adjacent), and a numeric type `700050`.
- `HS_ADMIN` data is `{"format": "admin", "value": {"handle": "0.na/10.1038", "index": 200, "permissions": "111111110010"}}` on Crossref and `{"handle": "10.admin/codata", "index": 300}` on the DataCite record. hodoi parses it into `HandleAdminValue`.
- `?type=URL` and `?index=1` each restrict the values (verified; both returned only the URL entry). Repeated parameters work (verified 2026-11-28: `type=URL&type=HS_ADMIN` returned both entries). `?cert=true` answered the same record with HTTP 200 (verified 2026-11-28). `?recursive=true` was accepted and returned the full record; the factsheet does not list it. The factsheet also documents `auth` and a `callback` JSONP parameter. hodoi sends `type`, `index`, `auth`, and `cert`.
- Unknown prefix: HTTP 404 with `{"responseCode": 100, "message": "HandleException (SERVICE_NOT_FOUND) ...", "handle": ...}`. A malformed handle string (`/api/handles/nonsense`): HTTP 404 with `{"responseCode": 100, "handle": "nonsense"}` and no message. hodoi raises `NotFoundError` on both; `normalize_doi()` rejects malformed strings client-side for `handle()`.
- Response code 200 (values not found) answers HTTP 200 with `{"responseCode": 200, "handle": ..., "values": []}` (verified 2026-11-28 with `?type=NOPE`). hodoi returns the record with an empty `values` list.
- `?pretty=true` answers the same JSON indented (verified 2026-11-28). hodoi does not send it.

## The redirect of a DOI

- `GET https://doi.org/{doi}` with `Accept: text/html` answers 302 to the landing page, with the "Handle Redirect" HTML body. hodoi's `resolve()` returns that response.

## The redirect listing

- `GET https://doi.org/{doi}?action=showurls` answers HTTP 200 and `text/xml` (verified 2026-11-28). The body is a `<locations>` element with one `<location>` element for every URL the proxy could redirect to. The landing page carries `mode="legacy"`, `weight="1.0"`, and `href`. The data server of the agency carries `weight="0"`, `http_role="conneg"`, `href`, and a `href_template`, in which `{hdl}` stands for the DOI. hodoi's `locations()` parses the listing into `RedirectLocation` models and keeps every attribute.
- The demo DOI 10.1000/202 lists only its landing page, with no entry for a data server. An unknown DOI answers 404 with an HTML page.
- `?noredirect` answers an HTML page that shows the DOI name and its values. It is a web page and not an API, so hodoi leaves it out.

## Politeness and limits

- doi.org publishes no rate limit. The factsheet asks only for the standard proxy etiquette; there is no `mailto` polite pool for doi.org itself (unlike Crossref). hodoi defaults to 2 requests per second and concurrency 2.
- The proxy caches handle values with a 24-hour TTL; a changed URL can be stale without `auth=True`.

## Quirks in the client's own tests

- The live mEDRA sample (10.1400/56174) has no `RA` change; its landing redirect went to `digital.casalini.it`, not to a medra.org page. `landing_url()` reads the handle record, so it is unaffected.
- The DOI Foundation HTML handbook pages moved under `/doi-handbook/`; the old `/doi_handbook/3_Resolution.html` URL now redirects to a landing page. The content-negotiation factsheet at `citation.doi.org/docs.html` is the stable format matrix.
