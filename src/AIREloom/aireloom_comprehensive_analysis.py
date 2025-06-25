#!/usr/bin/env python3
"""
AIREloom Comprehensive Analysis Script

This script demonstrates advanced data retrieval, storage, and analysis capabilities
using the AIREloom library for OpenAIRE data. It performs an integrated workflow
including data collection, local storage with DuckDB, and comprehensive analytics.

Author: AIREloom Project
Requirements: Run with 'uv run aireloom_comprehensive_analysis.py'
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

import duckdb
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import polars as pl
from bibliofabric.exceptions import RateLimitError
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

# AIREloom imports
from aireloom import AireloomClient, Project, ResearchProduct
from aireloom.endpoints import ResearchProductsFilters, ScholixFilters

# Configure rich console and logging
console = Console()
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("aireloom_analysis")


class AIREloomAnalyzer:
    """
    Comprehensive analyzer for OpenAIRE data using AIREloom.

    Implements data retrieval, storage, and analysis pipeline with
    production-ready error handling and progress tracking.
    """

    client: AireloomClient
    db_conn: duckdb.DuckDBPyConnection

    def __init__(self, db_path: str = "aireloom_analysis.db"):
        """Initialize the analyzer with database connection."""
        self.db_path = db_path

        self.progress = None

        # Analysis results storage
        self.research_outputs: list[ResearchProduct] = []
        self.projects: list[Project] = []
        self.relationships: list[dict[str, Any]] = []

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize DuckDB database with optimized schema."""
        try:
            self.db_conn = duckdb.connect(self.db_path)

            # Create research outputs table
            self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS research_outputs (
                    id VARCHAR PRIMARY KEY,
                    title TEXT,
                    type VARCHAR,
                    publication_date DATE,
                    publisher TEXT,
                    description TEXT,
                    authors_count INTEGER,
                    authors_names TEXT[],
                    subjects TEXT[],
                    countries TEXT[],
                    citation_count INTEGER,
                    influence_score REAL,
                    popularity_score REAL,
                    downloads INTEGER,
                    views INTEGER,
                    access_right VARCHAR,
                    open_access_route VARCHAR,
                    keywords TEXT[],
                    language_code VARCHAR,
                    best_access_right_label VARCHAR,
                    collected_from_datasource TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create projects table
            self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id VARCHAR PRIMARY KEY,
                    code VARCHAR,
                    acronym VARCHAR,
                    title TEXT,
                    summary TEXT,
                    start_date DATE,
                    end_date DATE,
                    funded_amount REAL,
                    total_cost REAL,
                    currency VARCHAR,
                    funding_stream TEXT,
                    funder_name TEXT,
                    keywords TEXT[],
                    website_url TEXT,
                    open_access_mandate_publications BOOLEAN,
                    open_access_mandate_dataset BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create relationships table (for Scholix data)
            self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS scholix_relationships (
                    id INTEGER PRIMARY KEY,
                    source_pid VARCHAR,
                    target_pid VARCHAR,
                    source_type VARCHAR,
                    target_type VARCHAR,
                    source_title TEXT,
                    target_title TEXT,
                    relationship_type VARCHAR,
                    relationship_subtype VARCHAR,
                    source_publisher TEXT,
                    target_publisher TEXT,
                    link_publication_date TIMESTAMP,
                    harvest_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create analysis cache table for performance
            self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    cache_key VARCHAR PRIMARY KEY,
                    cache_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)

            logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def _init_client(self) -> None:
        """Initialize AIREloom client with authentication."""
        try:
            # Load environment variables from secrets.env
            load_dotenv("secrets.env")

            client_id = os.getenv("AIRELOOM_OPENAIRE_CLIENT_ID")
            client_secret = os.getenv("AIRELOOM_OPENAIRE_CLIENT_SECRET")

            if not client_id or not client_secret:
                raise ValueError("Missing OpenAIRE credentials in secrets.env")

            self.client = AireloomClient(
                client_id=client_id, client_secret=client_secret
            )

            logger.info("AIREloom client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AIREloom client: {e}")
            raise

    async def retrieve_research_outputs(self, max_items: int = 5000) -> int:
        """
        Retrieve research outputs from University of Twente (2024+).

        Args:
            max_items: Maximum number of items to retrieve

        Returns:
            Number of items successfully retrieved
        """
        try:
            # University of Twente OpenAIRE ID
            ut_openaire_id = "openorgs____::604881198363fedbb5d5478f465305f2"

            # Create filters for University of Twente research from 2024+
            filters = ResearchProductsFilters(
                relOrganizationId=ut_openaire_id,
                fromPublicationDate=datetime(2024, 1, 1).date(),
            )

            retrieved_count = 0
            batch_size = 100

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Retrieving research outputs...", total=max_items
                )

                # Use async iteration for efficient data retrieval
                async for research_output in self.client.research_products.iterate(
                    page_size=batch_size, filters=filters
                ):
                    if retrieved_count >= max_items:
                        break

                    self.research_outputs.append(research_output)
                    retrieved_count += 1

                    # Update progress
                    progress.update(task, advance=1)

                    # Implement rate limiting courtesy
                    if retrieved_count % batch_size == 0:
                        await asyncio.sleep(0.5)  # Brief pause between batches

                        # Store batch to database
                        await self._store_research_outputs_batch(
                            self.research_outputs[-batch_size:]
                        )

                # Store any remaining items
                if retrieved_count % batch_size != 0:
                    remaining_start = -(retrieved_count % batch_size)
                    await self._store_research_outputs_batch(
                        self.research_outputs[remaining_start:]
                    )

            logger.info(f"Successfully retrieved {retrieved_count} research outputs")
            return retrieved_count

        except RateLimitError as e:
            logger.warning(
                f"Rate limit encountered: {e}. Retrieved {retrieved_count} items."
            )
            return retrieved_count
        except Exception as e:
            logger.error(f"Failed to retrieve research outputs: {e}")
            raise

    async def _store_research_outputs_batch(self, batch: list[ResearchProduct]) -> None:
        """Store a batch of research outputs to database."""
        try:
            data = []
            for output in batch:
                # Extract author information
                authors_names = []
                authors_count = 0
                if output.authors:
                    authors_count = len(output.authors)
                    authors_names = [
                        author.fullName for author in output.authors if author.fullName
                    ]

                # Extract subjects
                subjects = []
                if output.subjects:
                    subjects = [
                        subj.subject.get("value", "") if subj.subject else ""
                        for subj in output.subjects
                    ]

                # Extract indicators
                citation_count = None
                influence_score = None
                popularity_score = None
                downloads = None
                views = None

                if output.indicators:
                    if output.indicators.citationImpact:
                        citation_count = output.indicators.citationImpact.citationCount
                        influence_score = output.indicators.citationImpact.influence
                        popularity_score = output.indicators.citationImpact.popularity

                    if output.indicators.usageCounts:
                        downloads = output.indicators.usageCounts.downloads
                        views = output.indicators.usageCounts.views

                # Extract access rights
                access_right = None
                open_access_route = None
                if output.bestAccessRight:
                    access_right = output.bestAccessRight.code

                # Parse publication date
                pub_date = None
                if output.publicationDate:
                    try:
                        pub_date = datetime.strptime(
                            output.publicationDate, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        try:
                            pub_date = datetime.strptime(
                                output.publicationDate, "%Y"
                            ).date()
                        except ValueError:
                            pass

                data.append(
                    {
                        "id": output.id,
                        "title": output.title,
                        "type": output.type,
                        "publication_date": pub_date,
                        "publisher": output.publisher,
                        "description": output.description,
                        "authors_count": authors_count,
                        "authors_names": authors_names,
                        "subjects": subjects,
                        "countries": [],  # Add missing field
                        "citation_count": citation_count,
                        "influence_score": influence_score,
                        "popularity_score": popularity_score,
                        "downloads": downloads,
                        "views": views,
                        "access_right": access_right,
                        "open_access_route": open_access_route,  # Add missing field
                        "keywords": output.keywords or [],
                        "language_code": output.language.code
                        if output.language
                        else None,
                        "best_access_right_label": output.bestAccessRight.label
                        if output.bestAccessRight
                        else None,
                        "collected_from_datasource": None,  # Add missing field
                        "created_at": None,  # DuckDB will auto-populate
                    }
                )

            # Convert to Polars DataFrame for efficient insertion
            df = pl.DataFrame(data)

            # Insert into DuckDB
            self.db_conn.execute("""
                INSERT OR REPLACE INTO research_outputs
                SELECT * FROM df
            """)

        except Exception as e:
            logger.error(f"Failed to store research outputs batch: {e}")
            raise

    async def map_projects_via_scholix(self) -> int:
        """
        Map projects connected to research outputs via Scholix API.

        Returns:
            Number of project relationships discovered
        """
        try:
            relationships_found = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Mapping project relationships...", total=len(self.research_outputs)
                )

                for output in self.research_outputs:
                    if not output.pids:
                        progress.update(task, advance=1)
                        continue

                    # Try to find relationships using PIDs
                    for pid in output.pids:
                        if not pid.id or not pid.id.value:
                            continue

                        try:
                            # Search for relationships where this output is the source
                            filters = ScholixFilters(sourcePid=pid.id.value)

                            # Limited search to avoid overwhelming the API
                            async for relationship in self.client.scholix.iterate_links(
                                page_size=10, filters=filters
                            ):
                                await self._process_scholix_relationship(relationship)
                                relationships_found += 1

                                # Limit to prevent excessive API calls
                                if relationships_found % 50 == 0:
                                    await asyncio.sleep(1)

                        except Exception as e:
                            logger.debug(
                                f"Scholix lookup failed for {pid.id.value}: {e}"
                            )
                            continue

                    progress.update(task, advance=1)

            logger.info(f"Discovered {relationships_found} project relationships")
            return relationships_found

        except Exception as e:
            logger.error(f"Failed to map projects via Scholix: {e}")
            raise

    async def _process_scholix_relationship(self, relationship) -> None:
        """Process and store a Scholix relationship."""
        try:
            # Extract relationship data
            rel_data = {
                "source_pid": relationship.source.identifier[0].id_val
                if relationship.source.identifier
                else None,
                "target_pid": relationship.target.identifier[0].id_val
                if relationship.target.identifier
                else None,
                "source_type": relationship.source.type,
                "target_type": relationship.target.type,
                "source_title": relationship.source.title,
                "target_title": relationship.target.title,
                "relationship_type": relationship.relationship_type.name,
                "relationship_subtype": relationship.relationship_type.sub_type,
                "source_publisher": relationship.source.publisher[0].name
                if relationship.source.publisher
                else None,
                "target_publisher": relationship.target.publisher[0].name
                if relationship.target.publisher
                else None,
                "link_publication_date": relationship.link_publication_date,
                "harvest_date": relationship.harvest_date,
            }

            self.relationships.append(rel_data)

            # Store to database
            self.db_conn.execute(
                """
                INSERT INTO scholix_relationships
                (source_pid, target_pid, source_type, target_type, source_title, target_title,
                 relationship_type, relationship_subtype, source_publisher, target_publisher,
                 link_publication_date, harvest_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    rel_data["source_pid"],
                    rel_data["target_pid"],
                    rel_data["source_type"],
                    rel_data["target_type"],
                    rel_data["source_title"],
                    rel_data["target_title"],
                    rel_data["relationship_type"],
                    rel_data["relationship_subtype"],
                    rel_data["source_publisher"],
                    rel_data["target_publisher"],
                    rel_data["link_publication_date"],
                    rel_data["harvest_date"],
                ],
            )

        except Exception as e:
            logger.error(f"Failed to process Scholix relationship: {e}")

    def generate_comprehensive_analytics(self) -> dict[str, Any]:
        """
        Generate comprehensive analytics from collected data.

        Returns:
            Dictionary containing all analysis results
        """
        analytics = {}

        try:
            logger.info("Generating comprehensive analytics...")

            # 1. Research Output Distribution Analysis
            analytics["output_distribution"] = self._analyze_output_distribution()

            # 2. Author Productivity and Collaboration Analysis
            analytics["author_analysis"] = self._analyze_author_patterns()

            # 3. Temporal Trends Analysis
            analytics["temporal_trends"] = self._analyze_temporal_trends()

            # 4. Subject Area Analysis
            analytics["subject_analysis"] = self._analyze_subject_areas()

            # 5. Impact and Citation Analysis
            analytics["impact_analysis"] = self._analyze_impact_metrics()

            # 6. Access Rights and Open Access Analysis
            analytics["access_analysis"] = self._analyze_access_patterns()

            # 7. Network Analysis
            analytics["network_analysis"] = self._analyze_collaboration_networks()

            # 8. Comparative Benchmarking
            analytics["benchmarking"] = self._generate_benchmarking_insights()

            logger.info("Analytics generation completed")
            return analytics

        except Exception as e:
            logger.error(f"Failed to generate analytics: {e}")
            raise

    def _analyze_output_distribution(self) -> dict[str, Any]:
        """Analyze research output distribution across types and years."""
        try:
            # Query data from database
            df = self.db_conn.execute("""
                SELECT
                    type,
                    EXTRACT(YEAR FROM publication_date) as year,
                    COUNT(*) as count,
                    AVG(citation_count) as avg_citations,
                    AVG(influence_score) as avg_influence
                FROM research_outputs
                WHERE publication_date IS NOT NULL
                GROUP BY type, year
                ORDER BY year DESC, count DESC
            """).df()

            # Create visualizations
            self._create_output_distribution_plots(df)

            return {
                "by_type": df.groupby("type")["count"].sum().to_dict(),
                "by_year": df.groupby("year")["count"].sum().to_dict(),
                "detailed_breakdown": df.to_dict("records"),
            }

        except Exception as e:
            logger.error(f"Failed to analyze output distribution: {e}")
            return {}

    def _create_output_distribution_plots(self, df) -> None:
        """Create visualizations for output distribution."""
        try:
            # Set up the plotting style
            plt.style.use("seaborn-v0_8")
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

            # 1. Output types distribution
            type_counts = df.groupby("type")["count"].sum()
            ax1.pie(type_counts.values, labels=type_counts.index, autopct="%1.1f%%")
            ax1.set_title("Research Output Types Distribution")

            # 2. Yearly publication trends
            yearly_counts = df.groupby("year")["count"].sum()
            ax2.plot(yearly_counts.index, yearly_counts.values, marker="o")
            ax2.set_title("Publication Trends Over Time")
            ax2.set_xlabel("Year")
            ax2.set_ylabel("Number of Publications")

            # 3. Citation distribution by type
            citation_data = df.dropna(subset=["avg_citations"])
            if not citation_data.empty:
                citation_data.boxplot(column="avg_citations", by="type", ax=ax3)
                ax3.set_title("Citation Distribution by Type")
                ax3.set_xlabel("Research Output Type")
                ax3.set_ylabel("Average Citations")

            # 4. Influence score trends
            influence_data = df.dropna(subset=["avg_influence"])
            if not influence_data.empty:
                for output_type in influence_data["type"].unique():
                    type_data = influence_data[influence_data["type"] == output_type]
                    ax4.plot(
                        type_data["year"],
                        type_data["avg_influence"],
                        label=output_type,
                        marker="o",
                    )
                ax4.set_title("Influence Score Trends by Type")
                ax4.set_xlabel("Year")
                ax4.set_ylabel("Average Influence Score")
                ax4.legend()

            plt.tight_layout()
            plt.savefig(
                "output_distribution_analysis.png", dpi=300, bbox_inches="tight"
            )
            plt.close()

        except Exception as e:
            logger.error(f"Failed to create distribution plots: {e}")

    def _analyze_author_patterns(self) -> dict[str, Any]:
        """Analyze author productivity and collaboration patterns."""
        try:
            # Query author data
            df = self.db_conn.execute("""
                SELECT
                    UNNEST(authors_names) as author_name,
                    authors_count,
                    citation_count,
                    influence_score,
                    type,
                    publication_date
                FROM research_outputs
                WHERE authors_names IS NOT NULL AND array_length(authors_names) > 0
            """).df()

            if df.empty:
                return {"message": "No author data available"}

            # Calculate productivity metrics
            author_productivity = (
                df.groupby("author_name")
                .agg(
                    {
                        "author_name": "count",  # Number of publications
                        "citation_count": ["mean", "sum"],
                        "influence_score": "mean",
                    }
                )
                .round(2)
            )

            author_productivity.columns = [
                "publications",
                "avg_citations",
                "total_citations",
                "avg_influence",
            ]

            # Collaboration analysis
            collaboration_analysis = df.groupby("authors_count").size()

            return {
                "top_authors": author_productivity.nlargest(20, "publications").to_dict(
                    "index"
                ),
                "collaboration_distribution": collaboration_analysis.to_dict(),
                "average_collaboration_size": df["authors_count"].mean(),
                "total_unique_authors": df["author_name"].nunique(),
            }

        except Exception as e:
            logger.error(f"Failed to analyze author patterns: {e}")
            return {}

    def _analyze_temporal_trends(self) -> dict[str, Any]:
        """Analyze temporal trends in research output and impact."""
        try:
            df = self.db_conn.execute("""
                SELECT
                    EXTRACT(YEAR FROM publication_date) as year,
                    EXTRACT(MONTH FROM publication_date) as month,
                    COUNT(*) as count,
                    AVG(citation_count) as avg_citations,
                    AVG(influence_score) as avg_influence,
                    AVG(popularity_score) as avg_popularity,
                    AVG(downloads) as avg_downloads,
                    AVG(views) as avg_views
                FROM research_outputs
                WHERE publication_date IS NOT NULL
                GROUP BY year, month
                ORDER BY year, month
            """).df()

            if df.empty:
                return {"message": "No temporal data available"}

            # Create temporal trend visualization
            self._create_temporal_plots(df)

            return {
                "yearly_trends": df.groupby("year")
                .agg({"count": "sum", "avg_citations": "mean", "avg_influence": "mean"})
                .to_dict("index"),
                "peak_publication_year": df.groupby("year")["count"].sum().idxmax(),
                "trend_analysis": "Generated temporal trend plots",
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal trends: {e}")
            return {}

    def _create_temporal_plots(self, df) -> None:
        """Create temporal trend visualizations."""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

            # 1. Monthly publication trends
            monthly_data = df.groupby(["year", "month"])["count"].sum().reset_index()
            monthly_data["date"] = pd.to_datetime(
                monthly_data[["year", "month"]].assign(day=1)
            )
            ax1.plot(monthly_data["date"], monthly_data["count"])
            ax1.set_title("Monthly Publication Trends")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Number of Publications")

            # 2. Citation trends over time
            citation_data = df.dropna(subset=["avg_citations"])
            if not citation_data.empty:
                ax2.scatter(
                    citation_data["year"], citation_data["avg_citations"], alpha=0.6
                )
                z = np.polyfit(citation_data["year"], citation_data["avg_citations"], 1)
                p = np.poly1d(z)
                ax2.plot(
                    citation_data["year"], p(citation_data["year"]), "r--", alpha=0.8
                )
                ax2.set_title("Citation Trends Over Time")
                ax2.set_xlabel("Year")
                ax2.set_ylabel("Average Citations")

            # 3. Influence score trends
            influence_data = df.dropna(subset=["avg_influence"])
            if not influence_data.empty:
                ax3.scatter(
                    influence_data["year"], influence_data["avg_influence"], alpha=0.6
                )
                ax3.set_title("Influence Score Trends")
                ax3.set_xlabel("Year")
                ax3.set_ylabel("Average Influence Score")

            # 4. Usage metrics trends
            usage_data = df.dropna(subset=["avg_downloads", "avg_views"])
            if not usage_data.empty:
                ax4_twin = ax4.twinx()
                ax4.bar(
                    usage_data["year"],
                    usage_data["avg_downloads"],
                    alpha=0.7,
                    label="Downloads",
                )
                ax4_twin.bar(
                    usage_data["year"],
                    usage_data["avg_views"],
                    alpha=0.7,
                    label="Views",
                    color="orange",
                )
                ax4.set_title("Usage Metrics Trends")
                ax4.set_xlabel("Year")
                ax4.set_ylabel("Average Downloads")
                ax4_twin.set_ylabel("Average Views")
                ax4.legend(loc="upper left")
                ax4_twin.legend(loc="upper right")

            plt.tight_layout()
            plt.savefig("temporal_trends_analysis.png", dpi=300, bbox_inches="tight")
            plt.close()

        except Exception as e:
            logger.error(f"Failed to create temporal plots: {e}")

    def _analyze_subject_areas(self) -> dict[str, Any]:
        """Analyze research across subject areas."""
        try:
            # Query subject data
            # Note: DuckDB UNNEST syntax is different, so we'll use a different approach
            df = self.db_conn.execute("""
                SELECT
                    subject_item as subject,
                    COUNT(*) as count,
                    AVG(citation_count) as avg_citations,
                    AVG(influence_score) as avg_influence
                FROM (
                    SELECT
                        UNNEST(subjects) as subject_item,
                        citation_count,
                        influence_score
                    FROM research_outputs
                    WHERE subjects IS NOT NULL AND len(subjects) > 0
                )
                GROUP BY subject_item
                HAVING COUNT(*) >= 2
                ORDER BY count DESC
                LIMIT 50
            """).df()

            if df.empty:
                return {"message": "No subject data available"}

            # Create subject area visualization
            self._create_subject_plots(df)

            return {
                "top_subjects": df.head(20).to_dict("records"),
                "subject_distribution": df["count"].describe().to_dict(),
                "high_impact_subjects": df.nlargest(10, "avg_influence")[
                    ["subject", "avg_influence"]
                ].to_dict("records"),
            }

        except Exception as e:
            logger.error(f"Failed to analyze subject areas: {e}")
            return {}

    def _create_subject_plots(self, df) -> None:
        """Create subject area visualizations."""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

            # 1. Top subjects by publication count
            top_subjects = df.head(15)
            ax1.barh(range(len(top_subjects)), top_subjects["count"])
            ax1.set_yticks(range(len(top_subjects)))
            ax1.set_yticklabels(
                [s[:50] + "..." if len(s) > 50 else s for s in top_subjects["subject"]]
            )
            ax1.set_xlabel("Number of Publications")
            ax1.set_title("Top 15 Subject Areas by Publication Count")

            # 2. Subject areas by impact (influence score)
            impact_subjects = df.dropna(subset=["avg_influence"]).nlargest(
                15, "avg_influence"
            )
            ax2.barh(range(len(impact_subjects)), impact_subjects["avg_influence"])
            ax2.set_yticks(range(len(impact_subjects)))
            ax2.set_yticklabels(
                [
                    s[:50] + "..." if len(s) > 50 else s
                    for s in impact_subjects["subject"]
                ]
            )
            ax2.set_xlabel("Average Influence Score")
            ax2.set_title("Top 15 Subject Areas by Impact")

            plt.tight_layout()
            plt.savefig("subject_areas_analysis.png", dpi=300, bbox_inches="tight")
            plt.close()

        except Exception as e:
            logger.error(f"Failed to create subject plots: {e}")

    def _analyze_impact_metrics(self) -> dict[str, Any]:
        """Analyze impact metrics and citation patterns."""
        try:
            df = self.db_conn.execute("""
                SELECT
                    citation_count,
                    influence_score,
                    popularity_score,
                    downloads,
                    views,
                    type,
                    publication_date,
                    EXTRACT(YEAR FROM publication_date) as year
                FROM research_outputs
                WHERE citation_count IS NOT NULL
                   OR influence_score IS NOT NULL
                   OR downloads IS NOT NULL
            """).df()

            if df.empty:
                return {"message": "No impact data available"}

            # Calculate impact statistics
            impact_stats = {
                "citation_stats": df["citation_count"].describe().to_dict(),
                "influence_stats": df["influence_score"].describe().to_dict(),
                "usage_stats": {
                    "downloads": df["downloads"].describe().to_dict(),
                    "views": df["views"].describe().to_dict(),
                },
            }

            # High-impact publications
            high_impact = df.nlargest(20, "citation_count")[
                ["citation_count", "influence_score", "type"]
            ].to_dict("records")

            return {
                "impact_statistics": impact_stats,
                "high_impact_outputs": high_impact,
                "correlation_analysis": self._calculate_impact_correlations(df),
            }

        except Exception as e:
            logger.error(f"Failed to analyze impact metrics: {e}")
            return {}

    def _calculate_impact_correlations(self, df) -> dict[str, float]:
        """Calculate correlations between different impact metrics."""
        try:
            numeric_cols = [
                "citation_count",
                "influence_score",
                "popularity_score",
                "downloads",
                "views",
            ]
            available_cols = [
                col
                for col in numeric_cols
                if col in df.columns and not df[col].isna().all()
            ]

            if len(available_cols) < 2:
                return {}

            correlation_matrix = df[available_cols].corr()

            # Extract meaningful correlations
            correlations = {}
            for i, col1 in enumerate(available_cols):
                for j, col2 in enumerate(available_cols[i + 1 :], i + 1):
                    corr_value = correlation_matrix.loc[col1, col2]
                    if not pd.isna(corr_value):
                        correlations[f"{col1}_vs_{col2}"] = round(corr_value, 3)

            return correlations

        except Exception as e:
            logger.error(f"Failed to calculate correlations: {e}")
            return {}

    def _analyze_access_patterns(self) -> dict[str, Any]:
        """Analyze open access patterns and availability."""
        try:
            df = self.db_conn.execute("""
                SELECT
                    access_right,
                    best_access_right_label,
                    COUNT(*) as count,
                    AVG(citation_count) as avg_citations,
                    EXTRACT(YEAR FROM publication_date) as year
                FROM research_outputs
                WHERE access_right IS NOT NULL
                GROUP BY access_right, best_access_right_label, year
                ORDER BY count DESC
            """).df()

            if df.empty:
                return {"message": "No access rights data available"}

            access_distribution = df.groupby("access_right")["count"].sum().to_dict()
            yearly_access_trends = (
                df.groupby(["year", "access_right"])["count"]
                .sum()
                .unstack(fill_value=0)
                .to_dict("index")
            )

            return {
                "access_distribution": access_distribution,
                "yearly_trends": yearly_access_trends,
                "open_access_percentage": self._calculate_open_access_percentage(df),
            }

        except Exception as e:
            logger.error(f"Failed to analyze access patterns: {e}")
            return {}

    def _calculate_open_access_percentage(self, df) -> float:
        """Calculate the percentage of open access publications."""
        try:
            total_publications = df["count"].sum()
            if total_publications == 0:
                return 0.0

            # Common open access indicators
            open_access_codes = [
                "open",
                "openAccess",
                "OPEN",
                "gold",
                "green",
                "hybrid",
            ]
            open_access_count = df[df["access_right"].isin(open_access_codes)][
                "count"
            ].sum()

            return round((open_access_count / total_publications) * 100, 2)

        except Exception as e:
            logger.error(f"Failed to calculate open access percentage: {e}")
            return 0.0

    def _analyze_collaboration_networks(self) -> dict[str, Any]:
        """Analyze collaboration networks using NetworkX."""
        try:
            # Query collaboration data
            df = self.db_conn.execute("""
                SELECT
                    authors_names,
                    authors_count,
                    citation_count,
                    type
                FROM research_outputs
                WHERE authors_names IS NOT NULL
                  AND array_length(authors_names) > 1
                  AND array_length(authors_names) <= 10  -- Limit for computational efficiency
            """).df()

            if df.empty:
                return {"message": "No collaboration data available"}

            # Build collaboration network
            G = nx.Graph()

            for _, row in df.iterrows():
                authors = row["authors_names"]
                if len(authors) > 1:
                    # Add edges between all pairs of authors
                    for i in range(len(authors)):
                        for j in range(i + 1, len(authors)):
                            if G.has_edge(authors[i], authors[j]):
                                G[authors[i]][authors[j]]["weight"] += 1
                            else:
                                G.add_edge(authors[i], authors[j], weight=1)

            if G.number_of_nodes() == 0:
                return {"message": "No collaboration network could be built"}

            # Calculate network metrics
            network_metrics = {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "density": nx.density(G),
                "average_clustering": nx.average_clustering(G),
                "connected_components": nx.number_connected_components(G),
            }

            # Find top collaborators
            degree_centrality = nx.degree_centrality(G)
            top_collaborators = sorted(
                degree_centrality.items(), key=lambda x: x[1], reverse=True
            )[:20]

            return {
                "network_metrics": network_metrics,
                "top_collaborators": [
                    {"author": author, "centrality": centrality}
                    for author, centrality in top_collaborators
                ],
                "analysis_summary": "Collaboration network analysis completed",
            }

        except Exception as e:
            logger.error(f"Failed to analyze collaboration networks: {e}")
            return {}

    def _generate_benchmarking_insights(self) -> dict[str, Any]:
        """Generate comparative benchmarking insights."""
        try:
            # Calculate key performance indicators
            total_outputs = len(self.research_outputs)

            # Research output metrics
            # First get basic metrics
            df = self.db_conn.execute("""
                SELECT
                    COUNT(*) as total_outputs,
                    COUNT(DISTINCT EXTRACT(YEAR FROM publication_date)) as active_years,
                    AVG(citation_count) as avg_citations,
                    AVG(influence_score) as avg_influence,
                    AVG(authors_count) as avg_collaboration_size
                FROM research_outputs
            """).fetchone()

            # Get unique authors count separately
            unique_authors = self.db_conn.execute("""
                SELECT COUNT(DISTINCT author_name) as unique_authors
                FROM (
                    SELECT UNNEST(authors_names) as author_name
                    FROM research_outputs
                    WHERE authors_names IS NOT NULL AND len(authors_names) > 0
                )
            """).fetchone()

            # Combine results
            df = list(df) + [unique_authors[0] if unique_authors else 0]

            # Access rights analysis
            access_df = self.db_conn.execute("""
                SELECT
                    access_right,
                    COUNT(*) as count
                FROM research_outputs
                WHERE access_right IS NOT NULL
                GROUP BY access_right
            """).df()

            # Calculate productivity metrics
            productivity_metrics = {
                "total_research_outputs": total_outputs,
                "average_citations_per_output": round(df[2] or 0, 2),
                "average_influence_score": round(df[3] or 0, 3),
                "average_collaboration_size": round(df[4] or 0, 1),
                "unique_researchers": df[5] or 0,
                "research_active_years": df[1] or 0,
            }

            # Generate insights and recommendations
            insights = self._generate_insights(productivity_metrics, access_df)

            return {
                "productivity_metrics": productivity_metrics,
                "benchmarking_insights": insights,
                "data_quality_score": self._calculate_data_quality_score(),
            }

        except Exception as e:
            logger.error(f"Failed to generate benchmarking insights: {e}")
            return {}

    def _generate_insights(self, metrics: dict[str, Any], access_df) -> list[str]:
        """Generate actionable insights from the analysis."""
        insights = []

        try:
            # Productivity insights
            if metrics["average_citations_per_output"] > 10:
                insights.append(
                    "High-impact research: Average citations per output exceeds 10, indicating strong research quality."
                )
            elif metrics["average_citations_per_output"] < 3:
                insights.append(
                    "Consider strategies to increase research visibility and impact."
                )

            # Collaboration insights
            if metrics["average_collaboration_size"] > 5:
                insights.append(
                    "Strong collaborative culture: High average collaboration size indicates good research partnerships."
                )
            elif metrics["average_collaboration_size"] < 2:
                insights.append(
                    "Opportunity for increased collaboration: Consider fostering more multi-author research projects."
                )

            # Open access insights
            if not access_df.empty:
                total_with_access_info = access_df["count"].sum()
                open_access_indicators = ["open", "openAccess", "OPEN"]
                open_access_count = access_df[
                    access_df["access_right"].isin(open_access_indicators)
                ]["count"].sum()

                if total_with_access_info > 0:
                    oa_percentage = (open_access_count / total_with_access_info) * 100
                    if oa_percentage > 50:
                        insights.append(
                            f"Excellent open access adoption: {oa_percentage:.1f}% of research outputs are openly accessible."
                        )
                    else:
                        insights.append(
                            f"Open access opportunity: Only {oa_percentage:.1f}% of outputs are open access. Consider institutional OA policies."
                        )

            # Research volume insights
            if metrics["total_research_outputs"] > 1000:
                insights.append(
                    "High research productivity: Large volume of research outputs demonstrates active research environment."
                )

            return insights

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return [
                "Analysis completed with some limitations due to data processing errors."
            ]

    def _calculate_data_quality_score(self) -> float:
        """Calculate a data quality score based on completeness."""
        try:
            df = self.db_conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(title) as has_title,
                    COUNT(publication_date) as has_date,
                    COUNT(authors_names) as has_authors,
                    COUNT(citation_count) as has_citations,
                    COUNT(subjects) as has_subjects
                FROM research_outputs
            """).fetchone()

            if df[0] == 0:  # total count
                return 0.0

            total = df[0]
            completeness_score = (
                (df[1] / total) * 0.2  # title
                + (df[2] / total) * 0.2  # date
                + (df[3] / total) * 0.2  # authors
                + (df[4] / total) * 0.2  # citations
                + (df[5] / total) * 0.2  # subjects
            ) * 100

            return round(completeness_score, 1)

        except Exception as e:
            logger.error(f"Failed to calculate data quality score: {e}")
            return 0.0

    def generate_executive_summary(self, analytics: dict[str, Any]) -> None:
        """Generate an executive summary report."""
        try:
            summary_table = Table(
                title="AIREloom Analysis Executive Summary",
                show_header=True,
                header_style="bold blue",
            )
            summary_table.add_column("Metric", style="cyan", no_wrap=True)
            summary_table.add_column("Value", style="magenta")
            summary_table.add_column("Insight", style="green")

            # Key metrics
            total_outputs = len(self.research_outputs)
            total_relationships = len(self.relationships)

            summary_table.add_row(
                "Total Research Outputs",
                str(total_outputs),
                "Data collection successful",
            )
            summary_table.add_row(
                "Scholix Relationships",
                str(total_relationships),
                "Cross-reference mapping completed",
            )

            # Add analytics insights
            if (
                "benchmarking" in analytics
                and "productivity_metrics" in analytics["benchmarking"]
            ):
                metrics = analytics["benchmarking"]["productivity_metrics"]
                summary_table.add_row(
                    "Avg Citations/Output",
                    str(metrics.get("average_citations_per_output", "N/A")),
                    "Research impact indicator",
                )
                summary_table.add_row(
                    "Unique Researchers",
                    str(metrics.get("unique_researchers", "N/A")),
                    "Research community size",
                )
                summary_table.add_row(
                    "Data Quality Score",
                    f"{analytics['benchmarking'].get('data_quality_score', 0)}%",
                    "Completeness assessment",
                )

            console.print("\n")
            console.print(summary_table)

            # Print key insights
            if (
                "benchmarking" in analytics
                and "benchmarking_insights" in analytics["benchmarking"]
            ):
                console.print("\n[bold blue]Key Insights:[/bold blue]")
                for insight in analytics["benchmarking"]["benchmarking_insights"]:
                    console.print(f"• {insight}")

            # Performance summary
            console.print("\n[bold green]Analysis completed successfully![/bold green]")
            console.print(f"Database: {self.db_path}")
            console.print(
                "Generated visualizations: output_distribution_analysis.png, temporal_trends_analysis.png, subject_areas_analysis.png"
            )

        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")

    async def run_comprehensive_analysis(self) -> None:
        """Run the complete analysis pipeline."""
        start_time = time.time()

        try:
            console.print(
                "[bold blue]🚀 Starting AIREloom Comprehensive Analysis[/bold blue]"
            )

            # 1. Initialize client
            await self._init_client()

            # 2. Retrieve research outputs
            console.print("\n[yellow]📚 Retrieving research outputs...[/yellow]")
            retrieved_count = await self.retrieve_research_outputs(max_items=5000)

            if retrieved_count == 0:
                console.print("[red]No research outputs retrieved. Exiting.[/red]")
                return

            # 3. Map project relationships via Scholix
            console.print("\n[yellow]🔗 Mapping project relationships...[/yellow]")
            relationships_count = await self.map_projects_via_scholix()

            # 4. Generate comprehensive analytics
            console.print("\n[yellow]📊 Generating analytics...[/yellow]")
            analytics = self.generate_comprehensive_analytics()

            # 5. Generate executive summary
            console.print("\n[yellow]📋 Generating executive summary...[/yellow]")
            self.generate_executive_summary(analytics)

            # Performance metrics
            elapsed_time = time.time() - start_time
            console.print(
                f"\n[bold green]✅ Analysis completed in {elapsed_time:.2f} seconds[/bold green]"
            )

        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}")
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            raise

        finally:
            # Cleanup
            if self.client:
                await self.client.aclose()
            if self.db_conn:
                self.db_conn.close()


async def main():
    """Main entry point for the analysis script."""
    try:
        # Import pandas and numpy here to handle potential import issues
        import numpy as np
        import pandas as pd

        # Create and run analyzer
        analyzer = AIREloomAnalyzer()
        await analyzer.run_comprehensive_analysis()

    except ImportError as e:
        console.print(f"[red]Missing required dependency: {e}[/red]")
        console.print(
            "[yellow]Please install missing packages using: uv add <package_name>[/yellow]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we're running with the correct Python environment
    if "uv" not in sys.executable and "UV_PROJECT_ROOT" not in os.environ:
        console.print(
            "[yellow]⚠️  This script should be run with 'uv run aireloom_comprehensive_analysis.py'[/yellow]"
        )

    # Run the analysis
    asyncio.run(main())
