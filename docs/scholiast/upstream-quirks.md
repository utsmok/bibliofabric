# Upstream quirks

Findings from 67 requests against the live Semantic Scholar APIs on
2026-11-27, with the [Academic Graph API reference](https://api.semanticscholar.org/api-docs/graph),
the [product page](https://www.semanticscholar.org/product/api), and the
published OpenAPI documents of the graph, recommendations, and datasets
services as the reference. Where a quirk affects scholiast, the
behavior of the client is noted.

## Rate limits and the anonymous pool

The published limits are 1000 requests per second shared among all
unauthenticated callers, and 1 request per second guaranteed for an API key
(the introductory tier). The shared pool is contended in practice. During
the study, keyless requests answered HTTP 429 at a steady 1 request per
second and stayed lossy even at 3 to 5 seconds between requests, while other
requests in the same window answered 200. The 429s are not proportional to
pacing; the pool throttles unevenly.

scholiast therefore defaults to 1 request per second with
concurrency 1, which works with and without a key. The live test suite sends
at most one request per second and skips with `pytest.skip("rate limited")`
on a 429 instead of failing, because the pool is shared and often exhausted.

## The API key on hand is inactive

The optional API key stored in the repository `.env` answered HTTP 403 on
2026-11-27 in two separate checks, with the key sent as `x-api-key`. The key
is probably no longer active. scholiast accepts any key and sends
it as the `x-api-key` header, so the setting needs no change once a new key
is issued. All live tests run without a key.

## Key-gated fields answer 400, not 401

`GET /paper/{id}?fields=openAccessDoi` keyless answers HTTP 400 with
`{"error": "Unrecognized or unsupported fields: [openAccessDoi]"}`. The
same happens for `embedding`, and on the author routes for
`normalizedAffiliations` and `aliases` (2026-11-28). The fields exist and
are documented; they are only served to keys with the right access.
scholiast models these fields and lets the API decide.

## Paper ids

- Every documented prefix answered 200 keyless on 2026-11-27: a bare S2
  paper id, `DOI:`, `ARXIV:`, `PMID:`, `MAG:`, `ACL:`, and `CorpusId:`.
- `URL:` needs percent-encoding of the whole value
  (`URL:https%3A%2F%2Fdoi.org%2F...`); it answered 429 in the study window,
  so the encoded form is implemented per the API docs but its 200 was not
  observed.
- `PMCID:PMC4221854` answered 404 twice even though the same paper's
  `externalIds` lists that PubMedCentral id. `PubMedCentral:` was not
  verifiable for the same reason. scholiast passes all id forms
  through unchanged; the API decides what it accepts.
- Unknown ids answer HTTP 404 with `{"error": "Paper with id ... not
  found"}`, which the client maps to `NotFoundError`.

## Batch routes answer a bare array

`POST /paper/batch` and `POST /author/batch` answer a JSON array, not an
envelope. Unknown ids hold the position with `null`. scholiast
reads the array (and tolerates an envelope for safety) and drops the null
entries. The `fields` parameter is a single-value query parameter, not part
of the POST body. Both POSTs are reads and are sent with retries
(`retry=True`).

Limits: 500 ids per paper batch call, 1000 ids per author batch call. The
client chunks automatically.

## Search paging

- `/paper/search` answers `{total, offset, next, data}` and caps
  `offset + limit` at 10,000, so one relevance query reaches at most
  10,000 records. The client sets `max_offset` to 9900.
- `/paper/search/bulk` answers `{total, token, data}` and returns up to
  1000 records per call (a `limit` above 1000 is rejected client-side).
  Continuation works: the opaque `token` was passed back and the next
  1000-record page came back with a fresh token on 2026-11-27. The last
  page answers `"token": null`, which ends `bulk_iterate()`.
- The relevance-search route stayed at 429 through the whole study window
  (10 attempts, without a key), so its envelope comes from the API
  documentation alone. No successful answer was captured for that route.

## Field selection

`fields` is a comma-joined single-value query parameter on every graph
route, including the batch POSTs (where it goes into the query string).
Without `fields`, a paper answers with `paperId` only (plus `title` and
`year` on some routes). `citationStyles` and `textAvailability` are
documented as objects; the models keep them permissive because their inner
shape varies.

## Other routes

- `GET /paper/{id}/citations` and `/references` answer
  `{data, next, offset}`; `/references` also carries `citingPaperInfo`.
  The routes serve at most the most recent 10,000 citation and reference
  edges per paper (documented limit).
- `GET /paper/autocomplete` answers `{"matches": [...]}` with minimal
  records (`id`, `title`, `authorsYear`), not the `data` key the other
  routes use. The unwrapper reads both.
- `GET /paper/search/match` answers `{"data": [record]}` where the record
  is the paper itself with `matchScore` beside it.
- `GET /author/search` answers `{total, offset, next, data}`.
- `GET /patent/{ucid}` answered 200 keyless. The detail record carries
  `claims` as one text and the party names (`assignees`, `applicants`,
  `inventors`) as lists of strings (2026-11-28).
- `GET /patent/outbound-citations/{paper_id}` answers
  `{total, offset, next, data}`. A paper that no patent cites answers
  HTTP 404, not an empty list, which the client raises as `NotFoundError`.
- `GET /snippet/search` is documented with a 1000 max limit; keyless it
  stayed at 429 in the study, so the client wraps it but the payload shape
  comes from the spec only.
- The recommendations routes live on their own base URL
  (`/recommendations/v1`). `GET /papers/forpaper/{id}` and
  `POST /papers/` both answered 200 keyless on 2026-11-27 and answer
  `{"recommendedPapers": [...]}`.
- The datasets routes also have their own base URL (`/datasets/v1`).
  `GET /release` answered a plain array of release id strings, and
  `GET /release/latest` answered `{release_id, datasets: [...]}` (11
  datasets on 2026-11-24). The old `/datasets/v1/datasets` route answers
  404; it is gone. `GET /release/latest/dataset/abstracts` answered HTTP
  401 keyless, so dataset file listings and diffs need an API key. The
  client sends the requests anyway and lets the API decide.

## Model field names

The datasets service uses snake_case (`release_id`, `from_release`,
`update_files`), unlike the graph service's camelCase
(`paperId`, `openAccessPdf`). The models keep the API's own names.
