# DataCite REST API upstream quirks

Facts below were verified against the live API at `https://api.datacite.org`
with curl in November 2026, one to two requests per second, roughly sixty
requests during the study and a small live test run. They shape choices in
this client and the upstream documentation does not always state them.

## Paging

- The default is numbered paging with `page[number]` and `page[size]`.
  `page[size]` accepts 1 to 1000; 1001 clamps down to 1000.
- Numbered paging can only reach the first 10,000 records of a query.
  Beyond that, DataCite returns 400 and tells you to switch to cursor
  paging.
- Cursor paging starts at `page[cursor]=1`. `links.next` in the response
  carries the encoded next cursor; following it walks the whole result set.
- A cursor walk always sorts by `created` ascending, whatever `sort` says.
- `count()` and single-record requests work over either mode; the client
  uses numbered paging for `search()` and cursor paging for `iterate()` and
  `collect()`.

## Query syntax

- Full-text search uses `query=` and matches indexed metadata. Filters are
  one query parameter per criterion, not one `filter` object: `client-id=`,
  `provider-id=`, `consortium-id=`, `prefix=`, `schema-version=`,
  `state=`, `affiliation-id=`, `affiliation-country=`, `funded-by=`,
  `resource-type-id=`, `created=`, `registered=`, `published=`, and
  `has-views=` among others.
- **Unknown query parameters are silently ignored.** A typo in a filter
  yields an unfiltered result, not an error.
- List values join with commas and mean OR; different keys mean AND.
- `sort` accepts `relevance`, `name`, `created`, `updated`, `published`,
  `view-count`, `download-count`, `citation-count`, and `title`, each
  reversible with a leading `-`. Sorting by `publicationYear` is silently
  ignored.
- Sparse fieldsets use `fields[dois]=doi,titles` (route-named). `include=`
  accepts `client` and `media` on DOI routes.
- `fields[dois]` honors some attribute names (`doi`, `titles`,
  `publicationYear`, `publisher`, `schemaVersion`) but silently drops
  others, among them `resourceTypeGeneral`: even
  `fields[dois]=resourceTypeGeneral` returns empty attributes. Do not rely
  on sparse fieldsets for the general resource type.

## Attributes DataCite trims or varies

- Older records carry affiliations as bare strings; the models wrap those
  as `{"name": ...}`.
- `publisher` can be a string or an object with `name`, `publisherIdentifier`,
  and scheme fields.
- `metadataVersion` is a number on current records and a string on old ones.
- Affiliation identifiers, publisher identifiers, and registration-agency
  details are omitted unless the request passes `affiliation=true`,
  `publisher=true`, or `detail=true`. `detail=true` additionally adds
  `xml`, `viewsOverTime`, `citationsOverTime`, and relationship counts.
- The JSON:API `type` of a DOI record is `dois`, and relationship names use
  `client`, `provider`, `media`, and `repository`.

## Routes that behave differently than documented

- `GET /dois/{id}/views`, `/downloads`, and `/url` return 404. They belong
  to the login-only MDS and Usage Reports APIs, not the REST API. The
  client does not wrap them; use the DOI attributes or `events` instead.
- `GET /dois/{id}/media` returns 404 anonymously, and an
  `Accept: application/vnd.api+json` request answers with an empty
  `data: []`, so it is useless without a login and is not wrapped.
- `GET /prefixes/totals` answers `204 No Content` without a `client-id`
  parameter and a JSON array with one entry per prefix with it (verified
  2026-11-28). `prefixes.totals()` therefore requires a client id.
- `/clients/totals` and `/providers/totals` are public but are bare JSON
  arrays of `{id, title, count, temporal, states}` entries, not JSON:API
  envelopes, and they are unpaged (about 1.5 MB and 0.6 MB).
- `/client-prefixes` and `/provider-prefixes` records carry only
  `createdAt` and `updatedAt`; prefix, client, and provider are
  relationships.
- `/events` records use hyphenated attribute names (`subj-id`,
  `relation-type-id`, `citation-type`, `occurred-at`); the spec text spells
  `occured-at` without the first r, and older fixtures use that form.
- The unfiltered `/events` route stalls for tens of seconds; filter it (for
  example `doi=`) and it answers in seconds.
- `HEAD /dois/{id}` works and returns 200, so the framework default
  `exists()` needs no override.
- Unknown DOI ids return 404 with a JSON:API errors body.

## GraphQL API

- `POST /graphql` answers without a login, with the
  `Accept: application/vnd.api+json` header that the client sends on every
  request (verified 2026-11-27).
- A rejected query (an unknown field, a wrong argument type) answers 400
  with an `errors` list. A field that fails (a record that does not exist)
  answers 200 with an `errors` list and `data: null`. The client raises
  `APIError` for both and attaches the body.
- Introspection is open: `__schema` lists 69 fields of the `Query` type on
  2026-11-27. The `id` argument of `work` has the type `ID!`.
- The support portal had no page for the GraphQL API on 2026-11-27. The
  endpoint and its schema are the reference.

## Traffic limits

- No rate-limit headers are sent. DataCite documents 500 requests per
  5 minutes for anonymous callers; this client paces itself at 1.5 requests
  per second.
- `api.datacite.org` serves neither the swagger UI nor an OpenAPI document;
  the machine-readable reference lives in the DataCite support portal.
