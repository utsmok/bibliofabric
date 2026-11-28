# API reference

Generated from the source with mkdocstrings.

## Client

::: rorifer.RoriferClient
    options:
      heading_level: 3
      show_source: false
      members:
        - organizations
        - dumps
        - request

## Sync client

::: rorifer.RoriferSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - organizations
        - dumps
        - request

## Settings

::: rorifer.RoriferSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

Each resource client inherits the generic operations from `bibliofabric.ResourceClient` (`get`, `search`, `iterate`, `collect`, `first`, `count`) through `rorifer._async.dialect.RoriferResourceClient`. Only the members that ROR changes or adds are shown here.

::: rorifer._async.organizations.OrganizationsClient
    options:
      heading_level: 3
      show_source: false
      members:
        - search
        - iterate
        - count
        - match_affiliation
        - find_by_external_id
        - find_by_funder_doi

::: rorifer._async.dialect.RoriferResourceClient
    options:
      heading_level: 3
      show_source: false
      members:
        - build_filter_params
        - normalize_id
        - exists

::: rorifer._async.dumps.DumpsClient
    options:
      heading_level: 3
      show_source: false

## Filters

::: rorifer.OrganizationFilters
    options:
      heading_level: 3
      show_source: false

::: rorifer.filters.external_id_query
    options:
      heading_level: 3
      show_source: false

## Dialect and helpers

::: rorifer.dialect
    options:
      heading_level: 3
      show_source: false
      members:
        - ROR_API_BASE_URL
        - ROR_ZENODO_API_BASE_URL
        - ROR_ZENODO_COMMUNITY
        - ROR_PAGE_SIZE
        - ROR_MAX_PAGE
        - ORGANIZATION_TYPES
        - RECORD_STATUSES
        - ROR_FILTER_KEYS

::: rorifer.unwrapper.RoriferUnwrapper
    options:
      heading_level: 3
      show_source: false

::: rorifer.dump.iter_dump_records
    options:
      heading_level: 3
      show_source: false

::: rorifer.dump.index_external_ids
    options:
      heading_level: 3
      show_source: false

::: rorifer.dump.compact_external_id
    options:
      heading_level: 3
      show_source: false

::: rorifer.crosswalk.fundref_id_from_doi
    options:
      heading_level: 3
      show_source: false

::: rorifer.crosswalk.fundref_doi_from_id
    options:
      heading_level: 3
      show_source: false

## Models

The models live in `rorifer.models` and are re-exported from the top-level package. They are plain Pydantic models with `extra="allow"`.

::: rorifer.models.Organization
    options:
      heading_level: 3
      show_source: false
      members:
        - display_name
        - external_ids_of_type

::: rorifer.models.Name
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.ExternalId
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.Location
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.GeonamesDetails
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.Relationship
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.Link
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.Admin
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.AdminDate
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.AffiliationMatch
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.FacetCount
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.RorDump
    options:
      heading_level: 3
      show_source: false
      members:
        - zip_file
        - zip_url

::: rorifer.models.DumpFile
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.DumpFileLinks
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.DumpMetadata
    options:
      heading_level: 3
      show_source: false

::: rorifer.models.DumpLinks
    options:
      heading_level: 3
      show_source: false
