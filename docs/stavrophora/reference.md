# API reference

## Client

::: stavrophora.client
    options:
      members:
        - StavrophoraClient

## Settings

::: stavrophora.config
    options:
      members:
        - StavrophoraSettings
        - get_settings

## Resources

::: stavrophora.resources.works
::: stavrophora.resources.journals
::: stavrophora.resources.funders
::: stavrophora.resources.members
::: stavrophora.resources.types
::: stavrophora.resources.prefixes
::: stavrophora.resources.licenses

## Filters

::: stavrophora.filters

## Models

::: stavrophora.models.work
::: stavrophora.models.entities
::: stavrophora.models.agency

## Exceptions

Exceptions are re-exported from bibliofabric; see its documentation for details. `stavrophora` exports `APIError`, `AuthError`, `BibliofabricError`, `ConfigurationError`, `NetworkError`, `NotFoundError`, `RateLimitError`, `TimeoutError`, and `ValidationError`, plus `Page`.
