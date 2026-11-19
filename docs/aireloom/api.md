# API reference

Generated from the docstrings with mkdocstrings.

## Client

::: aireloom.AireloomClient
    options:
      members:
        - request
        - aclose

## Settings

::: aireloom.AireloomSettings
    options:
      members: false

## Resources

::: aireloom._async.resources.ResearchProductsResource
::: aireloom._async.resources.ProjectsResource
::: aireloom._async.resources.OrganizationsResource
::: aireloom._async.resources.DataSourcesResource
::: aireloom._async.resources.PersonsResource
::: aireloom._async.resources.LinksResource
::: aireloom._async.resources.ScholixResource

## Sync client

The sync twins mirror the async classes above; they take the same parameters
and raise the same errors. See [Sync usage](index.md#sync-usage).

::: aireloom.AireloomSyncClient
    options:
      members:
        - request
        - close

## Filter models

::: aireloom.ResearchProductsFilters
    options:
      members:
        - to_expression
::: aireloom.ProjectsFilters
    options:
      members: false
::: aireloom.OrganizationsFilters
    options:
      members: false
::: aireloom.DataSourcesFilters
    options:
      members: false
::: aireloom.PersonsFilters
    options:
      members: false
::: aireloom.LinksFilters
    options:
      members: false
::: aireloom.ScholixFilters
    options:
      members: false

## Paging

::: bibliofabric.paging.Page

## Models

::: aireloom.ResearchProduct
    options:
      members: false
::: aireloom.Project
    options:
      members: false
::: aireloom.Organization
    options:
      members: false
::: aireloom.DataSource
    options:
      members: false
::: aireloom.Person
    options:
      members: false
::: aireloom.Relation
    options:
      members: false
::: aireloom.ScholixRelationship
    options:
      members: false
