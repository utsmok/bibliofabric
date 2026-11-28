# Upstream quirks

Findings from about 80 requests against the live OpenCitations APIs on 2026-11-27 (about 45 by an earlier probe, 23 in this study, and the live test runs), with the [Index API v2 documentation](https://opencitations.net/index/api/v2) (version 2.2.0, 2025-04-15) and the [Meta API v1 documentation](https://opencitations.net/meta/api/v1) (version 1.1.1, 2022-12-22) as the reference. Where a quirk affects opcitato, the behavior of the client is noted.

## Limits and access

- Both APIs document a rate limit of 180 requests per minute per IP address (3 per second). No rate-limit headers are sent, so the limit cannot be read from responses; the client paces at 3 requests per second by default.
- Higher limits need an OpenCitations Access Token in an `authorization` header. The client does not manage tokens; send one through `default_headers` once credentials exist.
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

## Values that differ from the documentation

- The count operations answer `[{"count": "57"}]`: the count travels as a string although the documentation types the field as int. The `Count` model coerces it.
- `journal_sc` and `author_sc` are `"yes"`/`"no"` strings.
- `creation` dates can be partial (`2013`, `2013-07`); `timespan` can be negative (`-P1Y1M16D`).
- The documentation claims that values are prefixed with `[index name] =>` when data comes from several indexes; no such prefix appeared in any live payload on 2026-11-27. The models store the values as they arrive.

## Unknown identifiers and errors

- An unknown id is not an error. Row operations answer 200 with `[]`, and so do the count operations; the client reads `[]` from a count route as `None`.
- Rejected parameters answer 400 with a `text/plain` body, not JSON. The framework raises `APIError` for any status of 400 or above, before parsing the body.

## Routes that do not exist

The Index operations `/metadata/{id}`, `/citation-count-and-year/{id}`, `/citations-with-context/{id}`, and source-scoped `/index/v2/{source}/citations/{id}` answered 404 on `api.opencitations.net` on 2026-11-27 and appear in neither API's documentation; the six documented Index operations and the three documented Meta operations are the complete surface. The Meta routes `related`, `citation`, `journal`, `publisher`, `identifier`, `amount`, and `concept` also answered 404 and are not documented.
