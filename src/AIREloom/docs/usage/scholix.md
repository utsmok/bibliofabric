# Working with Scholix Links (Scholexplorer)

This guide explains how to use the `ScholixClient` to interact with the OpenAIRE Scholexplorer API. This API allows you to find and explore "Scholix links" – relationships between different research products, such as a publication citing a dataset, or a software package supplementing a publication.

## Accessing the Client

The `ScholixClient` is accessed via an `AireloomSession` instance:

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

async def main():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # You can now access the Scholix client
        scholix_client = session.scholix
        # ... use scholix_client to make calls ...
        print("ScholixClient is ready.")

if __name__ == "__main__":
    asyncio.run(main())
```
The Scholix client uses a different base API URL (`https://api-beta.scholexplorer.openaire.eu/v3/`) than the OpenAIRE Graph API, but this is handled transparently by `AireloomSession`.

## Searching Scholix Links

To search for Scholix links, use the `search_links()` method. This method supports pagination and filtering.

**Important:** When using `ScholixFilters`, you **must** provide either a `sourcePid` or a `targetPid`. PIDs should be prefixed with their scheme (e.g., `doi:10.xxxx/yyyyy`).

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import ScholixFilters # Import the filter model
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def search_scholix_links_example():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            # Example 1: Find links where a specific DOI is the source
            source_doi = "10.1038/s41586-021-03964-9" # An example Nature paper DOI
            print(f"Searching for links originating from PID: doi:{source_doi}")

            filters_from_source = ScholixFilters(
                sourcePid=f"doi:{source_doi}",
                # Optional: filter by relationship type
                # relation="References", # e.g., source "References" target
                # Optional: filter by target type
                # targetType="Dataset"
            )

            response_from_source = await session.scholix.search_links(
                filters=filters_from_source,
                page=0,       # Scholexplorer API uses 0-indexed pages
                page_size=5   # Corresponds to 'rows' in the API
            )

            print(f"\nFound {response_from_source.total_links} links originating from doi:{source_doi}.")
            print(f"Displaying page {response_from_source.current_page + 1} of {response_from_source.total_pages}:")

            if response_from_source.result:
                for link in response_from_source.result:
                    target_id = link.target.identifier[0].id_val if link.target.identifier else 'N/A'
                    target_type = link.target.type if link.target.type else 'N/A'
                    rel_name = link.relationship_type.name if link.relationship_type else 'N/A'
                    print(f"  - Source ({link.source.identifier[0].id_val}) {rel_name} Target ({target_id}, Type: {target_type})")
            else:
                print("  No links found for this source PID on this page.")

            # Example 2: Find links where a specific DOI is the target
            target_doi = "10.5281/zenodo.3937230" # An example Zenodo dataset DOI
            print(f"\nSearching for links targeting PID: doi:{target_doi}")

            filters_to_target = ScholixFilters(
                targetPid=f"doi:{target_doi}",
                # relation="IsSupplementedBy" # e.g., target "IsSupplementedBy" source
            )
            response_to_target = await session.scholix.search_links(
                filters=filters_to_target,
                page_size=3
            )
            print(f"\nFound {response_to_target.total_links} links targeting doi:{target_doi}.")
            if response_to_target.result:
                for link in response_to_target.result:
                    source_id = link.source.identifier[0].id_val if link.source.identifier else 'N/A'
                    source_type = link.source.type if link.source.type else 'N/A'
                    rel_name = link.relationship_type.name if link.relationship_type else 'N/A'
                    print(f"  - Source ({source_id}, Type: {source_type}) {rel_name} Target ({link.target.identifier[0].id_val})")
            else:
                print("  No links found targeting this PID.")


        except ValueError as ve: # Raised if sourcePid/targetPid is missing
            print(f"Validation Error: {ve}")
        except ValidationError as e: # Raised for other Pydantic validation issues
            print(f"Pydantic Validation error during search: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during search: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_scholix_links_example())
```

### Filters (`ScholixFilters`)

The `filters` parameter takes an instance of `ScholixFilters` from `aireloom.endpoints`. Key filter fields include:
*   `sourcePid` (str): PID of the source research product (e.g., `doi:10.xxxx/yyyyy`). **Required if `targetPid` is not set.**
*   `targetPid` (str): PID of the target research product. **Required if `sourcePid` is not set.**
*   `sourcePublisher` (str): Name of the source publisher.
*   `targetPublisher` (str): Name of the target publisher.
*   `sourceType` (Literal["Publication", "Dataset", "Software", "Other"]): Type of the source product.
*   `targetType` (Literal["Publication", "Dataset", "Software", "Other"]): Type of the target product.
*   `relation` (str): The name of the relationship type (e.g., "References", "IsSupplementTo"). See `ScholixRelationshipNameValue` in `aireloom.models.scholix` for common values.
*   `from_date` (date): Filter links published from this date (YYYY-MM-DD). Aliased as `from` in the API.
*   `to_date` (date): Filter links published up to this date (YYYY-MM-DD). Aliased as `to` in the API.

### Response (`ScholixResponse`)

The `search_links()` method returns a `ScholixResponse` object, which contains:
*   `current_page` (int): The current page number (0-indexed).
*   `total_links` (int): Total number of links matching the query.
*   `total_pages` (int): Total number of pages available.
*   `result` (list[ScholixRelationship]): A list of `ScholixRelationship` model instances for the current page.

## Iterating Over All Scholix Links

If you need to process all Scholix links matching certain criteria without manually handling pagination, use the `iterate_links()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import ScholixFilters
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def iterate_all_scholix_links():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # Example: Iterate over all links where a specific dataset is the target
        target_dataset_doi = "10.5281/zenodo.3937230"
        print(f"Iterating through all links targeting dataset: doi:{target_dataset_doi}")
        count = 0
        max_results_to_show = 10  # Limit for example display

        try:
            filters = ScholixFilters(
                targetPid=f"doi:{target_dataset_doi}",
                # sourceType="Publication" # e.g., only show publications linking to this dataset
            )

            async for link in session.scholix.iterate_links(
                filters=filters,
                page_size=20  # How many to fetch per underlying API call
            ):
                count += 1
                source_id = link.source.identifier[0].id_val if link.source.identifier else 'N/A'
                source_type = link.source.type if link.source.type else 'N/A'
                rel_name = link.relationship_type.name if link.relationship_type else 'N/A'

                print(f"  #{count}: Source ({source_id}, Type: {source_type}) {rel_name} Target ({link.target.identifier[0].id_val})")

                if count >= max_results_to_show:
                    print(f"\nStopping iteration early after fetching {max_results_to_show} links for this example.")
                    break

            print(f"\nFinished iterating. Total links processed in this run (up to limit): {count}")

        except ValueError as ve:
             print(f"Validation Error: {ve}")
        except ValidationError as e:
            print(f"Pydantic Validation error during iteration: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during iteration: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during iteration: {e}")

if __name__ == "__main__":
    asyncio.run(iterate_all_scholix_links())
```
The `iterate_links()` method handles fetching subsequent pages automatically until all results are exhausted or the iteration is explicitly broken.

## The `ScholixRelationship` Model

The `ScholixRelationship` Pydantic model (defined in `aireloom.models.scholix`) provides a structured way to access the details of each link. Key attributes include:

*   `link_provider` (Optional[list[ScholixLinkProvider]]): Information about who provided the link.
*   `relationship_type` (ScholixRelationshipType): Describes the nature of the link.
    *   `name` (ScholixRelationshipNameValue): The primary relationship type (e.g., "References", "IsSupplementTo").
    *   `sub_type` (Optional[str]): A more specific subtype of the relationship.
*   `source` (ScholixEntity): Details of the source research product.
*   `target` (ScholixEntity): Details of the target research product.
*   `link_publication_date` (Optional[datetime]): When the link itself was published.
*   `license_url` (Optional[HttpUrl]): URL of the license applying to the link information.

Both `ScholixEntity` (for source and target) objects contain:
*   `identifier` (list[ScholixIdentifier]): List of PIDs for the entity. Each `ScholixIdentifier` has:
    *   `id_val` (str, alias `ID`): The identifier value.
    *   `id_scheme` (str, alias `IDScheme`): The scheme of the identifier (e.g., "doi", "ark").
    *   `id_url` (Optional[HttpUrl], alias `IDURL`): A resolvable URL for the identifier.
*   `type` (ScholixEntityTypeName): The type of the entity (e.g., "publication", "dataset").
*   `title` (Optional[str]): Title of the entity.
*   `creator` (Optional[list[ScholixCreator]]): Creators/authors of the entity.
*   `publication_date` (Optional[str]): Publication date of the entity.
*   `publisher` (Optional[list[ScholixPublisher]]): Publishers of the entity.

Refer to `aireloom.models.scholix.py` for the complete structure of these models.
