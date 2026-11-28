# Communities

The `communities` resource wraps Zenodo's community routes on
`https://zenodo.org/api`.

## List and search

`search()` queries the community catalog. Communities page like records
(`size` up to 25, `page` from 1) and answer `sortBy` and facet counts in
`Page.meta`.

```python
page = await client.communities.search(query="data curation", page_size=5)
for community in page.results:
    print(community.slug, community.metadata.title)
```

`get()` accepts the slug (`ror-data`) or the community URL. The `id` field
of a community is a UUID; the routes accept the slug as well.

```python
community = await client.communities.get("ror-data")
print(community.id, community.metadata.title)
```

## Records of a community

`records()` searches the records accepted into one community. It sends the
same parameters as the records search and answers the same envelope, so the
results are `ZenothecaRecord` objects and `Page.meta` carries the record
facet counts.

```python
page = await client.communities.records(
    "ror-data", {"type": "dataset"}, query="ROR", page_size=5
)
print(page.total, [record.id for record in page.results])
```

Passing `all_versions=True` counts every version of each concept in the
community instead of only the newest.

## Subcommunities

`subcommunities()` lists the children of one community. The route answers
the community envelope with `sortBy` `newest` and the `type`, `funder`,
and `organization` facets. Most communities carry no children, so `total`
is usually 0.

```python
page = await client.communities.subcommunities("zenodo")
print(page.total, [community.slug for community in page.results])
```

## Where to go next

- [Records](records.md) for the record search parameters and helpers.
- [Upstream quirks](../upstream-quirks.md).
