# Free search

The Portal search at `https://portal.issn.org/search` answers a
server-rendered HTML page for every `Accept` header and format parameter;
there is no machine-readable variant. `client.search` fetches that page and
parses the result rows with the standard library, so this resource is an
HTML scrape of the public search form, not an API. When the Portal changes
its markup, the parser raises `APIError` with a body excerpt instead of
returning guesses.

```python
page = await client.search.page("0028-0836")
print(page.total)  # the data-hits value of the result list
for hit in page.hits:
    print(hit.issn, hit.medium, hit.title)
```

## Parameters

The parameters mirror the public search form. Every criterion is optional,
but at least one is required.

| Parameter | Values | Notes |
|---|---|---|
| `query` | free text | The `search` field; also matches ISSNs |
| `fuzzy` | flag | The fuzzy search checkbox |
| `chinese_script` | flag | The Chinese script checkbox |
| `partner_repositories` | `kee`, `roa`, `tra` | Repeatable |
| `iso_country` | ISO 3166-1 alpha-3 codes | Repeatable |
| `media` | `ta` (print), `cr` (online) | Repeatable |
| `category` | `reg` (confirmed record) | Repeatable |
| `page`, `page_size` | `page_size` 20, 30, 50, 100 | Defaults 1 and 20 |
| `sort_field`, `sort_order` | `search score`, `title`, `country`, `issn`; `asc`, `desc` | |

Unknown values travel to the Portal untouched, and the Portal decides
whether to accept them.

## Result rows

Each `SearchHit` carries what the row displays.

| Field | Content |
|---|---|
| `issn` | The record ISSN |
| `title` | The key title shown in the heading |
| `detail_path` | The link target under `/resource`, without the search session parameters |
| `issn_l`, `issn_h` | The ISSN-L and ISSN-H cluster identifiers |
| `medium`, `medium_label` | The medium code and its label, for example `ta` and `Print` |
| `country`, `country_label` | The country code and its label |
| `category`, `category_label` | The record badge, for example `reg` and `Confirmed record` |
| `cancelled_issns` | Cancelled ISSNs of the record |
| `other_media` | The sibling medium links of the cluster, each with `label` and `href` |

## Paging and counting

`client.search.iterate(...)` accepts the same criteria and walks the pages
one paced request at a time. It stops at `limit`, on an empty page, or when
the `data-hits` total has been reached. `client.search.count(...)` returns
the total of one request.

```python
async for hit in client.search.iterate("nature", limit=50):
    print(hit.issn, hit.country_label)
```

Because `iterate` is an async iterator, `async for` consumes it directly,
one paced request per page.
