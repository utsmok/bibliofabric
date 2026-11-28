# Reference

Classes, methods, and models of `seriatim`. All names are importable from
the package top level.

## SeriatimClient

The async client. `SeriatimSyncClient` exposes the same API synchronously.

| Member | Kind | Purpose |
|---|---|---|
| `records` | property | `RecordsClient` for `/resource/ISSN/{issn}` |
| `issn_l` | property | `IssnLClient` for `/resource/ISSN-L/{issn}` |
| `search` | property | `SearchClient` for the HTML search |
| `ltwa` | property | `LtwaClient` for the LTWA table |
| `default_headers` | property | `{"Accept": "application/ld+json"}` |

Constructor arguments: `settings` (defaults to `get_settings()`), `base_url`
override for tests, and an optional caller-owned `http_client`.

## RecordsClient and IssnLClient

Both share the same shape; the model differs.

| Method | Returns | Notes |
|---|---|---|
| `get(id)` | `SeriatimRecord` or `IssnLRecord` | Typed model; `record.raw` holds the node |
| `raw(id)` | `dict` | The untouched JSON-LD node |
| `exists(id)` | `bool` | `GET` based; `False` on 404 |

`IssnLClient.download_table(dest)` streams the public ISSN-L table zip to
`dest` and returns the path.

Identifiers normalize through `require_issn`; invalid values raise
`ConfigurationError` without a request, unregistered values raise
`NotFoundError`.

## SearchClient

| Method | Returns | Notes |
|---|---|---|
| `page(query, ...)` | `SearchPage` | One page of parsed rows; see the [search page](search.md) for parameters |
| `iterate(query, ...)` | async iterator of `SearchHit` | Walks pages; stops at `limit`, an empty page, or the total |
| `count(query, ...)` | `int` or `None` | The `data-hits` total |

## LtwaClient

| Method | Returns | Notes |
|---|---|---|
| `page(...)` | `LtwaPage` | One table page; at most 100 rows |
| `iterate(...)` | async iterator of `LtwaEntry` | Walks pages; stops on the first empty page |

## Models

- `SeriatimRecord`: one ISSN record node. Properties `issn`, `issn_l`,
  `key_title`; fields for titles, identifiers, cluster membership,
  provenance, `url`, and the cancelled and incorrect ISSN lists. Extra keys
  stay reachable, `raw` holds the node.
- `IssnLRecord`: one ISSN-L node with `hasPart` entries (`HasPart`:
  `format`, `id`, `identifier`) and the `issn_l` property.
- `SearchPage`: `total`, `page`, `page_size`, `hits`.
- `SearchHit`: `issn`, `issn_l`, `issn_h`, `title`, `detail_path`,
  `medium`, `medium_label`, `country`, `country_label`, `category`,
  `category_label`, `cancelled_issns`, `other_media`.
- `OtherMedium`: `label`, `href`.
- `LtwaPage`: `entries`, `page`, `page_size`, `search`, `languages`,
  `sort`, `order`.
- `LtwaEntry`: `word`, `abbreviation`, `language`.
- `IdentifiedBy`, `LangString`, `TitleValue`, `IsPartOf`,
  `RecordProvenance`, `GenerationActivity`, `RecordAttribution`: the nested
  node models of a record.

## Helpers

| Name | Purpose |
|---|---|
| `is_valid_issn(value)` | Modulo 11 check digit validation |
| `require_issn(value)` | Normalize to the hyphenated form or raise `ConfigurationError` |
| `parse_issn_record(node)` | Validate one record node, setting `raw` |
| `parse_issn_l(node)` | Validate one ISSN-L node, setting `raw` |
| `record_issn(record)` | Normalized ISSN of a record |
| `parse_search_page(html, page=, page_size=)` | Parse one search result page |
| `parse_ltwa_page(html)` | Parse one LTWA table page |
| `SeriatimSettings`, `get_settings()` | Settings with the `SERIATIM_` prefix |
| `iter_issn_to_issn_l(zip_path)` | Stream `IssnLink(issn, issn_l, medium)` rows from the ISSN-L table |
| `iter_issn_l_clusters(zip_path)` | Stream `(issn_l, issns)` pairs from the ISSN-L table |
