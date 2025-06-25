# API Reference

This section provides a basic API reference generated from the docstrings in the AIREloom library using `mkdocs-python-extractor`.

## `AireloomSession`

The main session class for interacting with AIREloom.

::: aireloom.session.AireloomSession

## Resource Clients

Clients for specific OpenAIRE API endpoints.

### `ResearchProductsClient`

For accessing research products (publications, datasets, software, etc.).

::: aireloom.resources.research_products_client.ResearchProductsClient

### `OrganizationsClient`

For accessing organization data.

::: aireloom.resources.organizations_client.OrganizationsClient

### `ProjectsClient`

For accessing research project data.

::: aireloom.resources.projects_client.ProjectsClient

### `DataSourcesClient`

For accessing data source information.

::: aireloom.resources.data_sources_client.DataSourcesClient

### `ScholixClient`

For accessing Scholix link data via the Scholexplorer API.

::: aireloom.resources.scholix_client.ScholixClient

---

*Note: For this extractor to work, the specified Python modules and classes must have docstrings. The level of detail in this API reference depends directly on the comprehensiveness of those docstrings.*
