# Upstream quirks

Findings from the live study of Wikidata's three read interfaces on 2026-11-27, at about 60 paced requests, with the [Action API self-documentation](https://www.wikidata.org/w/api.php?action=help&modules=wbgetentities), the [Wikibase REST OpenAPI document](https://www.wikidata.org/w/rest.php/wikibase/v1/openapi.json), and the [data access guides](https://www.wikidata.org/wiki/Wikidata:Data_access) as references. Where a quirk affects quiddita, the behavior of the client is noted.

## Read modules that exist

The module index of `action=help` lists these read modules: `wbgetentities`, `wbsearchentities`, `wbgetclaims`, `wbformatentities`, `wbformatvalue`, `wbparsevalue`, `wbavailablebadges`, `wbcheckconstraints`, and `wbsgetsuggestions`, plus the write modules. The modules `wbsearchbytitle` and `wbformatentitiesdata` do not exist on Wikidata; both answer `Unrecognized value for parameter "action"`.

## Action API error reporting

All Action API errors, soft and hard, answer with HTTP 200 and an `{"error": {code, info}}` body. Unknown module, unknown parameter value, too many ids, and `no-such-entity` all came back with 200. quiddita raises on that shape in the unwrapper: `no-such-entity` becomes `NotFoundError`, everything else `ConfigurationError`.

## Parameter facts

- `wbgetentities` accepts at most 50 ids per request (`toomanyvalues`, lowlimit 50). `batch_get()` and `iterate_ids()` chunk at 50.
- An unknown item, form, or sense id fails the whole `wbgetentities` request with `no-such-entity`, and the error body names the id as `id` (verified 2026-11-28). An unknown lexeme or property id answers with success and a `{"id": ..., "missing": ""}` stub instead. Both raise `NotFoundError` in the client. `iterate_ids()` drops and records such ids with `on_error="skip"`.
- `redirects` accepts `yes` and `no` (default `yes`); the values `0`, `1`, and the empty string answer `badvalue`. With `redirects=no` a redirect id answers as a stub entity (`info` only).
- `wbgetclaims`'s `rank` accepts `deprecated`, `normal`, and `preferred`. The value `valid` answers `badvalue`, so `ClaimsClient` rejects it before sending.
- `wbsearchentities` reports no total: `searchinfo` carries `search` and `offset` only. `count()` is therefore not supported, and `iterate()` walks `continue` offsets until an empty page.
- `wbformatentities` returns HTML links per id; `wbparsevalue` parses values against a `datatype`; `wbavailablebadges` takes no `titles` or `site` parameters (it warns and returns all badges).
- Multi-value parameters accept pipe-joined values (`ids=Q42|P31`); quiddita joins sequences with `|`.

## Special:EntityData (verified 2026-11-28)

- `wiki/Special:EntityData/{id}.{format}` serves the full entity per format: `json` (200 `application/json`, same shape as `wbgetentities`), `jsonld`, `rdf`, `nt`, `ttl`, and `n3`. The suffixes `nquads`, `trig`, and `svg` answer 415.
- `revision=<old revid>` serves that revision; an unknown revision answers 404 with an HTML page, an invalid id answers 400 with `Invalid ID: ...`. The route works for items, properties, and lexemes (`L2.json`).
- `Special:EntityData?ids=Q42|Q5&format=json` answers HTML: the `ids` parameter is not a JSON route, so the client fetches one entity per request.
- `https://www.wikidata.org/entity/Q42` answers 303 to `Special:EntityData/Q42.ttl` under `Accept: text/turtle`; `client.entity_data.negotiate()` follows that redirect.
- `https://query.wikidata.org/bigdata/ld/wd/Q42`, `.ttl`, and `.jsonld` all answer 404 (verified 2026-11-28): the linked-data endpoint of the query service is gone.

## REST suggest and lexeme routes (verified 2026-11-28)

- `/suggest/items` and `/suggest/properties` answer the same result shape as `/search/items` (match type can be `alias`). The query parameter is `q`; `search=` answers 400 `parameter-validation-failed`.
- The lexeme routes live only under `/w/rest.php/wikibaselexeme/v0`: `/entities/lexemes/L2` answers 200 with `{id, lemmas, lexical_category, language, statements, forms, senses}`, where `lexical_category` and `language` are bare item ids. The same path under `wikibase/v1` answers 404, and `/entities/forms/{id}` and `/entities/senses/{id}` answer `rest-no-match`.

