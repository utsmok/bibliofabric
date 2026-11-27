# API reference

Generated from the source with mkdocstrings.

## Client

::: aletheca.AlethecaClient
    options:
      heading_level: 3
      show_source: false
      members:
        - works
        - authors
        - sources
        - institutions
        - topics
        - keywords
        - publishers
        - funders
        - awards
        - locations
        - links
        - autocomplete
        - rate_limit
        - request
        - on_response
        - last_rate_limit_headers
        - is_retryable

## Sync client

::: aletheca.AlethecaSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - works
        - authors
        - sources
        - institutions
        - topics
        - keywords
        - publishers
        - funders
        - awards
        - locations
        - links
        - autocomplete
        - rate_limit
        - request
        - on_response
        - last_rate_limit_headers
        - is_retryable

The sync twins of the resource clients are exported from the package root
(``WorksSyncClient``, ``AuthorsSyncClient``, and so on). They mirror the
async resource clients method for method.

## Settings

::: aletheca.AlethecaSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

Each resource client inherits the generic operations from
`bibliofabric.ResourceClient` (`get`, `search`, `iterate`,
`collect`, `first`, `count`, `batch_get`) through
`aletheca._async.dialect.OpenAlexResourceClient`. Only class-specific members are
shown here.

::: aletheca._async.works.WorksClient
    options:
      heading_level: 3
      show_source: false
      members:
        - search
        - search_scoped
        - sample
        - batch_get_by_doi
        - batch_get_by_openalex_id
        - citing
        - referenced
        - oa_pdf_urls

::: aletheca._async.authors.AuthorsClient
    options:
      heading_level: 3
      show_source: false
      members:
        - batch_get_by_openalex_id

::: aletheca._async.locations.LocationsClient
    options:
      heading_level: 3
      show_source: false
      members:
        - normalize_id

::: aletheca._async.links.LinksClient
    options:
      heading_level: 3
      show_source: false
      members:
        - origin
        - target

## Filter models

Every filter model dumps with `by_alias=True` into OpenAlex dot-notation
keys and allows extra fields.

::: aletheca.filters.WorksFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.AuthorsFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.SourcesFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.InstitutionsFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.TopicsFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.KeywordsFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.PublishersFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.FundersFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.AwardsFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.LocationsFilters
    options:
      heading_level: 3
      show_source: false

::: aletheca.filters.LinksFilters
    options:
      heading_level: 3
      show_source: false

## Dialect and helpers

::: aletheca.dialect
    options:
      heading_level: 3
      show_source: false
      members:
        - OPENALEX_API_BASE_URL
        - MAX_OR_VALUES
        - MAX_BASIC_PAGING_RESULTS
        - MAX_SAMPLE_SIZE

::: aletheca._async.dialect.OpenAlexResourceClient
    options:
      heading_level: 3
      show_source: false

::: aletheca.reconstruct_abstract
    options:
      heading_level: 3
      show_source: false

## Models

Entity models live in `aletheca.models` and re-export from the top-level
package (`from aletheca import Work, Author, ...`). They are plain Pydantic
models; see the source for the full field list.

::: aletheca.models.Work
    options:
      heading_level: 3
      show_source: false

::: aletheca.models.GroupByBucket
    options:
      heading_level: 3
      show_source: false

::: aletheca.models.AutocompleteResult
    options:
      heading_level: 3
      show_source: false

::: aletheca.models.RateLimitStatus
    options:
      heading_level: 3
      show_source: false

::: aletheca.models.LocationRecord
    options:
      heading_level: 3
      show_source: false

::: aletheca.models.Link
    options:
      heading_level: 3
      show_source: false
