# API reference

Generated from the source with mkdocstrings.

## Client

::: opcitato.OpcitatoClient
    options:
      heading_level: 3
      show_source: false
      members:
        - index
        - meta
        - request

## Sync client

::: opcitato.OpcitatoSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - index
        - meta
        - request

## Settings

::: opcitato.OpcitatoSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

::: opcitato._async.resources.IndexClient
    options:
      heading_level: 3
      show_source: false

::: opcitato._async.resources.MetaClient
    options:
      heading_level: 3
      show_source: false

## Dialect and helpers

::: opcitato.dialect
    options:
      heading_level: 3
      show_source: false
      members:
        - OPENCITATIONS_API_BASE_URL
        - INDEX_API_PATH
        - META_API_PATH
        - MULTI_ID_SEPARATOR
        - FORMATS
        - INDEX_ID_SCHEMES
        - META_ID_SCHEMES
        - PERSON_ID_SCHEMES

::: opcitato.ids.parse_identifiers
    options:
      heading_level: 3
      show_source: false

::: opcitato.ids.ParsedIdentifier
    options:
      heading_level: 3
      show_source: false

::: opcitato.ids.normalize_index_id
    options:
      heading_level: 3
      show_source: false

::: opcitato.ids.normalize_meta_ids
    options:
      heading_level: 3
      show_source: false

::: opcitato.ids.normalize_person_id
    options:
      heading_level: 3
      show_source: false

::: opcitato.ids.normalize_oci
    options:
      heading_level: 3
      show_source: false

::: opcitato.csvparse.parse_csv_rows
    options:
      heading_level: 3
      show_source: false

::: opcitato.unwrapper.OpcitatoUnwrapper
    options:
      heading_level: 3
      show_source: false

## Models

The models live in `opcitato.models` and are re-exported from the top-level package. They are plain Pydantic models with `extra="allow"`.

::: opcitato.models.Citation
    options:
      heading_level: 3
      show_source: false
      members:
        - citing_identifiers
        - cited_identifiers

::: opcitato.models.Count
    options:
      heading_level: 3
      show_source: false

::: opcitato.models.MetadataRecord
    options:
      heading_level: 3
      show_source: false
      members:
        - identifiers
        - authors
        - editors
