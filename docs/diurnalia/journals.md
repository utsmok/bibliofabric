# Journals

`client.journals` talks to `/api/v4/search/journals/{query}` and `/api/v4/journals/{id}` and returns `Journal` models. DOAJ has no journal listing route, so searches and ISSN lookups go through the search route. One query reaches at most 1000 records, so a full registry harvest should use the [DOAJ public data dump](https://doaj.org/docs/public-data-dump/).

## Get one journal by ISSN

```python
journal = await client.journals.get("1932-6203")
journal = await client.journals.get("19326203")  # compact spelling
found = await client.journals.exists("1932-6203")
```

`get()` runs the search route with the `issn:` clause and accepts the grouped and the compact spelling and an ISSN URL. The clause matches the print and the electronic ISSN, because DOAJ indexes both in one field. A journal that does not carry the ISSN raises `NotFoundError`.

## Get one journal by record id

```python
full = await client.journals.get_by_id(journal.id)
```

`get_by_id()` runs the record route with the DOAJ record id that every search result carries as `id`. The record holds the fields of a search result plus `es_type`, `last_manual_update`, and `in_doaj` in `admin`. An id without a record raises `NotFoundError`.

## The record model

| Field | Content |
|---|---|
| `id` | The DOAJ record id, such as `2fdf1470373343b7bd4f825179c685f5` |
| `title` | `bibjson.title` |
| `issns` | The print and electronic ISSNs that are set |
| `publisher_name` | `bibjson.publisher.name` |
| `bibjson` | The full journal metadata; see the table below |
| `admin` | Editorial flags. A search result carries `ticked`; a record from the record route also carries `in_doaj` |
| `created_date`, `last_updated`, `last_manual_update` | Record timestamps; `last_manual_update` appears on records from the record route |
| `es_type` | `journal` on records from the record route, `None` on search results |

Selected `bibjson` fields:

| Field | Content |
|---|---|
| `title`, `alternative_title` | Journal names |
| `publisher` | `name` and `country` (ISO 3166 code) |
| `pissn`, `eissn` | The ISSNs |
| `license` | Entries with `type` (`CC BY`, `CC BY-NC`, and so on), the `by`/`nc`/`nd`/`sa` flags, and `url` |
| `language`, `keywords` | Lists of ISO 639 codes and keywords |
| `subject` | Classification entries with `scheme` (LCC), `code`, and `term` |
| `oa_start`, `boai` | The year the journal went fully open access, and the BOAI flag |
| `apc`, `other_charges`, `waiver` | Charge policies, each with a `has_*` flag, the APC `max` price list, and a `url` |
| `editorial`, `copyright`, `plagiarism`, `preservation`, `deposit_policy`, `pid_scheme` | Policies and services, each with flags and URLs |
| `article` | How article licenses are displayed (`license_display`, example URL) |
| `ref` | Journal links: aims and scope, author instructions, OA statement, license terms |

Fields DOAJ adds later are kept in `model_extra`.

## Search

```python
page = await client.journals.search(
    query='language:EN AND license:"CC BY"', sort="title:asc", page_size=50
)
page.total  # 23831 for the match-all query on 2026-11-27
page.results  # up to 50 Journal records
page.page  # the page number
page.meta  # the envelope: pageSize, timestamp, query, last/next/prev URLs
```

`iterate()`, `collect()`, `first()`, and `count()` build on the same route. `iterate()` pages at `pageSize=50` and stops at `total`; a page beyond the 1000-record cap raises `ConfigurationError` before a request is sent.

## Sorting

`sort=` takes `field` or `field:direction` with `asc` (the default) and `desc`. The field uses the dot notation (`sort=bibjson.title:desc`). An unknown sort field answers 400. Fields that hold multiple values sort by their smallest value.
