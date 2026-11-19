# Links

The `/v3/research-products/links` route returns relations between research
products as individual query parameters (not the V4 filter expression).

```python
from aireloom import LinksFilters

page = await client.research_products.search_links(
    LinksFilters(relation="IsSupplementTo", sourceType="publication"),
    page=0,
    page_size=99,
)
page.results  # list[Relation]
page.total  # totalLinks from the header

async for relation in client.research_products.iterate_links(limit=1000):
    ...
```

Pages are 0-indexed and page sizes cap at 99; sizes of 100 or more silently
return 10 results (see [upstream quirks](../quirks.md)). The route requires
one of the pid, publisher, or type parameters; a bare query returns 400.

The route has no cursor and no sort parameter, so page windows are not
pinned: if the upstream ordering changes between requests, pages can shift
and relations can be skipped or duplicated. The iterator stops on an empty
page or when the reported total has been fetched, which bounds the walk but
cannot remove that hazard.

## Relation types

```python
info = await client.research_products.get_relations_info()
info[0].relation  # "Cites"
info[0].inverse  # "IsCitedBy"
info[0].description
```

## Relation vocabulary

```python
from aireloom import RELATION_INVERSES, RelationName, relation_inverse

relation_inverse("Cites")  # "IsCitedBy"
relation_inverse("IsRelatedTo")  # "IsRelatedTo" (symmetric)
relation_inverse("nonsense")  # None
```

The vocabulary is static data mirroring the relations-info payload:
`RelationName` is the union of both directions, and
`RELATION_INVERSES`/`relation_inverse()` map each name to its inverse
without a live request.
