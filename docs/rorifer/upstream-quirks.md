# Upstream quirks

Findings from about 110 requests against the live ROR v2 API on 2026-11-27 and a second round on 2026-11-28 that also covered Zenodo, with the [REST API documentation](https://ror.readme.io/docs/rest-api) as the reference. Where a quirk affects rorifer, the behavior of the client is noted.

## Rejected requests return HTTP 200

An unknown filter key, a page above 500, malformed `query.advanced` syntax, and a request that carries both `query` and `query.advanced` all answer with status 200 and a body such as `{"errors": ["..."]}`. A client that only checks the status code reports an empty result. rorifer raises `ConfigurationError` with the messages of ROR whenever an envelope carries `errors`.

An unknown query parameter is different. It answers with status 400.

## Paging is fixed and capped

Pages hold exactly 20 records and the API serves pages 1 to 500. There is no page-size parameter, no cursor, no sort, and no field selection. One query therefore reaches at most 10,000 records.

ROR's documentation warns that a paged query without a filter can repeat or skip records between pages. The warning is real. A 60-record iteration of `query=university of twente` returned 52 distinct records on 2026-11-27. Use a dump for a complete list.

## The keyword search does not find an ISNI

`query` searches names and external ids, and it finds a FundRef id (`query=100000001` returns the National Science Foundation) and a Wikidata id in upper case (`query=Q1547084`). It does not find an ISNI in either spelling. Both `query=0000000403998953` and `query=0000 0004 0399 8953` return zero records.

The exact lookup works through `query.advanced` with the field `external_ids.all`, as in `external_ids.all:"0000 0004 0399 8953"`. The match is exact and case-sensitive: `external_ids.all:"Q1547084"` finds the record and `external_ids.all:"q1547084"` finds nothing, while the grouped ISNI finds the record and the compact spelling does not (2026-11-28). That is why rorifer searches every spelling. The fields `external_ids.all.value` and `_everything_` are rejected as illegal field names. A clause such as `external_ids.type:isni` matches a record that has any id of that type, not the value next to it, so rorifer applies `id_type` to the returned records. `names.value` is different: `names.value:twente` and `names.value:Twente` answer the same records.

ROR's query parser cannot search a value that contains a double quote, a backslash, or a colon. A GRID URL fails, while the bare `grid.52788.30` works.

## Filters

The eight documented keys work as described. A repeated key means OR, and a comma between keys means AND. The pipe character does not mean OR. Repeating the whole `filter` parameter also means AND, but rorifer sends one parameter.

## Records and representations

- `id` is a URL (`https://ror.org/006hf6230`). The API accepts three forms in the path: the bare id, the URL, and `ror.org/006hf6230`. rorifer strips the domain from the last two.
- A single `GET` returns inactive and withdrawn records. A search returns active records only, unless `all_status=true` is sent.
- `external_ids` is a list of objects with `type`, `all`, and `preferred`. The dump and the API use the same schema.
- `HEAD` answers with 403, so `exists()` sends `GET`.
- `Accept: application/ld+json` answers with 406. The client asks for `application/json`.
- `query.name` redirects with 302.

## Affiliation matching

The `affiliation` parameter answers with `items` of `{substring, score, matching_type, chosen, organization}`. It returns up to 10 candidates and marks one as `chosen`.

## Data dumps

The dumps live in the `ror-data` community on Zenodo (concept record 6347574). The zip holds a JSON file with a top-level array of records in the API schema, plus a CSV file. The download URL follows the pattern `/api/records/{id}/files/{key}/content` and honors `Range`.

Three details of Zenodo matter for the dump helper (checked on 2026-11-28):

- The search `q=communities:ror-data&type=dataset` answers three records without `all_versions=true`, because Zenodo collapses a release series into its newest version. With `all_versions=true` it answers every release (99 on that day). rorifer sends the parameter, so `dumps.list()` returns one record per release.
- The search orders by last update, not by publication date, so the first hit is not always the newest release. `GET /api/records/6347574` (the concept record) answers 302 to the newest release. rorifer reads the concept record for `dumps.latest()`.
- Callers without a Zenodo account get 25 records per search page. A larger `size` answers 400 (`Page size cannot be greater than 25`). The search route accepts 30 requests per minute for such callers; the 31st answers 429 with `{"message": "30 per 1 minute"}` and a `Retry-After` header. The record route accepts about 133 requests per minute. rorifer pages by 25 and paces its Zenodo requests to one every 2 seconds.

## Rate limits and health check

The [REST API documentation](https://ror.readme.io/docs/rest-api) gives a limit of 2,000 requests per 5 minutes per IP address, about 6.7 requests per second. The API sends no rate-limit headers. Registration for a client id is paused, and ROR enforces no client-id-based limit until it reopens ([client id page](https://ror.readme.io/docs/client-id)). rorifer defaults to 6 requests per second.

`GET https://api.ror.org/heartbeat` answers the text `OK` with content type `text/html`. The route lies outside `/v2`. `RoriferClient.heartbeat()` calls it and returns `True` for that answer.
