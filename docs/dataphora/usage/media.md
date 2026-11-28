# Media and other account routes

Several DataCite routes answer 404 or 401 for anonymous callers and need an
account. dataphora does not wrap them; this page records what they are
and why they are out of scope, verified against the live API in November
2026.

## Media (`/dois/{id}/media`)

The media route lists or stores the content URLs behind a DOI. Anonymous
requests get 404; with `Accept: application/vnd.api+json` the answer is an
empty `data: []`, which makes the route useless without a login, and the
JSON list form needs an authenticated MDS session. `DataphoraDoi` already
exposes the public `contentUrl`, `url`, and `media` attribute values that
DataCite ships on the DOI record itself, which covers most read needs.

## Usage statistics (`/dois/{id}/views` and `/dois/{id}/downloads`)

These per-DOI routes do not exist in the REST API; they return 404. Counts
live in the DOI attributes instead (`viewsOverTime`, `downloadsOverTime`,
`viewCount` when `detail=true`) and in the
[`events`](events.md) resource (`relation-type-id` `views` and
`downloads`). Full monthly reports use the separate
[Usage Reports API](https://support.datacite.org/docs/usage-reports-api),
which is login-only.

## URL resolution (`/dois/{id}/url`)

This route belongs to the login-only MDS API, not the REST API, and returns
404 anonymously. Read the `url` attribute of a `DataphoraDoi` instead.

## DOI writes (create, update, delete, publish)

All DOI mutations need DataCite account credentials and the MDS or REST
write endpoints. dataphora covers reads only; writes are out of scope
until test credentials exist.

## Prefix totals

`GET /prefixes/totals` answers `204 No Content` without a login.
`DataphoraPrefixesClient.totals()` models that answer as `None`.
