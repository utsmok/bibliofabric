# Vocabularies

The `vocabularies` resource wraps Zenodo's vocabulary routes. A vocabulary
is a reference list. The small ones live on
`https://zenodo.org/api/vocabularies/{name}`; on 2026-11-27 these with
entries were `resourcetypes` (43 entries), `licenses` (37 entries for the
query `creative`), `languages`, and `communitytypes` (4 entries: `event`,
`organization`, `project`, `topic`). Four large vocabularies have their own
top-level routes, and the client sends these names there: `funders` (to
`/api/funders`), `awards`, `affiliations`, and `subjects`. On 2026-11-28 the
query `european` matched 758 funders and 93,558 awards. Unknown names answer
404.

Each entry is a `ZenothecaVocabulary`. `title` and `description` map
language codes to texts; `props` carries the vocabulary specific extras
(`schemaorg` for resource types, `od_lic` for licenses, `alpha_2` for
languages). The model uses `extra="allow"`, so nothing is dropped.

## Search one vocabulary

`search()` fetches one page of entries. Entries page like a search
(`page` from 1, `size` up to 25 without a token) and the repository sorts
them by title. `query` becomes the `q` parameter.

```python
page = await client.vocabularies.search("resourcetypes", page_size=10)
print(page.total, [entry.id for entry in page.results])

page = await client.vocabularies.search("licenses", query="creative")
print(page.results[0].english_title)
```

`english_title` is the `en` title, or the first title the entry carries.

## Iterate every entry

`iterate()` walks the pages until the repository reports the end of the
list. `limit` stops early.

```python
types = [
    entry.english_title async for entry in client.vocabularies.iterate("communitytypes")
]
print(types)
```

## Get one entry

`get()` fetches a single entry by its id.

```python
entry = await client.vocabularies.get("resourcetypes", "publication")
print(entry.revision_id, entry.props)
```

## Sync usage

The sync twin behaves the same:

```python
for entry in client.vocabularies.iterate("communitytypes"):
    print(entry.id, entry.english_title)
```

## Where to go next

- [OAI-PMH](oai.md) for the OAI endpoint.
- [Upstream quirks](../upstream-quirks.md).
