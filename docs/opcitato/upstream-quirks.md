# Upstream quirks

Findings from about 80 requests against the live OpenCitations APIs on 2026-11-27 (about 45 by an earlier probe, 23 in this study, and the live test runs), and from further requests on 2026-11-28 that checked the count routes for unknown ids, the encoding of ids in the path, and the two SPARQL endpoints. The reference is the [Index API v2 documentation](https://opencitations.net/index/api/v2) (version 2.2.0, 2025-04-15) and the [Meta API v1 documentation](https://opencitations.net/meta/api/v1) (version 1.1.1, 2022-12-22). Where a quirk affects opcitato, the behavior of the client is noted.

## Limits and access

- Both APIs document a rate limit of 180 requests per minute per IP address (3 per second). No rate-limit headers are sent, so the limit cannot be read from responses; the client paces at 3 requests per second by default.
- Both API documentations ask applications to send an [OpenCitations Access Token](https://opencitations.net/accesstoken) in the `authorization` header. The token is free, optional, and lets OpenCitations count unique users. Neither documentation ties it to a higher limit. The client sends no token and manages none; a caller can pass a prepared `httpx.AsyncClient` that carries the header (verified offline).
- `https://opencitations.net/index/v2/...` (without the `api.` host) answers 403. The canonical host is `https://api.opencitations.net`, which is the client default. The Retrieval API routes (`https://opencitations.net/index/api/v2/citations/...`) answer 200 on the www host but are a different, undocumented service; the client does not use them.

## The result is the whole list

- No operation pages. Every request returns the complete result of the query; one response can reach hundreds of kilobytes (a 658 KB response was cut off once by the network and httpx raised `RemoteProtocolError`; the framework retries network errors).
- `require`, `filter`, `sort`, `format`, and `json` are server-side row operations that every operation accepts. The verified behavior: `require=creation` dropped one of 57 rows (the one with an empty creation date), `filter=creation:>2019-12` kept 15 of 57, and `sort=desc(creation)` ordered by the string date, so partial dates (`2020`, `2020-03`) sort before full dates within the same year.
- `format=csv` works as a query parameter. An `Accept: text/csv` header alone does not change the representation; the `format` parameter has priority over the header. The CSV header repeats the JSON field names, so `format="csv"` parses into the same models.
- The `json=array(...)`/`json=dict(...)` row transformations are documented but not exposed by the client.

## Identifier handling

- Index path ids must carry a scheme prefix. The documented shape is `(omid|doi|pmid|issn|isbn):(.+)`. A bare DOI and an `openalex:` id answer 400 with a plain-text body such as `HTTP status code 400: the value '10.1108/jd-12-2013-0166' is not valid for parameter 'id' in operation '/index/v2/citations/{id}'. Example: /index/v2/citations/doi:10.1108/jd-12-2013-0166`. The client rejects both shapes before a request is sent; a 400 that slips through raises `APIError`.
- Meta metadata accepts more schemes than the Index API: the documented shape also allows `openalex`, `pmid`, and `pmcid`, and `openalex:W2159974629` answered 200 with the Nature 12373 metadata (verified 2026-11-27).
- Several identifiers in one request are only a Meta feature. `/meta/v1/metadata/{a}__{b}` answered with one row per id (verified 2026-11-27). The Index operations document no multi-id form; `citations/doi:A__doi:B` answered `[]` even though both ids have citations, so the Index client sends one id per request.
- The `/citation/{oci}` operation wants the bare `first-second` numbers without the `oci:` prefix. The client strips an optional prefix.
- Citing and cited rows pack several schemes into one space-separated string. The live data carries `omid:`, `doi:`, `openalex:`, and `pmid:` (verified 2026-11-27).
- The server percent-decodes the path before it looks up the identifier. The SICI DOI `10.1002/(SICI)1097-4636(199823)43:3<338::AID-JBM16>3.0.CO;2-B` answered the same count when its parentheses, angle brackets, and semicolon arrived percent-encoded and when some of them arrived raw (verified 2026-11-28). httpx cuts a path at the first `#` or `?`, so the client percent-encodes every character of an identifier other than `/` and `:`.
- The Meta `/author/{id}` and `/editor/{id}` operations also accept an ORCID without the `orcid:` prefix, according to their documented shape. The client requires the prefix, as it does for every identifier.

## Values that differ from the documentation

- The count operations answer `[{"count": "57"}]`: the count travels as a string although the documentation types the field as int. The `Count` model coerces it.
- `journal_sc` and `author_sc` are `"yes"`/`"no"` strings.
- `creation` dates can be partial (`2013`, `2013-07`); `timespan` can be negative (`-P1Y1M16D`).
- The documentation claims that values are prefixed with `[index name] =>` when data comes from several indexes; no such prefix appeared in any live payload on 2026-11-27. The models store the values as they arrive.

## Unknown identifiers and errors

- An unknown id is not an error. Row operations answer 200 with `[]`. The count operations answered `[]` on 2026-11-27 and a zero row (`[{"count": "0"}]`) on 2026-11-28; the client returns `None` for the first answer and `0` for the second.
- Rejected parameters answer 400 with a `text/plain` body, not JSON. The framework raises `APIError` for any status of 400 or above, before parsing the body.

## Routes that do not exist

The Index operations `/metadata/{id}`, `/citation-count-and-year/{id}`, `/citations-with-context/{id}`, and source-scoped `/index/v2/{source}/citations/{id}` answered 404 on `api.opencitations.net` on 2026-11-27 and appear in neither API's documentation; the six documented Index operations and the three documented Meta operations are the complete surface. The Meta routes `related`, `citation`, `journal`, `publisher`, `identifier`, `amount`, and `concept` also answered 404 and are not documented.

## SPARQL endpoints

- Each dataset has a SPARQL endpoint: `https://sparql.opencitations.net/index` and `https://sparql.opencitations.net/meta`. The landing page at `https://sparql.opencitations.net/` lists both; the REST API documentations do not mention them.
- The endpoints answer SPARQL 1.1 Query Results XML unless the `Accept` header asks for another representation. `application/sparql-results+json` returns the JSON form with one addition: a `meta` member that carries `query-time-ms` and `result-size-total`. The `SparqlResult` model keeps it.
- `application/sparql-results+xml`, `text/csv`, `text/tab-separated-values`, `text/turtle`, and `application/n-triples` select the other representations. An `Accept` type the endpoint does not serve answers 406. A CONSTRUCT query that asks for `application/sparql-results+json` answers Turtle.
- A query travels in the `query` parameter of a GET request, in the form body of a POST request, or in an `application/sparql-query` body of a POST request. The client sends the `query` parameter by default and a form body for `method="POST"`.
- A malformed query answers 400 with a JSON body that carries an `exception` member. The framework raises `APIError` for the status.
- An ASK query answers `{"head": {}, "boolean": true}` with no `results` member.

## Index API v1

`https://api.opencitations.net/index/v1/citations/{doi}` still answers 200 (verified 2026-11-28). It takes a bare DOI and returns a subset of the v2 fields, with bare DOIs in `citing` and `cited` instead of the prefixed identifiers of v2. The client targets v2 only; the [deferred list](../roadmap/deferred.md) has the entry.
