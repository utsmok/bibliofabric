# Articles

`client.articles` talks to `/api/v4/search/articles/{query}` and `/api/v4/articles/{id}` and returns `Article` models. The index holds about 14 million articles, but like every DOAJ route the search serves at most 1000 records per query. Harvest everything through the [DOAJ public data dump](https://doaj.org/docs/public-data-dump/).

## Get one article by DOI

```python
article = await client.articles.get("10.3389/fpubh.2020.00115")
article = await client.articles.get("https://doi.org/10.3389/fpubh.2020.00115")
found = await client.articles.exists("10.3389/fpubh.2020.00115")
```

`get()` runs the search route with the `doi:` clause and accepts a bare DOI and a DOI URL. DOAJ answers a DOI without a record with an envelope of zero results, which the client turns into `NotFoundError`.

## Get one article by record id

```python
full = await client.articles.get_by_id(article.id)
```

`get_by_id()` runs the record route with the DOAJ record id that every search result carries as `id`. The record holds the fields of a search result plus `es_type` and an `admin` block with `in_doaj` and `publisher_record_id`. An id without a record raises `NotFoundError`.

## The record model

| Field | Content |
|---|---|
| `id` | The DOAJ record id |
| `title` | `bibjson.title` |
| `doi` | The DOI from `bibjson.identifier`, or `None` |
| `issns` | The ISSNs of the publishing journal |
| `bibjson` | The full article metadata; see below |
| `admin` | `in_doaj` and `publisher_record_id` on records from the record route, `None` on search results |
| `created_date`, `last_updated` | Record timestamps |
| `es_type` | `article` on records from the record route, `None` on search results |

Selected `bibjson` fields:

| Field | Content |
|---|---|
| `title`, `abstract` | Title and abstract text |
| `author` | Entries with `name`, `affiliation`, and `orcid` |
| `identifier` | Entries with `type` (`doi`, `eissn`, `pissn`) and `id` |
| `journal` | The journal block: `title`, `publisher` (a plain string), `country`, `language`, `issns`, `volume`, `number` |
| `link` | Entries with `type` (`fulltext`, `abstract`), `url`, and `content_type` (`PDF`, `HTML`, `ePUB`, `XML`) |
| `year`, `month` | Publication date as strings |
| `keywords`, `subject` | Keywords and LCC classification entries |

Fields DOAJ adds later are kept in `model_extra`.

## Search

```python
page = await client.articles.search(
    query='title:"food insecurity" AND year:2020', page_size=50
)
page.total  # 14038837 for the match-all query on 2026-11-27
page.results  # up to 50 Article records
```

The short field names are `title`, `doi`, `issn`, `publisher`, and `abstract`. `iterate()`, `collect()`, `first()`, and `count()` behave as on the journals page, with the same 1000-record cap.
