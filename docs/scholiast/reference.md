# API reference

Generated from the source with mkdocstrings.

## Client

::: scholiast.ScholiastClient
    options:
      heading_level: 3
      show_source: false
      members:
        - papers
        - authors
        - recommendations
        - datasets
        - snippets
        - patents
        - request

## Sync client

::: scholiast.ScholiastSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - papers
        - authors
        - recommendations
        - datasets
        - snippets
        - patents
        - request

## Settings

::: scholiast.ScholiastSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

Each resource client inherits the generic operations from
`bibliofabric.ResourceClient` (`get`, `search`, `iterate`, `collect`,
`first`, `count`) through
`scholiast._async.resources.ScholiastResourceClient`.
Only the members that Semantic Scholar changes or adds are shown here.

::: scholiast._async.papers.PapersClient
    options:
      heading_level: 3
      show_source: false

::: scholiast._async.authors.AuthorsClient
    options:
      heading_level: 3
      show_source: false

::: scholiast._async.recommendations.RecommendationsClient
    options:
      heading_level: 3
      show_source: false

::: scholiast._async.datasets.DatasetsClient
    options:
      heading_level: 3
      show_source: false

::: scholiast._async.snippets.SnippetsClient
    options:
      heading_level: 3
      show_source: false

::: scholiast._async.patents.PatentsClient
    options:
      heading_level: 3
      show_source: false

## Models

::: scholiast.models.Paper
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.Author
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.ExternalIds
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.Citation
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.Reference
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.PaperMatch
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.AutocompletePaper
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.SnippetSearchResult
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.Patent
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.Release
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.DatasetMetadata
    options:
      heading_level: 3
      show_source: false

::: scholiast.models.DatasetDiffList
    options:
      heading_level: 3
      show_source: false

## Unwrapper

::: scholiast.ScholiastUnwrapper
    options:
      heading_level: 3
      show_source: false
