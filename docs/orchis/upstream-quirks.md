# Upstream quirks

Findings from about 48 paced requests against the live ORCID Public API v3.0 on 2026-11-27, with the [Public API guide](https://info.orcid.org/documentation/integration-guide/public-api/), the [swagger document](https://pub.orcid.org/v3.0/), and the [usage limits page](https://info.orcid.org/ufaqs/what-are-the-api-limits/) as references. Where a quirk affects orchis, the behavior of the client is noted.

## Representations

- `Accept: application/json` and `Accept: application/vnd.orcid+json` both answer JSON. No `Accept` header and `Accept: application/xml` answer XML. orchis sends `Accept: application/json` on every request; `representation()` methods ask for `application/xml` and return the body as text.
- `Accept: application/ld+json` answers 406 with a generic ORCID error body, both for `/{orcid}/record` and for a single work. No JSON-LD method exists, because the representation is not served today.

## Missing data answers 404

- `/{orcid}/biography` answers 404 with error code 9041 ("Biography for the given record is null") when the record has no biography. `/{orcid}/emails` answers 404 the same way when the record has no public email. Both readers return `None`.
- Empty lists differ: keywords, peer-reviews, and addresses answer 200 with an empty list for the same record.
- An unused activities section was inconsistent across runs. `/{orcid}/distinctions` answered 404 in the study run and 200 with an empty `affiliation-group` in a later run on the same day. Every section reader therefore treats 404 as an empty section (`None`), and callers should handle both shapes.

## Routes and shapes

- Single-item routes use the singular segment (`/{orcid}/work/145464015`). The plural segment (`/{orcid}/works/145464015`) answers the same body with status 200. orchis sends the singular form.
- Nearly every scalar is wrapped as `{"value": ...}`, and timestamps are epoch milliseconds in the same wrapper. Field names mix singular and plural: the person section has `family-name`, expanded search has `family-names`; the summary element is `work-summary` inside `group`, while affiliation summaries sit in `affiliation-group[].summaries[]` wrapped per type. The models keep the API structure and alias it to snake_case.
- `display-index` is a number in person elements and a string in activity elements. The models accept both.
- Every element carries `put-code`, `path`, `visibility`, and a `source` block with `source-orcid` and/or `source-client-id`, so provenance survives grouping.

## Search

- `/expanded-search/` answers `{"expanded-result": [...], "num-found": N}`. A `start` past the total answers `{"expanded-result": null, "num-found": N}`; the unwrapper turns that into an empty result list with the total intact.
- `rows=1000` answers HTTP 500 with a Solr `RemoteSolrException` in `developer-message`. So does an unknown field name (`bogus-field:xyz`). Keep `rows` at 100 or below, which is the dialect maximum.
- `/search/` answers the Solr envelope `{"result": [{"orcid-identifier": ...}], "num-found": N}` and accepts the same `q`, `rows`, and `start` parameters.
- Both routes are unauthenticated. The client maps `start` to an offset and `rows` to the page size.

## Rate limits and credentials

- ORCID documents 12 requests per second for anonymous and public API callers and 24 for the member API, with a burst of 40 and a 503 above the burst. Daily quotas are 25,000 reads per IP address anonymously and 100,000 per client id for the public API. orchis defaults to 4 requests per second.
- The token and the client credentials on hand are public API credentials. The member API answered 403 (`"error": "forbidden"`) for both on a read of `https://api.orcid.org/v3.0/{orcid}/record` on 2026-11-27 and 2026-11-28, so the member API is not wrapped. The client-credentials grant at `https://orcid.org/oauth/token` with scope `/read-public` minted a token (HTTP 200), and that token worked on the public API through `ORCHIS_ACCESS_TOKEN` on 2026-11-28. Minting stays an OAuth call outside this client, so the client id and secret are not settings.

## Bulk data

The public data file is documented at [Working with the Public Data File](https://info.orcid.org/documentation/integration-guide/working-with-bulk-data) and hosted on `orcid.figshare.com`. The 2025 edition is a 17.4 GB tar.gz of XML. This package does not download or parse it; use the search routes or the data file directly.
