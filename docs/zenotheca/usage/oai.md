# OAI-PMH

The `oai` client wraps Zenodo's OAI-PMH 2.0 endpoint at
`https://zenodo.org/oai2d`. The REST API cannot list the whole repository
by date or set; the OAI endpoint can. Answers are XML, and the client
parses them into typed models: `OaiIdentifyResponse`, `OaiFormats`,
`OaiSets`, `OaiIdentifiers`, `OaiRecords`, and `OaiRecordResponse`. The
metadata payload of a record depends on the chosen prefix, so
`OaiRecord.metadata` keeps the raw XML string plus the prefix and the
namespace URI of the prefix.

```python
answer = await client.oai.identify()
print(answer.identify.repository_name)  # "Zenodo"
```

## Metadata formats

`list_metadata_formats()` returns the prefixes the repository offers
(`oai_dc`, `datacite`, `datacite4`, `marc21`, `marcxml`, `dcat`, and the
`oai_` wrappers on 2026-11-27).

```python
for item in (await client.oai.list_metadata_formats()).formats:
    print(item.metadata_prefix, item.metadata_namespace)
```

## Sets

`list_sets()` returns one page of sets. A page answers a resumption token
with `completeListSize` and `cursor`; pass the token back for the next
page. Zenodo reported 48,294 sets on 2026-11-27 with 50 sets per page.

```python
page = await client.oai.list_sets()
print(page.resumption_token.complete_list_size)
page = await client.oai.list_sets(resumption_token=page.resumption_token.token)
```

## Records and identifiers

`list_records()` and `list_identifiers()` take a `metadata_prefix` and
optional `from_`, `until`, and `set` (dates in `YYYY-MM-DD`, sets like
`user-ror-data`). `iterate_records()` and `iterate_identifiers()` follow
the resumption tokens until the repository reports the end of the list.

```python
page = await client.oai.list_records("oai_dc", from_="2026-11-20")
record = page.records[0]
print(record.header.identifier, record.metadata_prefix)

async for header in client.oai.iterate_identifiers("oai_dc", set="user-ror-data"):
    print(header.identifier, header.datestamp)
```

`get_record()` fetches one record by its OAI identifier. An unknown
identifier raises `NotFoundError`; a bad date or prefix raises
`ConfigurationError`.

```python
answer = await client.oai.get_record("oai:zenodo.org:24378467", "oai_dc")
print(answer.record.metadata)
```

## Errors

OAI errors arrive as HTTP 200 (success) or HTTP 422 (error) with an
`error` element. The client maps `noRecordsMatch` and `noSetHierarchy` to
empty pages, `idDoesNotExist` to `NotFoundError`, and the remaining codes
(`badArgument`, `badVerb`, `badResumptionToken`, `cannotDisseminateFormat`,
`noMetadataFormats`) to `ConfigurationError`.

## Sync usage

The sync twin behaves the same:

```python
with ZenothecaSyncClient() as client:
    for header in client.oai.iterate_identifiers("oai_dc", from_="2026-11-20"):
        print(header.identifier)
```

## Where to go next

- [Vocabularies](vocabularies.md) for the reference lists.
- [Upstream quirks](../upstream-quirks.md).
