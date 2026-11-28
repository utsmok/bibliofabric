# Upstream quirks

Findings from about 70 requests against the live Europe PMC services on
2026-11-27, with the [RESTful web service documentation](https://europepmc.org/RestfulWebService),
the OpenAPI document at `https://www.ebi.ac.uk/europepmc/webservices/rest/v3/api-docs`,
the [annotations API page](https://europepmc.org/AnnotationsApi), and the
[grants API page](https://europepmc.org/GristAPI) as references. Where a
quirk affects europaea, the behavior of the client is noted.

## Search

- `pageSize` accepts at most 1000; a larger value answers HTTP 404 with
  `{"errCode": 404, "errMsg": "Invalid page size provided. Valid size is
  between 1 and 1000"}`.
- Search pages with `cursorMark` tokens (opaque base64); the first request
  uses `cursorMark=*`. `nextCursorMark` repeats unchanged once the result
  list is exhausted; the framework cursor iteration stops on that.
- `sort` takes `field asc|desc` with the fields `CITED`, `P_PDATE_D`,
  `PDATE`, `AUTHOR_ID`, and `RELEVANCE`. The `query=... sort_cited:y` spelling
  from the documentation also works.
- `synonym=true|false` is echoed in the request envelope.
- A search can take several seconds; one `SRC:PMC AND OPEN_ACCESS:Y` search
  took about ten seconds. The client timeout default of 30 seconds covers it.
- The search service answers transient HTTP 503 (`Search service is
  temporarily unavailable`) for some requests. The framework retry policy
  retries it.

## Article records and per-article routes

- `/article/{source}/{id}` wraps the record in a `result` key alongside
  `hitCount` and the request echo. The unwrapper returns the record.
- `fullTextXML` and `supplementaryFiles` take a bare id (`PMC13810549`,
  `NBK32884`), not the `SOURCE:ID` form. `fullTextXML` answers 404 for
  articles without open access full text (`MED/23903748` answers 404; the
  PMC twin of the same article also has no JATS full text).
- `bookXML` answers HTTP 200 with a namespace-heavy wrapper document that
  carries `<message>Article is not either Open Access article or a valid
  NBK/PM ID</message>` and `<isOpenAccess>N</isOpenAccess>` for a book
  without open access XML. The client raises `NotFoundError` on that shape.
- XML routes need `Accept: application/xml` (or anything but JSON):
  `fullTextXML` answers 406 to `Accept: application/json`. The client
  overrides the per-request header.
- `references`, `citations`, and `databaseLinks` page with `page` and
  `pageSize` (`pageSize=1000` works on `references`). The `request` echo of
  `citations` and `databaseLinks` does not reflect the requested page
  (`offSet` stays 1); the records are still the requested page.
- The routes are `/{source}/{id}/databaseLinks` (curated, `database`,
  `page`, `pageSize` parameters) and `/{source}/{id}/datalinks` (lowercase,
  not paged, `category`, `obtainedBy` parameters). `dataLinks` (camelCase)
  answers 404.
- `datalinks` answers `dataLinkList.Category` with nested `Section` and
  `Linklist.Link` records whose keys are PascalCase (`Name`, `Title`,
  `LinkProvider`). The models alias them.
- `labsLinks` returns per-provider link counts and also pages with `page`
  and `pageSize`.
- `evaluations/{source}/{id}` returns `evaluationList.evaluation`, empty for
  most articles.
- These routes do not exist in the current service (all answer 404 on
  2026-11-27, and none appears in the OpenAPI document): `comments`,
  `correctionsAndErratum`, and `textMinedTerms` (with or without a type
  suffix). Comments and corrections are part of the core record
  (`commentCorrectionList`); text-mined terms moved to the annotations API.
- The `/preprint/{source}/{id}` routes that older documentation lists
  (`fullTextXML`, `annotations`, `supplementaryFiles`, `references`,
  `citations`, `databaseLinks`, `datalinks`, `labsLinks`) all answer 404
  (verified 2026-11-27). A preprint record is available through
  `/article/PPR/{id}`, and `/{id}/supplementaryFiles` works for a preprint
  id. `/article/PPR/{id}/references` answers 404, and `/{id}/fullTextXML`
  answers 500 for a preprint id.

## The POST search and the status monitor (verified 2026-11-27)

- `POST /searchPOST` is the GET search with the parameters
  (`query`, `resultType`, `synonym`, `cursorMark`, `pageSize`, `sort`,
  `format`) in an `application/x-www-form-urlencoded` body. Without
  `format=json` in the body the route answers XML. `cursorMark` paging works
  identically (verified with a two-page walk). europaea wraps it as
  `search_post()` and `iterate_post()`.
- `POST /status-update-search` takes `Content-Type: application/json` with a
  body `{"ids": [{"src": "PPR", "extId": "PPR324115"}, ...]}` and answers
  `{"metrics": {...}, "articlesWithStatusUpdate": [...]}`. `metrics` counts
  queried, found, without update, with update, and `articlesNotFound`.
  Articles with updates carry `src`, `ext_ID`, `title`, `firstPublishDate`,
  `statusUpdates` (for example `["PUBLISHED_VERSION_AVAILABLE"]`), and
  `links` (`SELF`, `PUBLISHED_ARTICLE`; the `href` values can literally start
  with `"null"`, as in `nullMED/35166174`).
- The route returns data only for articles the status monitor tracks.
  8 requests over 2026-11-27: 25 recent `PPR` records and 40 random `PMC`
  records answered 0 updates; 30 `PPR` records from 2020 answered 14 with
  updates (preprints that received a published version). Recent preprints
  and journal articles do not carry updates, so an empty
  `articlesWithStatusUpdate` is a normal answer, not an error.
  europaea wraps it as `client.articles.status_updates()`.

## Annotations API

- `annotationsByArticleIds` takes comma-joined `articleIds` (`MED:23903748`
  or `PMC:PMC4221854`) and answers a JSON list of per-article records.
- `annotationsByEntity` (parameter `entity`), `annotationsByProvider`
  (parameter `provider`), `annotationsByRelationship` (parameters
  `firstEntity` and `secondEntity`), and `annotationsBySectionAndOrType`
  page with a float `cursorMark` and answer
  `{cursorMark, nextCursorMark, articles}`. Exhaustion is signaled with
  `nextCursorMark` of `-1.0`, which the client maps to `None`.
- `annotationsByProvider` rejects unknown provider names with 400 and lists
  the valid names in the error message.
- `annotationsBySectionAndOrType` without any filter returns the whole
  annotation store (a test request with only `section=Methods` answered
  about 24 MB). The client requires `type` or `section`.

## Grants (Grist) API

- The query endpoint is `https://www.ebi.ac.uk/europepmc/GristAPI/rest/get/query=<q>&format=json&page=N`.
  The parameters must be glued to the path with `&`. With a `?` query string
  (`...query=malaria?format=json`) the route content-negotiates and answers
  406 for `Accept: application/json`, and answers XML otherwise; the
  `format=json` parameter is ignored in that position.
- A `pageSize` query parameter is concatenated into the query string
  (`Query: "pageSize=2malaria"`). The route has no page size.
- The answer keys are PascalCase (`HitCount`, `Request`, `RecordList`) and
  `HitCount` is a JSON string.

## Rate limits

The Europe PMC documentation publishes no rate limit and no hard request
limit for unauthenticated callers. europaea defaults to 3 requests per
second and a concurrency of 2 out of courtesy, and keeps the framework
timeout default of 30 seconds because a search can take about ten seconds.
