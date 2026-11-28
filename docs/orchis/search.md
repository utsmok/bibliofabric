# Search

ORCID exposes one Solr index through two routes. Both accept the same query syntax and the `rows` and `start` parameters, which the client maps through the bibliofabric paging dialect (`page_size` and `page`, with `start` as a zero-based offset).

## Expanded search

`/expanded-search/` answers one expanded profile per result: names, credit name, other names, emails, and institutions. `client.expanded_search` inherits the generic `search()`, `iterate()`, `collect()`, `first()`, and `count()` operations.

```python
page = await client.expanded_search.search(
    query="family-name:Kucsko", page_size=10, page=2
)
print(page.total)  # num-found from the API
print(page.page)  # 2
for result in page.results:
    print(result.orcid_id, result.given_names, result.family_names)
    print(result.institution_name)

async for result in client.expanded_search.iterate(
    query="family-name:Kucsko", page_size=50, limit=200
):
    print(result.orcid_id)
```

A page past the total answers `{"expanded-result": null, "num-found": N}`, which becomes an empty result list. Keep `rows` at 100 or below: `rows=1000` makes the server answer HTTP 500 with a Solr exception (verified 2026-11-27).

## Solr search

`/search/` answers the same index with one `orcid-identifier` per result and no profile fields.

```python
page = await client.search.search(query="family-name:Kucsko", page_size=10)
print(page.total, [r.orcid_identifier.path for r in page.results])
```

## CSV search

`/csv-search/` answers the same index as CSV text with a header row. `fields` picks the columns through the `fl` parameter; without it ORCID answers nine columns (`orcid`, `email`, `given-names`, `family-name`, `given-and-family-names`, `current-institution-affiliation-name`, `past-institution-affiliation-name`, `credit-name`, `other-names`).

```python
csv_text = await client.expanded_search.csv(
    "family-name:hickey", fields=["orcid", "given-names", "family-name"], rows=100
)
```

## Query syntax

The query is a Solr query string over indexed fields: `family-name:Kucsko`, `given-names:Georg`, `text-and-title:magnetic`, `doi:10.1088/...`, and so on. A plain word searches the default fields. An unknown field name makes the server answer HTTP 500 rather than a validation error, so quote field values and check spellings before paging through results.

## Rate limits

Search shares the API-wide limits: 12 requests per second for anonymous and public API callers, 40 burst, and 503 above the burst. The client paces at 4 requests per second by default.
