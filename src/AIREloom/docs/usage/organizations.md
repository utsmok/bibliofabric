# Working with Organizations

This guide explains how to use the `OrganizationsClient` to interact with OpenAIRE's organization data. You'll learn how to fetch individual organizations, search for them using various filters, and iterate over large result sets.

## Accessing the Client

The `OrganizationsClient` is accessed via an `AireloomSession` instance:

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

async def main():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # You can now access the organizations client
        org_client = session.organizations
        # ... use org_client to make calls ...
        print("OrganizationsClient is ready.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Fetching a Single Organization

To retrieve a specific organization by its OpenAIRE ID, use the `get()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from bibliofabric.exceptions import NotFoundError, BibliofabricError

# Example OpenAIRE ID for an organization
# This often uses GRID, ROR, or other organizational identifiers.
ORG_ID = "openaire____::orgID:grid.5522.e" # Example: University of Twente (GRID ID)
# ORG_ID = "openaire____::orgID:ror.org/04xy42073" # Example: CERN (ROR ID)

async def fetch_single_organization():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print(f"Attempting to fetch organization with ID: {ORG_ID}")
            organization = await session.organizations.get(ORG_ID)

            print(f"\nSuccessfully fetched organization:")
            print(f"  ID: {organization.id}")
            print(f"  Legal Name: {organization.legalName}")
            print(f"  Legal Short Name: {organization.legalShortName if organization.legalShortName else 'N/A'}")

            if organization.country:
                print(f"  Country: {organization.country.label} ({organization.country.code})")

            print(f"  Website URL: {organization.websiteUrl if organization.websiteUrl else 'N/A'}")

            if organization.pids:
                print("  Persistent Identifiers:")
                for pid in organization.pids:
                    print(f"    - {pid.scheme}: {pid.value}")

        except NotFoundError:
            print(f"Error: Organization with ID '{ORG_ID}' not found.")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_single_organization())
```

The `organization` object returned is an instance of the `Organization` Pydantic model.

## Searching Organizations

To search for organizations based on various criteria, use the `search()` method. This method supports pagination, sorting, and filtering.

```python
import asyncio
from math import ceil
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import OrganizationsFilters # Import the filter model
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def search_organizations_example():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print("Searching for organizations in the Netherlands with 'University' in their name...")

            # Define filters using the OrganizationsFilters model
            filters = OrganizationsFilters(
                legalName="University", # Search by part of the legal name
                country="NL"            # Filter by country code (Note: aliased to 'countryCode' in API)
                # pid="grid.5522.e"     # Example: filter by a specific PID value (without scheme)
            )

            # Perform the search
            search_response = await session.organizations.search(
                filters=filters,
                page=1,                     # Page number (1-indexed)
                page_size=5,                # Number of results per page
                sort_by="relevance desc"    # Sort by relevance (currently the only sort option for orgs)
            )

            header = search_response.header
            results = search_response.results

            total_results = header.numFound if header.numFound is not None else 0
            page_size = header.pageSize if header.pageSize is not None else 5
            total_pages = ceil(total_results / page_size) if page_size > 0 else 0

            print(f"\nFound {total_results} organizations matching criteria.")
            if total_results > 0:
                 print(f"Displaying page 1 of {total_pages} (approx.):")

            if results:
                for i, org in enumerate(results):
                    print(f"  Result {i+1}:")
                    print(f"    Legal Name: {org.legalName}")
                    print(f"    Country: {org.country.label if org.country else 'N/A'}")
                    print(f"    ID: {org.id}")
            else:
                print("  No organizations found for this page/filter combination.")

        except ValidationError as e:
            print(f"Validation error during search: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during search: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_organizations_example())
```

### Filters (`OrganizationsFilters`)

The `filters` parameter takes an instance of `OrganizationsFilters` from `aireloom.endpoints`. Key filter fields include:
*   `search`: General keyword search.
*   `legalName`: Filter by legal name.
*   `legalShortName`: Filter by legal short name.
*   `id`: Filter by OpenAIRE organization ID.
*   `pid`: Filter by a persistent identifier value (e.g., "grid.5522.e", "04xy42073"). The scheme (like "grid", "ror") is usually implicit or handled by the API.
*   `country` (alias for `countryCode`): Filter by country code (e.g., "NL", "DE", "GB").
*   `relCommunityId`: Filter by related community ID.
*   `relCollectedFromDatasourceId`: Filter by the data source ID from which the organization was collected.

Refer to the `OrganizationsFilters` model definition in `aireloom.endpoints` for a complete list.

### Sorting (`sort_by`)

Currently, the primary valid sort field for organizations is:
*   `relevance`

Format: `"relevance asc"` or `"relevance desc"`.

### Response (`OrganizationResponse`)

The `search()` method returns an `OrganizationResponse` object (`ApiResponse[Organization]`), containing:
*   `header`: A `Header` object with pagination info.
*   `results`: A list of `Organization` model instances.

## Iterating Over All Organizations

To process all organizations matching criteria without manual pagination, use the `iterate()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import OrganizationsFilters
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def iterate_all_organizations():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        print("Iterating through organizations in Germany...")
        count = 0
        max_results_to_show = 10  # Limit for example display

        try:
            filters = OrganizationsFilters(
                country="DE" # Filter for organizations in Germany
            )

            async for org in session.organizations.iterate(
                filters=filters,
                page_size=20,  # How many to fetch per underlying API call
                # sort_by="relevance desc" # Optional: sorting by relevance
            ):
                count += 1
                country_label = org.country.label if org.country and org.country.label else "N/A"
                print(f"  #{count}: {org.legalName} (Country: {country_label}, ID: {org.id})")

                if count >= max_results_to_show:
                    print(f"\nStopping iteration early after fetching {max_results_to_show} results for this example.")
                    break

            print(f"\nFinished iterating. Total organizations processed in this run (up to limit): {count}")

        except ValidationError as e:
            print(f"Validation error during iteration: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during iteration: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during iteration: {e}")

if __name__ == "__main__":
    asyncio.run(iterate_all_organizations())
```

## The `Organization` Model

The `Organization` Pydantic model (defined in `aireloom.models.organization`) provides structured access to organization data. Key attributes include:

*   `id` (str): The OpenAIRE ID of the organization.
*   `legalShortName` (Optional[str]): The legal short name.
*   `legalName` (Optional[str]): The full legal name.
*   `alternativeNames` (Optional[list[str]]): List of alternative names.
*   `websiteUrl` (Optional[str]): The organization's website URL.
*   `country` (Optional[Country]): Country information, where `Country` has `code` and `label`.
*   `pids` (Optional[list[OrganizationPid]]): List of persistent identifiers. Each `OrganizationPid` has:
    *   `scheme` (Optional[str]): The PID scheme (e.g., "grid", "ror", "fundref").
    *   `value` (Optional[str]): The PID value.

Refer to the `aireloom.models.organization.Organization` model definition for all available fields.
