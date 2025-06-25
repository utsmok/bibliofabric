# Working with Data Sources

This guide explains how to use the `DataSourcesClient` to interact with OpenAIRE's data source information (e.g., repositories, journals, aggregators). You'll learn how to fetch individual data sources, search for them using various filters, and iterate over large result sets.

## Accessing the Client

The `DataSourcesClient` is accessed via an `AireloomSession` instance:

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

async def main():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # You can now access the data sources client
        ds_client = session.data_sources
        # ... use ds_client to make calls ...
        print("DataSourcesClient is ready.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Fetching a Single Data Source

To retrieve a specific data source by its OpenAIRE ID, use the `get()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from bibliofabric.exceptions import NotFoundError, BibliofabricError

# Example OpenAIRE ID for a data source
# These IDs are often prefixed like 'openaire____::datasourceId:'
DS_ID = "openaire____::datasourceId:doaj" # Directory of Open Access Journals
# DS_ID = "openaire____::datasourceId:zenodo" # Zenodo Repository

async def fetch_single_data_source():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print(f"Attempting to fetch data source with ID: {DS_ID}")
            data_source = await session.data_sources.get(DS_ID)

            print(f"\nSuccessfully fetched data source:")
            print(f"  ID: {data_source.id}")
            print(f"  Official Name: {data_source.officialName}")
            print(f"  English Name: {data_source.englishName if data_source.englishName else 'N/A'}")

            if data_source.type:
                print(f"  Type: {data_source.type.value} (Scheme: {data_source.type.scheme})")

            print(f"  Website URL: {data_source.websiteUrl if data_source.websiteUrl else 'N/A'}")
            print(f"  OpenAIRE Compatibility: {data_source.openaireCompatibility if data_source.openaireCompatibility else 'N/A'}")

            if data_source.contentTypes:
                print(f"  Content Types: {', '.join(data_source.contentTypes)}")

        except NotFoundError:
            print(f"Error: Data source with ID '{DS_ID}' not found.")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_single_data_source())
```

The `data_source` object returned is an instance of the `DataSource` Pydantic model.

## Searching Data Sources

To search for data sources based on various criteria, use the `search()` method. This method supports pagination, sorting, and filtering.

```python
import asyncio
from math import ceil
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import DataSourcesFilters # Import the filter model
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def search_data_sources_example():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print("Searching for data sources that are 'Journal' type and compatible with OpenAIRE...")

            # Define filters using the DataSourcesFilters model
            filters = DataSourcesFilters(
                dataSourceTypeName="Journal",       # Filter by data source type name
                openaireCompatibility="openaire_guidelines_3.0_literature_repositories" # Example compatibility level
                # officialName="Zenodo"             # Example: filter by official name
                # subjects=["biology"]              # Example: filter by subject
            )

            # Perform the search
            search_response = await session.data_sources.search(
                filters=filters,
                page=1,                     # Page number (1-indexed)
                page_size=5,                # Number of results per page
                sort_by="relevance desc"    # Sort by relevance (currently the only sort option for data sources)
            )

            header = search_response.header
            results = search_response.results

            total_results = header.numFound if header.numFound is not None else 0
            page_size = header.pageSize if header.pageSize is not None else 5
            total_pages = ceil(total_results / page_size) if page_size > 0 else 0

            print(f"\nFound {total_results} data sources matching criteria.")
            if total_results > 0:
                 print(f"Displaying page 1 of {total_pages} (approx.):")

            if results:
                for i, ds in enumerate(results):
                    print(f"  Result {i+1}:")
                    print(f"    Official Name: {ds.officialName}")
                    ds_type = ds.type.value if ds.type and ds.type.value else "N/A"
                    print(f"    Type: {ds_type}")
                    print(f"    ID: {ds.id}")
            else:
                print("  No data sources found for this page/filter combination.")

        except ValidationError as e:
            print(f"Validation error during search: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during search: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_data_sources_example())
```

### Filters (`DataSourcesFilters`)

The `filters` parameter takes an instance of `DataSourcesFilters` from `aireloom.endpoints`. Key filter fields include:
*   `search`: General keyword search.
*   `officialName`: Filter by official name.
*   `englishName`: Filter by English name.
*   `legalShortName`: Filter by legal short name (often of the owning organization).
*   `id`: Filter by OpenAIRE data source ID.
*   `pid`: Filter by a persistent identifier value.
*   `subjects`: List of subject keywords.
*   `dataSourceTypeName`: Filter by the type of data source (e.g., "Journal", "Repository", "Aggregator").
*   `contentTypes`: List of content types hosted (e.g., "publication", "dataset").
*   `openaireCompatibility`: Filter by OpenAIRE compatibility level string.
*   `relOrganizationId`: Filter by related organization ID.
*   `relCommunityId`: Filter by related community ID.
*   `relCollectedFromDatasourceId`: Filter by the data source ID from which this data source was collected (for metadata aggregations).

Refer to the `DataSourcesFilters` model definition in `aireloom.endpoints` for a complete list.

### Sorting (`sort_by`)

Currently, the primary valid sort field for data sources is:
*   `relevance`

Format: `"relevance asc"` or `"relevance desc"`.

### Response (`DataSourceResponse`)

The `search()` method returns a `DataSourceResponse` object (`ApiResponse[DataSource]`), containing:
*   `header`: A `Header` object with pagination info.
*   `results`: A list of `DataSource` model instances.

## Iterating Over All Data Sources

To process all data sources matching criteria without manual pagination, use the `iterate()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import DataSourcesFilters
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def iterate_all_data_sources():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        print("Iterating through 'Repository' type data sources...")
        count = 0
        max_results_to_show = 10  # Limit for example display

        try:
            filters = DataSourcesFilters(
                dataSourceTypeName="Repository"
            )

            async for ds in session.data_sources.iterate(
                filters=filters,
                page_size=20,  # How many to fetch per underlying API call
                # sort_by="relevance desc" # Optional: sorting by relevance
            ):
                count += 1
                print(f"  #{count}: {ds.officialName} (ID: {ds.id})")

                if count >= max_results_to_show:
                    print(f"\nStopping iteration early after fetching {max_results_to_show} results for this example.")
                    break

            print(f"\nFinished iterating. Total data sources processed in this run (up to limit): {count}")

        except ValidationError as e:
            print(f"Validation error during iteration: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during iteration: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during iteration: {e}")

if __name__ == "__main__":
    asyncio.run(iterate_all_data_sources())
```

## The `DataSource` Model

The `DataSource` Pydantic model (defined in `aireloom.models.data_source`) provides structured access to data source information. Key attributes include:

*   `id` (str): The OpenAIRE ID of the data source.
*   `originalIds` (Optional[list[str]]): List of original IDs from other systems.
*   `pids` (Optional[list[ControlledField]]): List of persistent identifiers (e.g., OAI-PMH base URL). `ControlledField` has `scheme` and `value`.
*   `type` (Optional[ControlledField]): The type of data source (e.g., repository, journal). `ControlledField` has `scheme` and `value`.
*   `openaireCompatibility` (Optional[str]): OpenAIRE compatibility level.
*   `officialName` (Optional[str]): The official name.
*   `englishName` (Optional[str]): The English name, if different.
*   `websiteUrl` (Optional[str]): URL of the data source's website.
*   `logoUrl` (Optional[str]): URL of the data source's logo.
*   `dateOfValidation` (Optional[str]): Date of last validation by OpenAIRE.
*   `description` (Optional[str]): Description of the data source.
*   `subjects` (Optional[list[str]]): List of main subjects covered.
*   `languages` (Optional[list[str]]): List of languages of content.
*   `contentTypes` (Optional[list[str]]): List of content types (e.g., "publication", "dataset", "software").
*   `accessRights` (Optional[Literal["open", "restricted", "closed"]]): Default access rights.
*   `policies` (Optional[list[str]]): Links to policies.
*   `journal` (Optional[Container]): If the data source is a journal, this field (from `aireloom.models.research_product.Container`) may contain journal-specific metadata like ISSNs.

Refer to the `aireloom.models.data_source.DataSource` model definition for all available fields.
