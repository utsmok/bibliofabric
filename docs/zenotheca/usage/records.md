# Records

The `records` resource wraps Zenodo's record routes on `https://zenodo.org/api`.

## Get one record

`get()` accepts a version id, a concept id, a DOI, or a Zenodo URL. A
version id answers that version directly. A concept id (for example
`6347574`) makes Zenodo answer a redirect to the newest version, and the
client follows it.

```python
record = await client.records.get("10.5281/zenodo.24378467")
print(record.title)  # "ROR Data"
print(record.conceptrecid)  # "6347574", the version family
print(record.metadata.publication_date)
print(record.files[0].checksum)  # "md5:..."
```

`exists()` sends a `HEAD` request and returns `False` on 404. A missing
record raises `NotFoundError` from `get()`.

## Search

`search()` returns a `Page` of records. `query` is an Elasticsearch query
string; build the clauses with the helpers from `zenotheca`
(`community()`, `resource_type()`, `phrase()`, `term()`, `any_of()`,
`all_of()`). Filters take a mapping such as `{"type": "dataset"}` or
`{"communities": "ror-data"}`.

```python
from zenotheca import all_of, community, phrase, resource_type

page = await client.records.search(
    {"type": "dataset"},
    query=all_of(community("ror-data"), phrase("title", "ROR Data")),
    sort="mostrecent",  # orders by last update, not publication date
)
print(page.total, page.meta["aggregations"].keys())
```

Verified sorts are `bestmatch` (the default), `mostrecent`, and
`-mostrecent`. Page sizes above 25 are clamped by the client, because
Zenodo rejects larger unauthenticated requests with HTTP 400.

By default a search answers only the newest version of each concept. Pass
`all_versions=True` to count and return every version:

```python
page = await client.records.search(
    {"communities": "ror-data"}, page_size=1, all_versions=True
)
print(page.total)  # 99 instead of 3
```

`iterate()`, `collect()`, `first()`, and `count()` accept the same
arguments. Iteration stops at `limit`, when `hits.total` records were seen,
or when the next page would cross the Elasticsearch window of 10,000
results (the client checks this before sending and raises
`ConfigurationError`).

## Versions and the latest version

`versions()` lists every published version of one concept, newest first.
The id must be a version id; a concept id answers 404. `latest()` resolves
the newest version through Zenodo's `versions/latest` redirect.

```python
versions = await client.records.versions(24378467, page_size=5)
print(versions.total)  # 97
for record in versions.results:
    print(record.id, record.metadata.version)

newest = await client.records.latest(5534443)
print(newest.id)
```

## Files and downloads

The file list embedded in a record carries `key`, `size`, `checksum`, and a
`self` link. The full listing adds `mimetype`, `bucket_id`, and the
`content` link per file.

```python
files = await client.records.files(24378467)
print(files.keys)  # file names, in order
print(files.entries[0].mimetype)
```

`download_file()` streams one file to disk without loading it into memory.
It creates parent directories, overwrites an existing file, and
URL-quotes the key, so file names with spaces or punctuation work.

```python
target = await client.records.download_file(
    24378467, "v2.16-2026-11-19-ror-data.zip", "downloads/ror-data.zip"
)
print(target.stat().st_size)
```

Verify the download against the record's `md5:` checksum if you need to.

## The access token

Without a token the client sends no `Authorization` header and clamps
`page_size` to 25. Set `ZENOTHECA_API_TOKEN` and every request carries
`Authorization: Bearer`; the page size cap rises to the documented 100 and
private record reads become available.

## Where to go next

- [Communities](communities.md).
- [Vocabularies](vocabularies.md) and [OAI-PMH](oai.md) for the
  whole-repository views.
- [Upstream quirks](../upstream-quirks.md) for paging limits, redirects,
  and sort behavior.
