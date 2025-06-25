#!/usr/bin/env python3
"""
Simple AIREloom Usage Example

This script demonstrates basic usage of the AIREloom library
for retrieving and analyzing OpenAIRE research data.

Run with: uv run simple_example.py
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from aireloom import AireloomClient
from aireloom.endpoints import ResearchProductsFilters

console = Console()


async def main():
    """Demonstrate basic AIREloom usage."""
    console.print("[bold blue]🚀 AIREloom Simple Example[/bold blue]")

    # Load credentials
    load_dotenv("secrets.env")
    client_id = os.getenv("AIRELOOM_OPENAIRE_CLIENT_ID")
    client_secret = os.getenv("AIRELOOM_OPENAIRE_CLIENT_SECRET")

    if not client_id or not client_secret:
        console.print("[red]❌ Missing credentials in secrets.env[/red]")
        return

    # Initialize client
    async with AireloomClient(
        client_id=client_id, client_secret=client_secret
    ) as client:
        # Example 1: Get a single research product
        console.print("\n[yellow]📄 Example 1: Get single research product[/yellow]")
        try:
            product = await client.research_products.get(
                "doi_dedup__::0123456789abcdef"
            )
            console.print(f"Found: {product.title}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        # Example 2: Search research products
        console.print("\n[yellow]🔍 Example 2: Search research products[/yellow]")
        filters = ResearchProductsFilters(
            search="machine learning", fromPublicationDate=datetime(2024, 1, 1).date()
        )

        response = await client.research_products.search(
            page=1, page_size=5, filters=filters
        )

        total_results = getattr(response.header, "total", len(response.results or []))
        console.print(f"Found {total_results} total results")

        # Display results in a table
        table = Table(title="Recent Machine Learning Research")
        table.add_column("Title", style="cyan", max_width=50)
        table.add_column("Type", style="magenta")
        table.add_column("Date", style="green")

        results = response.results or []
        for product in results[:5]:
            title = product.title or "No title"
            title_display = title[:47] + "..." if len(title) > 50 else title
            table.add_row(
                title_display,
                product.type or "Unknown",
                product.publicationDate or "N/A",
            )

        console.print(table)

        # Example 3: Iterate through all results (limited)
        console.print("\n[yellow]🔄 Example 3: Iterate through results[/yellow]")
        count = 0
        async for product in client.research_products.iterate(
            page_size=10, filters=filters
        ):
            count += 1
            if count <= 3:  # Limit for demo
                title = product.title or "No title"
                console.print(f"  {count}. {title[:60]}...")
            if count >= 10:  # Stop after 10 for demo
                break

        console.print(f"Processed {count} research products")

        # Example 4: Get project information
        console.print("\n[yellow]📊 Example 4: Search projects[/yellow]")
        try:
            projects = await client.projects.search(page_size=3)
            total_projects = getattr(
                projects.header, "total", len(projects.results or [])
            )
            console.print(f"Found {total_projects} total projects")

            project_results = projects.results or []
            for project in project_results[:3]:
                console.print(f"  • {project.title or 'No title'}")
        except Exception as e:
            console.print(f"[red]Error fetching projects: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
