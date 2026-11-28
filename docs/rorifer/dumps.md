# Data dumps

ROR publishes a dump of the whole registry with every release, in the `ror-data` community on Zenodo. The dump of 2026-11-19 (v2.16) holds 152,297 records in a 40.9 MB zip file. Use it when you need every record, because the API reaches at most 10,000 records per query.

## List, pick, and download

```python
dumps = await client.dumps.list(limit=5)
for dump in dumps:
    print(dump.publication_date, dump.version, dump.zip_url)

latest = await client.dumps.latest()
path = await client.dumps.download(latest, "ror-data.zip")
```

`list()` returns `RorDump` records from the Zenodo search API, ordered by last update. `latest()` picks the one with the newest `publication_date`. `download()` streams the zip to disk, creates missing parent directories, and returns the path. A dump record also exposes `record_id`, `concept_id`, `doi`, `metadata`, `files`, and `links`.

## Read the records

```python
from rorifer import iter_dump_records

for org in iter_dump_records(path):
    print(org.id, org.display_name)
```

`iter_dump_records()` reads the JSON member of the zip one record at a time and yields `Organization` models, the same models as `client.organizations.get()`. It never loads the whole file. On a 2026 test machine, parsing and validating the full dump took 14 seconds. The function raises `ConfigurationError` when the zip has no `.json` member, when the member is not a JSON array, or when the member is truncated.

`iter_dump_records()` is a plain function, so the same call works with the sync client and without a client at all.

## Index by external id

```python
from rorifer import index_external_ids, iter_dump_records

records = list(iter_dump_records(path))
fundref = index_external_ids(records, "fundref")
nsf = fundref["100000001"][0]
```

`index_external_ids()` groups records by every `external_ids.all` value of one scheme. Keys drop whitespace and lower case, so an ISNI matches in both spellings. The full dump yields about 30,000 FundRef ids. `compact_external_id()` returns one id in that key form.

## Crosswalk to Crossref funder DOIs

```python
from rorifer import fundref_doi_from_id, fundref_id_from_doi

fundref_id_from_doi("https://doi.org/10.13039/100000001")  # "100000001"
fundref_doi_from_id("100000001")  # "10.13039/100000001"
```

Every Crossref Funder Registry DOI has the prefix `10.13039/` followed by the FundRef id. Both functions raise `ValueError` for input in any other form.
