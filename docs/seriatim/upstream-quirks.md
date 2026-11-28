# Upstream quirks

Facts verified against the live ISSN Portal with curl on 2026-11-27, in
about 55 paced requests. The portal publishes no rate limit; the client
defaults to one request per second.

## Record routes

- `GET /resource/ISSN/{issn}` with `Accept: application/ld+json` answers
  200 `application/ld+json`. The body is one JSON-LD node, not an `@graph`
  array. `?format=json` answers the same node; a `.json` suffix answers 400
  `application/json`.
- `Accept: application/json`, `text/turtle`, `application/rdf+xml`, and a
  missing `Accept` header answer the HTML page instead of JSON-LD.
- The route requires the hyphenated ISSN. The compact spelling
  (`/resource/ISSN/00280836`) answers 404 with a JSON error body.
- A value with a wrong check digit or a malformed shape answers 400 with a
  generic HTML error page. A value with a valid check digit that is not
  registered answers 404 with a JSON error body. The client validates the
  check digit before sending, so 400 never happens through the library.
- Lowercase check digit `x` works (`/resource/ISSN/2434-561x` answers the
  same node as `2434-561X`).
- `GET /resource/ISSN-L/{issn}` with the JSON-LD `Accept` header answers one
  node with a `hasPart` array listing every medium of the cluster.
- `/resource/ISSN-H/9048-0007` answers HTML only; the `ISSN-H` route does
  not serve JSON-LD through content negotiation.
- Full records share one key set: `@context`, `alternateName`, `format`,
  `hasCancelledISSN-L`, `hasIncorrectISSN`, `id` (often the empty string),
  `identifiedBy`, `identifier`, `isPartOf`, `issnBibo`, `issnSchema`,
  `mainEntityOf`, `mainTitle`, `name`, `spatial`, `title`, `type`,
  `typeDct`, `url`. Cancelled records answer only `@context`, `id`,
  `identifiedBy`, `mainEntityOf`.
- Identifier nodes cluster under `#ISSN`, `#ISSN-L` and `#KeyTitle` keys.
  Key titles carry language tags of the `und-Latn` shape. Cancelled records
  answer one flat identifier node with `cancelledInFavorOf` instead.
- Observed `format` values are `medium:Print` and `medium:Online`;
  `typeDct` was `formofmaterial:a` on every full record sampled, print and
  online alike.

## Search

- `/search` answers server-rendered HTML for every probe: the `Accept`
  headers `application/ld+json` and `application/json`, `format=json`,
  `format=jsonld`, `format=rdf`, and with a `python-httpx` user agent.
- The result container holds the total in `data-hits`; each record row is an
  `article.search-results__record` with `data-issn`, `data-key-title`,
  `data-issnl`, `data-issnh`, `data-cancelled-issn`, `data-medium` (`ta`
  print, `cr` online), `data-country`, and a `data-category` badge (`reg`
  confirmed record).
- The form fields are `search`, `fuzzy` and `chinese_script` (checkboxes
  with the value `True`), `partner_repositories` (`kee`, `roa`, `tra`),
  `iso_country`, `media`, `category`, `page`, `page_size` (20, 30, 50, 100),
  and `sort_field` (`search score`, `title`, `country`, `issn`) with
  `sort_order` (`asc`, `desc`).
- `page=2` works without the `search_id` session parameter the page embeds
  in its own links.
- The site runs Anubis bot protection. Requests with a browser-like
  `User-Agent` (tested with `Mozilla/5.0`) receive a proof-of-work
  challenge page; the library's default user agent passes.

## Title Word Abbreviations

- `/ltwa` renders the table with `page`, `page_size`, `order`, `sort` plus
  the form fields `search` and `languages` (ISO 639-2 codes).
- `page_size=100` answers 100 rows; `page_size=500` answers a page with the
  generic error alert and no table. 100 is the practical cap.
- The page carries no total row count.
- `/ltwa-export?page=1&page_size=20&order=asc&sort=word` answers 502 Bad
  Gateway (probed twice on 2026-11-27); without parameters it answers 400.
  The CSV export is therefore not wrapped.

## Other services

- No SPARQL endpoint: `/sparql` answers 404 and `data.issn.org` did not
  answer.
- ROAD (`road.issn.org`) is a separate Drupal site. Its record paths
  redirect to `publishers.issn.org/resource/issn/...` and answer HTML only,
  even with the JSON-LD `Accept` header.
- `/internal/search/export` and `/internal/browse` answer 404 without a
  session.
- The ISSN-L Table downloads as `/public/issnltables.zip` (about 25 MB) from
  the `/issnl-table` page.
- The menu lists the SRU Search API and OAI-PMH access as paid services.
  `portal.issn.org/sru` and `portal.issn.org/oai` answer 404, and
  `oai.issn.org` answers a 404 page, so no public endpoint exists without a
  subscription.
