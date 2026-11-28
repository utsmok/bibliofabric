# API reference

Generated from the source with mkdocstrings.

## Client

::: zenotheca.ZenothecaClient
    options:
      heading_level: 3
      show_source: false
      members:
        - records
        - communities
        - vocabularies
        - oai
        - request
        - rate_class

## Sync client

::: zenotheca.ZenothecaSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - records
        - communities
        - vocabularies
        - oai
        - request

The sync twins of the resource clients are exported from the package root
(`ZenothecaRecordsSyncClient`, `ZenothecaCommunitiesSyncClient`,
`VocabulariesSyncClient`, `OaiSyncClient`). They
mirror the async resource clients method for method.

## Settings

::: zenotheca.ZenothecaSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

Each resource client inherits the generic operations from
`bibliofabric.ResourceClient` (`get`, `search`, `iterate`, `collect`,
`first`, `count`) through `zenotheca._async.dialect.ZenothecaResourceClient`.
Only the members that Zenodo changes or adds are shown here.

::: zenotheca._async.records.ZenothecaRecordsClient
    options:
      heading_level: 3
      show_source: false
      members:
        - get
        - search
        - iterate
        - count
        - versions
        - latest
        - files
        - download_file
        - communities
        - export

::: zenotheca._async.communities.ZenothecaCommunitiesClient
    options:
      heading_level: 3
      show_source: false
      members:
        - records
        - subcommunities

::: zenotheca._async.vocabularies.VocabulariesClient
    options:
      heading_level: 3
      show_source: false

::: zenotheca._async.oai.OaiClient
    options:
      heading_level: 3
      show_source: false

::: zenotheca._async.dialect.ZenothecaResourceClient
    options:
      heading_level: 3
      show_source: false

## Query helpers

::: zenotheca.filters.term
    options:
      heading_level: 3
      show_source: false

::: zenotheca.filters.phrase
    options:
      heading_level: 3
      show_source: false

::: zenotheca.filters.community
    options:
      heading_level: 3
      show_source: false

::: zenotheca.filters.resource_type
    options:
      heading_level: 3
      show_source: false

::: zenotheca.filters.any_of
    options:
      heading_level: 3
      show_source: false

::: zenotheca.filters.all_of
    options:
      heading_level: 3
      show_source: false

## Identifier helpers

::: zenotheca.ids.normalize_record_id
    options:
      heading_level: 3
      show_source: false

::: zenotheca.ids.normalize_community_slug
    options:
      heading_level: 3
      show_source: false

## Dialect

::: zenotheca.dialect
    options:
      heading_level: 3
      show_source: false
      members:
        - ZENODO_API_BASE_URL
        - ZENODO_OAI_BASE_URL
        - ZENODO_MAX_PAGE_SIZE
        - ZENODO_DEFAULT_PAGE_SIZE
        - ZENODO_MAX_RESULT_WINDOW
        - RECORD_SORT_OPTIONS
        - RECORD_EXPORT_FORMATS
        - TOP_LEVEL_VOCABULARIES
        - ZENODO_SEARCH_RATE_CLASS
        - ZENODO_SEARCH_REQUESTS_PER_SECOND
        - is_search_route

## Models

Entity models live in `zenotheca.models` and re-export from the top-level
package (`from zenotheca import ZenothecaRecord, ...`). They are plain
Pydantic models with `extra="allow"`; see the source for the full field
list.

::: zenotheca.models.ZenothecaRecord
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.ZenothecaRecordMetadata
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.ZenothecaFiles
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.ZenothecaFileEntry
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.ZenothecaCommunity
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.ZenothecaCommunityMetadata
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.ZenothecaVocabulary
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiIdentifyResponse
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiFormats
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiSets
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiIdentifiers
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiRecords
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiRecordResponse
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiRecord
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiHeader
    options:
      heading_level: 3
      show_source: false

::: zenotheca.models.OaiResumptionToken
    options:
      heading_level: 3
      show_source: false
