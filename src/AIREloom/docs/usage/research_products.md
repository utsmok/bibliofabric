# Working with Research Products

This guide explains how to use the `ResearchProductsClient` to interact with OpenAIRE's research product data (e.g., publications, datasets, software). You'll learn how to fetch individual products, search for products using various filters, and iterate over large result sets.

## Accessing the Client

The `ResearchProductsClient` is accessed via an `AireloomSession` instance:

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

async def main():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # You can now access the research products client
        rp_client = session.research_products
        # ... use rp_client to make calls ...
        print("ResearchProductsClient is ready.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Fetching a Single Research Product

To retrieve a specific research product by its OpenAIRE ID, use the `get()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from bibliofabric.exceptions import NotFoundError, BibliofabricError

# Example OpenAIRE ID for a research product
# This format typically includes a prefix indicating the original source and the identifier type.
PRODUCT_ID = "openaire____::doi:10.5281/zenodo.7664304" # A Zenodo record

async def fetch_single_product():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print(f"Attempting to fetch research product with ID: {PRODUCT_ID}")
            product = await session.research_products.get(PRODUCT_ID)

            print(f"\nSuccessfully fetched product:")
            print(f"  ID: {product.id}")
            print(f"  Title: {product.mainTitle}")
            print(f"  Type: {product.type}") # e.g., 'publication', 'dataset', 'software', 'other'

            if product.author:
                print(f"  First Author: {product.author[0].fullName if product.author[0].fullName else 'N/A'}")

            print(f"  Publication Date: {product.publicationDate if product.publicationDate else 'N/A'}")

            # Accessing PIDs (e.g., DOI)
            doi_value = None
            for pid_entry in product.pid:
                if pid_entry.scheme and pid_entry.scheme.lower() == 'doi':
                    doi_value = pid_entry.value
                    break
            print(f"  DOI: {doi_value if doi_value else 'Not available'}")

            if product.bestAccessRight:
                print(f"  Best Access Right: {product.bestAccessRight.label} ({product.bestAccessRight.code})")

        except NotFoundError:
            print(f"Error: Research product with ID '{PRODUCT_ID}' not found.")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_single_product())
```

The `product` object returned is an instance of the `ResearchProduct` Pydantic model, providing type-hinted access to its attributes.

## Searching Research Products

To search for research products based on various criteria, use the `search()` method. This method supports pagination, sorting, and filtering.

```python
import asyncio
from math import ceil
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import ResearchProductsFilters # Import the filter model
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def search_products():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print("Searching for research products (articles on 'climate modeling' from 2023)...")

            # Define filters using the ResearchProductsFilters model
            filters = ResearchProductsFilters(
                mainTitle="climate modeling", # Search in the main title
                type="publication",           # Filter by type (e.g., publication, dataset, software, other)
                fromPublicationDate="2023-01-01",
                toPublicationDate="2023-12-31",
                # countryCode="NL",           # Example: filter by country
                # authorFullName="Doe, John"  # Example: filter by author
            )

            # Perform the search
            search_response = await session.research_products.search(
                filters=filters,
                page=1,                     # Page number (1-indexed)
                page_size=5,                # Number of results per page
                sort_by="publicationDate desc" # Sort by publication date, newest first
            )

            header = search_response.header
            results = search_response.results

            total_results = header.numFound if header.numFound is not None else 0
            page_size = header.pageSize if header.pageSize is not None else 5 # Default to request page_size
            total_pages = ceil(total_results / page_size) if page_size > 0 else 0

            print(f"\nFound {total_results} products matching criteria.")
            if total_results > 0:
                 print(f"Displaying page 1 of {total_pages} (approx.):")


            if results:
                for i, product in enumerate(results):
                    doi_value = next((pid.value for pid in product.pid if pid.scheme and pid.scheme.lower() == 'doi'), 'N/A')
                    print(f"  Result {i+1}:")
                    print(f"    Title: {product.mainTitle}")
                    print(f"    DOI: {doi_value}")
                    print(f"    Publication Date: {product.publicationDate if product.publicationDate else 'N/A'}")
            else:
                print("  No products found for this page/filter combination.")

        except ValidationError as e:
            print(f"Validation error during search: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during search: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_products())
```

### Filters (`ResearchProductsFilters`)

The `filters` parameter takes an instance of `ResearchProductsFilters` from `aireloom.endpoints`. Key filter fields include:
*   `search`: General keyword search across multiple fields.
*   `mainTitle`: Search within the main title.
*   `description`: Search in the description.
*   `id`: Filter by OpenAIRE ID.
*   `pid`: Filter by a persistent identifier (e.g., `doi:10.xxxx/yyyyy`).
*   `type`: Filter by product type (`publication`, `dataset`, `software`, `other`).
*   `fromPublicationDate`, `toPublicationDate`: Filter by a date range (YYYY-MM-DD).
*   `subjects`: List of subject keywords.
*   `countryCode`: Filter by country code (e.g., "NL", "DE").
*   `authorFullName`: Filter by author's full name.
*   `authorOrcid`: Filter by author's ORCID.
*   `publisher`: Filter by publisher name.
*   `bestOpenAccessRightLabel`: Filter by the label of the best open access right (e.g., "open access").
*   `isPeerReviewed` (bool): Filter by peer review status.
*   `relProjectId`: Filter by related project ID.
*   ...and many more. Refer to the `ResearchProductsFilters` model definition in `aireloom.endpoints` for a complete list.

### Sorting (`sort_by`)

The `sort_by` parameter takes a string in the format `"field_name asc"` or `"field_name desc"`. Valid sort fields for research products are:
*   `relevance`
*   `publicationDate`
*   `dateOfCollection`
*   `influence`
*   `popularity`
*   `citationCount`
*   `impulse`

Using an invalid sort field will raise a `ValidationError`.

### Response (`ResearchProductResponse`)

The `search()` method returns a `ResearchProductResponse` object, which is an `ApiResponse[ResearchProduct]`. It contains:
*   `header`: A `Header` object with pagination information like `numFound` (total results), `pageSize`, and `nextCursor`.
*   `results`: A list of `ResearchProduct` model instances for the current page.

## Iterating Over All Research Products

If you need to process all research products matching certain criteria without manually handling pagination, use the `iterate()` method. It uses efficient cursor-based pagination provided by the API.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import ResearchProductsFilters
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def iterate_all_products():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        print("Iterating through recent peer-reviewed articles from the Netherlands...")
        count = 0
        max_results_to_show = 10  # Limit for example display

        try:
            filters = ResearchProductsFilters(
                countryCode="NL",
                type="publication",
                isPeerReviewed=True,
                fromPublicationDate="2023-01-01" # Example: recent publications
            )

            async for product in session.research_products.iterate(
                filters=filters,
                page_size=20,  # How many to fetch per underlying API call
                sort_by="publicationDate desc"
            ):
                count += 1
                doi_value = next((pid.value for pid in product.pid if pid.scheme and pid.scheme.lower() == 'doi'), 'N/A')
                print(f"  #{count}: {product.mainTitle} (DOI: {doi_value}, Date: {product.publicationDate})")

                if count >= max_results_to_show:
                    print(f"\nStopping iteration early after fetching {max_results_to_show} results for this example.")
                    break

            print(f"\nFinished iterating. Total products processed in this run (up to limit): {count}")

        except ValidationError as e:
            print(f"Validation error during iteration: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during iteration: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during iteration: {e}")

if __name__ == "__main__":
    asyncio.run(iterate_all_products())
```
The `iterate()` method handles fetching subsequent pages automatically until all results are exhausted or the iteration is explicitly broken.

## The `ResearchProduct` Model

The `ResearchProduct` Pydantic model (defined in `aireloom.models.research_product`) provides a structured way to access data. Key attributes include:

*   `id` (str): The OpenAIRE ID of the product.
*   `type` (Optional[Literal["publication", "dataset", "software", "other"]]): The type of research product.
*   `originalId` (list[str]): List of original IDs from source systems.
*   `mainTitle` (Optional[str]): The main title of the product.
*   `subTitle` (Optional[str]): The subtitle.
*   `author` (list[Author]): A list of authors, where `Author` is a Pydantic model with fields like `fullName`, `name`, `surname`, `pid`.
*   `bestAccessRight` (Optional[BestAccessRight]): Information about the best determined open access right (e.g., `code`, `label`, `scheme`).
*   `publicationDate` (Optional[str]): The publication date (often YYYY-MM-DD or YYYY).
*   `pid` (list[ResultPid]): A list of persistent identifiers (e.g., DOI, Handle), where `ResultPid` has `scheme` and `value`.
*   `publisher` (Optional[str]): The publisher.
*   `descriptions` (list[str]): List of descriptions or abstracts.
*   `subjects` (list[Subject]): List of subjects/keywords.
*   `instance` (list[Instance]): List of instances of the research product, each with details like `accessRight`, `license`, `urls`, `hostedBy`.
*   `indicators` (Optional[Indicator]): Contains citation and usage metrics like `citationCount`, `influence`, `downloads`, `views`.
*   `isGreen` (Optional[bool]): Indicates if it's a green open access route.
*   `openAccessColor` (Optional[str]): Color code for OA status.
*   `isInDiamondJournal` (Optional[bool]): Indicates if it's in a diamond OA journal.
*   `publiclyFunded` (Optional[bool]): Indicates if it's publicly funded.
*   Specific fields for subtypes:
    *   For publications: `container` (journal/book series info).
    *   For datasets: `size`, `version`, `geolocations`.
    *   For software: `documentationUrls`, `codeRepositoryUrl`, `programmingLanguage`.

Refer to the `aireloom.models.research_product.ResearchProduct` model definition for all available fields and their types.
