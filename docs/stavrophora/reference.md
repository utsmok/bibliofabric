# API reference

## Async client

::: stavrophora._async.client
    options:
      members:
        - StavrophoraClient

## Sync client

::: stavrophora._sync.client
    options:
      members:
        - StavrophoraSyncClient

## Settings

::: stavrophora.config
    options:
      members:
        - StavrophoraSettings
        - get_settings

## Async resources

::: stavrophora._async.works
::: stavrophora._async.journals
::: stavrophora._async.funders
::: stavrophora._async.members
::: stavrophora._async.types
::: stavrophora._async.prefixes
::: stavrophora._async.licenses

## Sync resources

::: stavrophora._sync.works
::: stavrophora._sync.journals
::: stavrophora._sync.funders
::: stavrophora._sync.members
::: stavrophora._sync.types
::: stavrophora._sync.prefixes
::: stavrophora._sync.licenses

## Filters

::: stavrophora.filters

## Models

::: stavrophora.models.base
::: stavrophora.models.work
::: stavrophora.models.entities
::: stavrophora.models.agency

## Exceptions

Exceptions are re-exported from bibliofabric; see its documentation for details. `stavrophora` exports `APIError`, `AuthError`, `BibliofabricError`, `ConfigurationError`, `NetworkError`, `NotFoundError`, `RateLimitError`, `TimeoutError`, and `ValidationError`, plus `Page`.
