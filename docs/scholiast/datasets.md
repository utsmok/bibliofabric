# Datasets

`client.datasets` talks to the `/datasets/v1` routes. A release is a dated
snapshot of the whole Academic Graph, refreshed weekly. The old
`/datasets/v1/datasets` route is gone; the release routes are the current
API, and they use snake_case field names.

```python
releases = await client.datasets.releases()
# ['2022-05-10', '2022-05-17', ..., '2026-11-24']

release = await client.datasets.latest()
release.release_id  # '2026-11-24'
release.datasets  # DatasetSummary entries
release.datasets[0].name  # 'abstracts'
release.datasets[0].description

release = await client.datasets.release("2026-11-24")  # or any id, or 'latest'
```

## One dataset with file URLs

```python
dataset = await client.datasets.dataset("abstracts")
dataset.files  # temporary pre-signed download links
```

This route needs an API key and answers HTTP 401 without one. The client
sends the request anyway and lets the API decide. Downloading the files
themselves is plain HTTP against the pre-signed URLs and is not wrapped.

## Diffs between two releases

```python
diffs = await client.datasets.diffs("abstracts", "2026-11-17", "2026-11-24")
diffs.diffs[0].from_release
diffs.diffs[0].update_files  # files to insert or update
diffs.diffs[0].delete_files  # files whose records to delete
```

Applying every diff in order brings a local copy from the start release to
the end release. This route also needs an API key.
