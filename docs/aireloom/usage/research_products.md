# Research products

`client.research_products` queries `/v4/research-products`. All criteria go
into one V4 `filter` expression; see the
[filter syntax](#filter-syntax) below.

## Search

```python
from aireloom import ResearchProductsFilters

page = await client.research_products.search(
    ResearchProductsFilters(type="publication", is_green=True),
    query="graph neural networks",
    sort="citation_count:desc",
    select=["id", "mainTitle", "publicationDate"],
    page_size=50,
)
page.total  # numFound from the response header
page.results  # list[ResearchProduct]
page.next_cursor  # cursor for iterate/resume
```

## Filter syntax

Each set field becomes one `field:value` entry:

- a model attribute with a dotted alias sends the dotted name
  (`ids_doi` sends `ids.doi`);
- list values join with `|` (OR within one field), commas between fields
  are AND;
- a leading `!` negates, `>` and `<` compare on numeric and date fields;
- booleans encode as `true`/`false`.

```python
ResearchProductsFilters(
    subjects=["chemistry", "biology"],  # subjects:chemistry|biology
    impact_citation_count=">100",  # impact.citation_count:>100
    oa_color="!gold",  # oa_color:!gold
)
```

Plain dictionaries work the same way:
`search({"type": "dataset", "language": "!ger"})`.

## Iterate

`iterate` walks all matches at 100 per page and stops when the API stops
returning `nextCursor` or echoes the current cursor:

```python
async for product in client.research_products.iterate(
    ResearchProductsFilters(type="dataset"), limit=500
):
    ...
```

Pass `on_page(number, next_cursor)` to checkpoint progress, and feed a saved
cursor back through `cursor=` to resume an interrupted harvest.

## Single record

```python
product = await client.research_products.get("doi_dedup___::<identifier>")
```

`get` reads `/v3/research-products/{id}`; colons in the identifier stay
unencoded.

## Batch lookups

```python
by_id = await client.research_products.batch_get(["id_1", "id_2"])
by_doi = await client.research_products.batch_get_by_doi(
    ["10.1038/nature12373", "https://doi.org/10.5281/zenodo.1234"]
)
```

DOIs are normalized before lookup and as result keys; missing DOIs are
absent from the result. Requests go out in chunks of 50 as OR expressions.

## By author ORCID

```python
works = await client.research_products.by_orcid(
    "https://orcid.org/0000-0002-1825-0097", limit=50
)
```

Any ORCID spelling works (bare, dashed, or URL); the request uses the
hyphenated form in the `authorships.author.orcid` V4 filter and returns a
plain list capped at `limit` (automatically paginating via cursor when `limit`
exceeds 100).

## Sparse batch fetch

```python
records = await client.research_products.get_fields(
    ["06cdd3ff4700::3c8734759ca685b966b1d737c37daeed"],
    ["id", "mainTitle", "publicationDate"],
)
```

Sends concurrent chunks of up to 50 IDs combining an `id` OR-filter with the
V4 `select` parameter. Records carry only the requested fields, so this is the
cheap way to enrich local rows; unknown field names are the caller's
responsibility.

## Aggregations

```python
counts = await client.research_products.group_by("type")
facets = await client.research_products.facets("type", "result_hosts", page_size=1)
```

`group_by` fetches no records; `facets` fetches records plus aggregations,
so bound it with `page_size`. See [upstream quirks](../quirks.md) for the
uneven `group_by` totals.

## Relations

`search_links`, `iterate_links`, and `get_relations_info` use the separate
`/v3/research-products/links` route; see [Links](links.md).
