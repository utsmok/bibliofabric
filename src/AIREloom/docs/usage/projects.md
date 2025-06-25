# Working with Projects

This guide explains how to use the `ProjectsClient` to interact with OpenAIRE's project data. You'll learn how to fetch individual projects, search for projects using various filters, and iterate over large result sets.

## Accessing the Client

The `ProjectsClient` is accessed via an `AireloomSession` instance:

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

async def main():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # You can now access the projects client
        projects_client = session.projects
        # ... use projects_client to make calls ...
        print("ProjectsClient is ready.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Fetching a Single Project

To retrieve a specific project by its OpenAIRE ID, use the `get()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from bibliofabric.exceptions import NotFoundError, BibliofabricError

# Example OpenAIRE ID for a project
# This format can vary based on the source (e.g., CORDIS H2020, national funders)
PROJECT_ID = "corda_h2020::269f7314d3149ba797a079979839581b" # Example H2020 project

async def fetch_single_project():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print(f"Attempting to fetch project with ID: {PROJECT_ID}")
            project = await session.projects.get(PROJECT_ID)

            print(f"\nSuccessfully fetched project:")
            print(f"  ID: {project.id}")
            print(f"  Title: {project.title}")
            print(f"  Acronym: {project.acronym if project.acronym else 'N/A'}")
            print(f"  Start Date: {project.startDate if project.startDate else 'N/A'}")
            print(f"  End Date: {project.endDate if project.endDate else 'N/A'}")

            if project.fundings:
                funding_info = project.fundings[0]
                funder_name = funding_info.name if funding_info.name else "N/A"
                stream_desc = funding_info.fundingStream.description if funding_info.fundingStream and funding_info.fundingStream.description else "N/A"
                print(f"  Funder: {funder_name} ({stream_desc})")

            if project.granted:
                 amount = project.granted.fundedAmount if project.granted.fundedAmount is not None else "N/A"
                 currency = project.granted.currency if project.granted.currency else ""
                 print(f"  Funded Amount: {amount} {currency}")


        except NotFoundError:
            print(f"Error: Project with ID '{PROJECT_ID}' not found.")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_single_project())
```

The `project` object returned is an instance of the `Project` Pydantic model.

## Searching Projects

To search for projects based on various criteria, use the `search()` method. This method supports pagination, sorting, and filtering.

```python
import asyncio
from math import ceil
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import ProjectsFilters # Import the filter model
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def search_projects_example():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            print("Searching for projects related to 'artificial intelligence' funded by 'EC'...")

            # Define filters using the ProjectsFilters model
            filters = ProjectsFilters(
                keywords=["artificial intelligence"], # Search by keywords (list)
                fundingShortName="EC",                # Search by funder short name (e.g., EC for European Commission)
                # title="Robotics research",          # Example: filter by title
                # fromStartDate="2020-01-01",       # Example: filter by start date
            )

            # Perform the search
            search_response = await session.projects.search(
                filters=filters,
                page=1,                     # Page number (1-indexed)
                page_size=3,                # Number of results per page
                sort_by="endDate desc"      # Sort by end date, newest first
            )

            header = search_response.header
            results = search_response.results

            total_results = header.numFound if header.numFound is not None else 0
            page_size = header.pageSize if header.pageSize is not None else 3 # Default to request page_size
            total_pages = ceil(total_results / page_size) if page_size > 0 else 0

            print(f"\nFound {total_results} projects matching criteria.")
            if total_results > 0:
                 print(f"Displaying page 1 of {total_pages} (approx.):")

            if results:
                for i, project in enumerate(results):
                    print(f"  Result {i+1}:")
                    print(f"    Title: {project.title}")
                    print(f"    Acronym: {project.acronym if project.acronym else 'N/A'}")
                    print(f"    ID: {project.id}")
                    print(f"    End Date: {project.endDate if project.endDate else 'N/A'}")
            else:
                print("  No projects found for this page/filter combination.")

        except ValidationError as e:
            print(f"Validation error during search: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during search: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_projects_example())
```

### Filters (`ProjectsFilters`)

The `filters` parameter takes an instance of `ProjectsFilters` from `aireloom.endpoints`. Key filter fields include:
*   `search`: General keyword search.
*   `title`: Search within the project title.
*   `keywords`: List of keywords.
*   `id`: Filter by OpenAIRE project ID.
*   `code`: Filter by project code.
*   `grantID`: Filter by grant ID.
*   `acronym`: Filter by project acronym.
*   `callIdentifier`: Filter by call identifier.
*   `fundingShortName`: Filter by the short name of the funding agency (e.g., "EC", "NSF").
*   `fundingStreamId`: Filter by funding stream ID.
*   `fromStartDate`, `toStartDate`: Filter by project start date range.
*   `fromEndDate`, `toEndDate`: Filter by project end date range.
*   `relOrganizationName`: Filter by related organization name.
*   `relOrganizationId`: Filter by related organization ID.
*   ...and more. Refer to the `ProjectsFilters` model definition in `aireloom.endpoints`.

### Sorting (`sort_by`)

Valid sort fields for projects are:
*   `relevance`
*   `startDate`
*   `endDate`

Format: `"field_name asc"` or `"field_name desc"`.

### Response (`ProjectResponse`)

The `search()` method returns a `ProjectResponse` object (`ApiResponse[Project]`), containing:
*   `header`: A `Header` object with pagination info.
*   `results`: A list of `Project` model instances.

## Iterating Over All Projects

To process all projects matching criteria without manual pagination, use the `iterate()` method.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from aireloom.endpoints import ProjectsFilters
from bibliofabric.exceptions import ValidationError, BibliofabricError

async def iterate_all_projects():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        print("Iterating through H2020 projects ending recently...")
        count = 0
        max_results_to_show = 5  # Limit for example display

        try:
            filters = ProjectsFilters(
                fundingShortName="EC", # European Commission funded
                # Consider adding a date filter if "recently" is important, e.g.,
                # fromEndDate="2023-01-01"
            )

            async for project in session.projects.iterate(
                filters=filters,
                page_size=10,  # How many to fetch per underlying API call
                sort_by="endDate desc"
            ):
                count += 1
                print(f"  #{count}: {project.title} (Acronym: {project.acronym}, End: {project.endDate})")

                if count >= max_results_to_show:
                    print(f"\nStopping iteration early after fetching {max_results_to_show} results for this example.")
                    break

            print(f"\nFinished iterating. Total projects processed in this run (up to limit): {count}")

        except ValidationError as e:
            print(f"Validation error during iteration: {e}")
        except BibliofabricError as e:
            print(f"An Aireloom error occurred during iteration: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during iteration: {e}")

if __name__ == "__main__":
    asyncio.run(iterate_all_projects())
```

## The `Project` Model

The `Project` Pydantic model (defined in `aireloom.models.project`) provides structured access to project data. Key attributes include:

*   `id` (str): The OpenAIRE ID of the project.
*   `code` (Optional[str]): Project code.
*   `acronym` (Optional[str]): Project acronym.
*   `title` (Optional[str]): Project title.
*   `callIdentifier` (Optional[str]): Call identifier.
*   `fundings` (Optional[list[Funding]]): List of funding information. Each `Funding` object contains:
    *   `fundingStream` (Optional[FundingStream]): Details like `id`, `description`.
    *   `jurisdiction` (Optional[str]).
    *   `name` (Optional[str]): Funder name.
    *   `shortName` (Optional[str]): Funder short name.
*   `granted` (Optional[Grant]): Grant details like `currency`, `fundedAmount`, `totalCost`.
*   `h2020Programmes` (Optional[list[H2020Programme]]): List of H2020 programme details.
*   `keywords` (Optional[list[str] | str]): List of keywords (or a single string).
*   `openAccessMandateForDataset` (Optional[bool]).
*   `openAccessMandateForPublications` (Optional[bool]).
*   `startDate` (Optional[str]): Project start date.
*   `endDate` (Optional[str]): Project end date.
*   `subjects` (Optional[list[str]]): List of subjects.
*   `summary` (Optional[str]): Project summary/abstract.
*   `websiteUrl` (Optional[str]): Project website URL.

Refer to the `aireloom.models.project.Project` model definition for all available fields.