## Action utility modules (verified 2026-11-27/28)

- `wbavailablebadges` answers `{"badges": [...]}` with no parameters.
- `wbformatentities` answers `wbformatentities: {id: html}`; the `props` and `languages` parameters are ignored with a warning, so the client does not offer them.
- `wbformatvalue` takes `datavalue` as the JSON `{"type": ..., "value": ...}` object and `datatype`; without the `type` key it answers `baddatavalue`.
- `wbparsevalue` answers `results: [{raw, value, type}]` for `values` and `datatype`.
- `wbsgetsuggestions` answers `search: [{id, url, rating, label, description}]` and requires `entity` or `properties`; without both it answers `propertysuggester-wbsgetsuggestions-either-entity-or-properties`. With `entity=Q42` the suggester answered an empty list on 2026-11-27.
- `wbcheckconstraints` takes the entities in an `id` parameter (maximum 50, pipe-joined); `entity` and `entityid` answer the `no-data` error. The report is keyed by entity, then property, with per-claim `mainsnak.results` entries carrying status, constraint, and message HTML.

## Term data on 2026-11-27

The item Q42 answered with no English label in any read shape (Action API with and without `languages=en`, REST item payload, and the REST `/labels/en` route answering `resource-not-found`), while `wbsearchentities` still matched it on the English label and the English description answered normally. The client's `label()` helpers return `None` in that case; they never fall back silently.

## REST API paths

The Wikibase REST API on Wikidata lives at `https://www.wikidata.org/w/rest.php/wikibase/v1/`. The bare `https://wikidata.org/...` spelling 301-redirects to `www`, and `/items/Q42` answers `rest-no-match`; the real entity routes are `/entities/items/{id}`, `/entities/properties/{id}`, and `/statements/{statement_id}`. The read routes are the entity GETs, the per-language `labels`, `descriptions`, `aliases` (plus `*_with_language_fallback`), `sitelinks` (plus per-site), `statements` (plus per-statement), `property-data-types`, and `search/items` and `search/properties`.

The `_fields` query parameter that the OpenAPI document lists for the entity GET is rejected by the live API with `invalid-query-parameter` (HTTP 400). The client therefore always fetches full payloads.

The `labels_with_language_fallback` and `descriptions_with_language_fallback` routes answer HTTP 307 when another language serves the term (a request for `simple` redirected to the fallback chain). The term methods follow redirects.

The REST statement payload differs from the Action API claim: `property` arrives as a `{id, data_type}` object in entity payloads and as a string in the per-statement route, and value `content` is absent for `somevalue` and `novalue` snaks. The models accept both shapes. Lexemes live under a separate prefix (`/w/rest.php/wikibaselexeme/v0`), where `client.lexemes.get()` reads one lexeme. `wbgetentities` reads lexemes by id too.

## SPARQL query service

- `GET` and `POST` both answer `format=json` with the SPARQL 1.1 JSON result (`head.vars`, `results.bindings`, typed terms with `uri`/`literal`, `xml:lang`, and `datatype`).
- Without an `Accept` header, the default answer is a SPARQL-result XML document. A non-JSON `format` query parameter is ignored; other representations (`csv`, `tsv`, `turtle`) are selected through `Accept` (verified 2026-11-27).
- A malformed query answers with HTTP 400 and a plain-text Java stack trace starting with `SPARQL-QUERY: queryStr=...`, not a JSON error envelope.
- Under load the service answers HTTP 429 with a Wikimedia error page instead of its usual error shapes; the framework maps that to `RateLimitError` and honors `Retry-After`. The live smoke set observed 429s on 2026-11-27 after several consecutive runs.
- The service requires a descriptive `User-Agent` with contact information and asks readers to run one query at a time; the `sparql` rate class defaults to one query every 2 seconds.

## Rate defaults and sources

- Action API and REST: the guides at `Wikidata:Data_access` and `Wikidata:Data_access/Large_volume` ask readers to make requests in series with a delay, roughly one request every 500 milliseconds. Default: `max_requests_per_second=2.0`, `max_concurrency=1`.
- SPARQL: `Wikidata:SPARQL_query_service` asks readers to run one query at a time and cancels overlong queries. Default: `rate_limits={"sparql": 0.5}` (one query every 2 seconds) under the shared concurrency bound.
- All three services ask for a descriptive `User-Agent` with contact information; `effective_user_agent()` builds it from `user_agent` or the package metadata, and `mailto` is appended when set.
