# Upstream quirks

Findings from about 40 requests against the live Zenodo REST API on
2026-11-27, plus about 28 more against the vocabularies, subcommunities,
and OAI-PMH routes the same day, with the
[developers.zenodo.org documentation](https://developers.zenodo.org/)
as the reference. Where a quirk affects zenotheca, the behavior of the
client is noted.

## The served API is the legacy record schema

`GET /api/records` answers records in the legacy shape (`recid`,
`conceptrecid`, `conceptdoi`, `metadata`, `state`, `submitted`, `owners`,
`stats`, `swh`) even though several `links` values point at the newer
InvenioRDM routes (`versions`, `latest`, `parent`, `files`, `draft`). The
documentation links an OpenAPI schema that does not match either shape
completely, so the live API was treated as ground truth and the models use
`extra="allow"`.

## Rate limits differ per route (checked on 2026-11-28)

The documentation names no limit. The live API sends `x-ratelimit-limit` headers that split the routes in two groups for callers without a token:

- The record search (`/api/records`, with or without `q`) and the search over the records of one community (`/api/communities/{slug}/records`) allow 30 requests per minute. The 31st request answers 429 with `{"message": "30 per 1 minute"}` and a `Retry-After` header of the seconds until the window resets.
- Every other route allows 133 per minute: a record, its files, its versions, the communities list, a community's subcommunities, and the vocabularies.

A pace of 2 requests per second therefore fails on a long iteration over a search. zenotheca puts the two search routes in the `search` rate class at 0.5 requests per second and keeps 2 requests per second for everything else. The limits for token holders were not checked.

## Paging limits

- `size` caps at 25 without an access token. `size=101` answers HTTP 400
  with `Page size cannot be greater than 25. Please use authenticated
  requests to increase the limit to 100.` zenotheca clamps `page_size` to
  25.
- Deep paging hits Elasticsearch's `max_result_window` of 10,000:
  `page=401&size=25` answers HTTP 400 with `Invalid querystring
  parameters.` There is no cursor paging anywhere; `links.next` just bumps
  `page`. zenotheca rejects `page * size` products above 10,000 before
  sending.
- The versions listing pages like a search (`size` default 25, `sort`
  `version`) and reports the family size in `hits.total` (97 versions for
  the ROR data concept on 2026-11-27).

## Redirects stand in for concept resolution

- `GET /api/records/{conceptrecid}` answers `302` with a relative
  `Location: /api/records/{newest version id}` and an HTML body.
- `GET /api/records/{recid}/versions/latest` answers `301` with an absolute
  `Location` to the newest version.
- Both redirects are followed by `records.get()` and `records.latest()`.
  A concept id in the `versions()` path answers 404
  (`The persistent identifier does not exist.`), because the concept id is
  not itself a record.

## Sorting and searching

- Verified record sorts are `bestmatch` (the default), `mostrecent`, and
  `-mostrecent`. Any other value answers HTTP 400 (`Invalid sort option`).
- `mostrecent` orders by last update, not by publication date. To find the
  newest release of a concept, use `versions()` or `latest()` instead.
- The `communities` query parameter accepts a slug
  (`communities=ror-data`), and the same clause works inside `q`
  (`q=communities:ror-data`).
- Quoted phrases work in `q` (`q=title:"ROR Data"`).
- Without `all_versions=true` a search answers one record per concept; with
  it, every version counts (3 records for the `ror-data` community became
  99).
- `HEAD /api/records/{id}` answers 200 for existing records, so `exists()`
  keeps the default HEAD-based behavior.

## Records, files, and links

- `id` is an integer while `recid` and `conceptrecid` are numeric strings.
- The `links` map mostly carries URL strings, but `links.thumbnails` is a
  nested object keyed by size. `ZenothecaRecord.links` therefore accepts
  arbitrary JSON values.
- `GET /api/records/{id}/files` answers an object (`enabled`,
  `default_preview`, `order`, `entries`, `links`), not a bare array. Each
  entry carries `key`, `size`, `checksum`, `mimetype`, `bucket_id`, and
  `links.self`/`content`/`container`.
- `GET /api/records/{id}/files/{key}/content` streams the bytes, answers
  `206 Partial Content` with `accept-ranges: bytes` for a `Range` request,
  and serves `application/octet-stream`. File names with spaces,
  parentheses, percent signs, and dashes work when URL-quoted; zenotheca
  quotes the key.
- Some `metadata` fields moved into typed blocks: `resource_type` is
  `{"id": ..., "title": ..., "type": "dataset"}` and `license` is
  `{"id": "cc-zero"}`. `creators[].affiliation` is `null` on newer records.

## Communities

- The community list answers `hits` with the newer community schema: a UUID
  `id`, a `slug`, `metadata` (`title`, `description`, `type` as an object
  with localized titles, `organizations`, `website`), `access`,
  `custom_fields`, `deletion_status`, and `revision_id`.
- The `/communities/{slug}` routes accept the slug; the `records` link of a
  community points at `/api/communities/{slug}/records`, which answers the
  record search envelope.

## Vocabularies (studied on 2026-11-27, about 28 requests)

- `GET /api/vocabularies/{name}` answers the search envelope
  (`hits.hits`, `hits.total`, `links`, `page`, `sortBy` `title`). The
  parameters `q`, `page`, and `size` work like on a record search.
- Verified vocabularies with entries: `resourcetypes` (43 entries),
  `licenses` (37 for `q=creative`), `languages` (22 for `q=english`), and
  `communitytypes` (4: `event`, `organization`, `project`, `topic`).
- `funders` and `affiliations` under `/api/vocabularies` answer an empty
  list, but the same vocabularies have entries on their own top-level
  routes: `/api/funders`, `/api/awards`, `/api/affiliations`, and
  `/api/subjects` (verified 2026-11-28). Unknown names such as `datatypes`
  or `freekeywords` answer HTTP 404 with `{"status": 404, "message": "Not
  found."}`, and `/api/names` answers 403.
- Record exports live on the website, not under `/api`:
  `/records/{id}/export/{format}` answers twelve formats with their own media
  types; `ris` and `xml` answer 404. `/api/records/{id}/files-archive`
  answers 403 without a token.
- An entry carries `id`, `created`, `updated`, `links.self`, `revision_id`,
  `title` and `description` as language maps, an optional `icon`, `tags`,
  `props`, and `type`.

## Subcommunities (studied on 2026-11-27)

- `GET /api/communities/{slug}/subcommunities` answers the community
  envelope with `sortBy` `newest` and the `type`, `funder`, and
  `organization` aggregations. A spot check across known communities
  (`zenodo`, `ecfunded`, `clarin`, `openaire`) found none with children;
  several documented slugs (`ecfunding`, `dlcclist`, `dli-vifa`, `elpub`,
  `europeancommission`) answer 404. The live test uses `zenodo` and
  asserts an empty result.

## OAI-PMH (studied on 2026-11-27)

- The endpoint is `https://zenodo.org/oai2d`, protocol 2.0, and needs no
  token. Metadata prefixes: `datacite`, `datacite4`, `dcat`, `marc21`,
  `marcxml`, `oai_datacite`, `oai_datacite4`, `oai_dc`.
- Successful answers use HTTP 200; error answers use HTTP 422 with an
  `<error code="..."/>` element. `noRecordsMatch` (a date or set window
  with no records, including single-day windows on recent dates) and
  `noSetHierarchy` answer 422, not 200 with an empty list; zenotheca
  maps both to empty pages and `idDoesNotExist` to `NotFoundError`.
- `ListSets` returns 50 sets per page; the resumption token carries
  `expirationDate`, `cursor`, and `completeListSize` (48,294 sets on
  2026-11-27, token page 2 verified with `cursor` 50).
- `ListRecords` returned 50 records for a one-week window
  (`from=2026-11-20`, `until=2026-11-26`, `oai_datacite4`) with
  `completeListSize` 92,554.

## Routes outside this client

- `GET /api/deposit/depositions` (the legacy write route) answers HTTP 403
  with `Permission denied.` without credentials. Write routes are out of
  scope until an account exists to test them.
- Zenodo rejects requests without a `User-Agent` header; the client always
  sends one built from the package name and version.
- With an access token the API documents a page size of 100; the value was
  not verified live (no token was available on 2026-11-27), and zenotheca
  only allows the larger cap when `ZENOTHECA_API_TOKEN` is set.
