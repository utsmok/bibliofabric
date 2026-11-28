# Title Word Abbreviations

The list of Title Word Abbreviations lives at
`https://portal.issn.org/ltwa`. The page renders one HTML table per request,
so `client.ltwa` reads that table with the standard library. This is a
scrape of a public page, not a machine-readable API. The Portal's own
`/ltwa-export` CSV route answered 502 Bad Gateway when probed on
2026-11-27 and is not wrapped.

```python
page = await client.ltwa.page(search="journal", languages=["eng"])
for entry in page.entries:
    print(entry.word, entry.abbreviation, entry.language)
```

## Parameters

| Parameter | Values | Notes |
|---|---|---|
| `search` | free text | Filters by word text |
| `languages` | ISO 639-2 codes, for example `ger`, `fra` | Repeatable |
| `page`, `page_size` | any page; 20 default | The Portal serves at most 100 rows per page |
| `sort` | `word`, `abbreviation` | Default `word` |
| `order` | `asc`, `desc` | Default `asc` |

A `page_size` above 100 makes the Portal answer a page with an error alert
and no table; the parser returns an empty list for it.

## Rows

Each `LtwaEntry` holds `word`, `abbreviation` and `language`. The Portal
renders an empty abbreviation cell as the literal text `None`; the parser
maps that cell to `None`.

## Iterating the table

The page carries no total, so `client.ltwa.iterate(...)` stops on the first
page without rows. Each page costs one paced request.

```python
async for entry in client.ltwa.iterate(sort="abbreviation"):
    print(entry.word, entry.abbreviation)
```
