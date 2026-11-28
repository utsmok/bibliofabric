# API reference

Generated from the source with mkdocstrings.

## Client

::: dataphora.DataphoraClient
    options:
      heading_level: 3
      show_source: false
      members:
        - dois
        - activities
        - clients
        - client_prefixes
        - providers
        - provider_prefixes
        - repositories
        - prefixes
        - events
        - graphql
        - get_settings
        - request
        - is_retryable

## Sync client

::: dataphora.DataphoraSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - dois
        - activities
        - clients
        - client_prefixes
        - providers
        - provider_prefixes
        - repositories
        - prefixes
        - events
        - graphql
        - get_settings
        - request
        - is_retryable

The sync twins of the resource clients are exported from the package root
(``DoisSyncClient``, ``ClientsSyncClient``, and so on). They mirror the
async resource clients method for method.

## Settings

::: dataphora.DataphoraSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

Each resource client inherits the generic operations from
`bibliofabric.ResourceClient` (`get`, `exists`, `search`, `iterate`,
`collect`, `first`, `count`, `batch_get`) through
`dataphora._async.dialect.DataphoraResourceClient`. Only class-specific
members are shown here.

::: dataphora._async.dois.DoisClient
    options:
      heading_level: 3
      show_source: false
      members:
        - activities

::: dataphora._async.dois.ActivitiesClient
    options:
      heading_level: 3
      show_source: false

::: dataphora._async.registry.ClientsClient
    options:
      heading_level: 3
      show_source: false
      members:
        - dois
        - totals

::: dataphora._async.registry.ProvidersClient
    options:
      heading_level: 3
      show_source: false
      members:
        - dois
        - totals

::: dataphora._async.registry.RepositoriesClient
    options:
      heading_level: 3
      show_source: false
      members:
        - dois

::: dataphora._async.registry.PrefixesClient
    options:
      heading_level: 3
      show_source: false
      members:
        - dois
        - totals

::: dataphora._async.registry.ClientPrefixesClient
    options:
      heading_level: 3
      show_source: false

::: dataphora._async.registry.ProviderPrefixesClient
    options:
      heading_level: 3
      show_source: false

::: dataphora._async.events.EventsClient
    options:
      heading_level: 3
      show_source: false

::: dataphora._async.graphql.GraphqlClient
    options:
      heading_level: 3
      show_source: false

## Filter models

Every filter model dumps with `by_alias=True` into DataCite hyphenated keys
and allows extra fields.

::: dataphora.filters.DoiFilters
    options:
      heading_level: 3
      show_source: false

::: dataphora.filters.ClientFilters
    options:
      heading_level: 3
      show_source: false

::: dataphora.filters.ProviderFilters
    options:
      heading_level: 3
      show_source: false

::: dataphora.filters.RepositoryFilters
    options:
      heading_level: 3
      show_source: false

::: dataphora.filters.PrefixFilters
    options:
      heading_level: 3
      show_source: false

::: dataphora.filters.EventFilters
    options:
      heading_level: 3
      show_source: false

## Dialect and helpers

::: dataphora.dialect
    options:
      heading_level: 3
      show_source: false
      members:
        - DATACITE_API_BASE_URL
        - DATACITE_MAX_PAGE_SIZE
        - DATACITE_MAX_NUMBERED_RESULTS
        - DATACITE_DIALECT

::: dataphora._async.dialect.DataphoraResourceClient
    options:
      heading_level: 3
      show_source: false

::: dataphora.filters.serialize_filter_params
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.common.DataphoraResource
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.common.resource_ids
    options:
      heading_level: 3
      show_source: false

## Models

Record models live in `dataphora.models` and re-export from the
top-level package (`from dataphora import DataphoraDoi, ...`). They
are plain Pydantic models; see the source for the full field list.

::: dataphora.models.DataphoraDoi
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraClientRecord
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraProvider
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraRepository
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraPrefix
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraEvent
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraActivity
    options:
      heading_level: 3
      show_source: false

::: dataphora.models.DataphoraTotals
    options:
      heading_level: 3
      show_source: false
