# API reference

Generated from the source with mkdocstrings.

## Client

::: orchis.OrchisClient
    options:
      heading_level: 3
      show_source: false
      members:
        - record
        - person
        - activities
        - expanded_search
        - search
        - default_headers
        - request

## Sync client

::: orchis.OrchisSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - record
        - person
        - activities
        - expanded_search
        - search
        - default_headers
        - request

## Settings

::: orchis.OrchisSettings
    options:
      heading_level: 3
      show_source: false

::: orchis.get_settings
    options:
      heading_level: 3
      show_source: false

## Resource clients

Each resource client inherits the generic operations from `bibliofabric.ResourceClient` (`get`, `exists`, `search`, `iterate`, `collect`, `first`, `count`) through `orchis._async.resources.OrchisResourceClient`. Only the members that ORCID adds are shown here.

::: orchis._async.resources.RecordClient
    options:
      heading_level: 3
      show_source: false
      members:
        - representation

::: orchis._async.resources.PersonClient
    options:
      heading_level: 3
      show_source: false

::: orchis._async.resources.ActivitiesClient
    options:
      heading_level: 3
      show_source: false

::: orchis._async.resources.ExpandedSearchClient
    options:
      heading_level: 3
      show_source: false

::: orchis._async.resources.SolrSearchClient
    options:
      heading_level: 3
      show_source: false

::: orchis._async.resources.OrchisResourceClient
    options:
      heading_level: 3
      show_source: false
      members:
        - normalize_id
        - item_path
        - exists

## Values and helpers

::: orchis.models.values.TextValue
    options:
      heading_level: 3
      show_source: false

::: orchis.models.values.IntValue
    options:
      heading_level: 3
      show_source: false

::: orchis.models.common.FuzzyDate
    options:
      heading_level: 3
      show_source: false

::: orchis.text
    options:
      heading_level: 3
      show_source: false

## Dialect

::: orchis.dialect
    options:
      heading_level: 3
      show_source: false

## Unwrapper

::: orchis.OrchisUnwrapper
    options:
      heading_level: 3
      show_source: false
