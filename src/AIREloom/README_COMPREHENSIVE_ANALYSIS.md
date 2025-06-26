# AIREloom example analysis script


`aireloom_comprehensive_analysis.py` demonstrates the `AIREloom` package by executing a data analysis pipeline using the AIREloom library to retrieve, analyze, and visualize OpenAIRE research data. The script performs an integrated workflow including:

- Data collection: Retrieves research outputs published 2024 and later by University of Twente authors
- Local storage: Stores data in an optimized DuckDB database
- Analytics: Generates detailed insights and visualizations
- Reporting: Produces summary reports with actionable insights


## 🛠️ Technical Implementation

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAIRE API  │───▶│  AIREloom Client │───▶│   Data Storage  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Visualizations │◀───│     Analytics    │◀───│   DuckDB Local  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Database Schema

Research Outputs:
- Comprehensive metadata (title, type, publication date)
- Author information (names, counts, affiliations)
- Impact metrics (citations, influence, popularity)
- Access rights and open access information
- Subject classifications and keywords

Projects:
- Project metadata and funding information
- Timeline and budget details
- Open access mandates

Scholix Relationships:
- Cross-references between research entities
- Relationship types and metadata

## Usage

### Prerequisites

1. `uv` installed to manage python
2. [optional] `OpenAIRE` credentials: Client ID and Secret from OpenAIRE stored in a `secrets.env` file for higher rate limits

### Setup & run

1. Clone and setup:
   ```bash
   git clone <repository>
   cd AIREloom
   ```

2. [OPTIONAL] Create environment file:
   ```bash
   # secrets.env
   AIRELOOM_OPENAIRE_CLIENT_ID=your_client_id_here
   AIRELOOM_OPENAIRE_CLIENT_SECRET=your_client_secret_here
   ```

3. Run analysis:
   ```bash
   uv run aireloom_comprehensive_analysis.py
   ```

## Results

### Runtime

- retrieval: ~35-40 seconds (4,824 research outputs)
- analysis: ~3-5 seconds
- total: ~40-45 seconds

### Outputs

Files:
- `output_distribution_analysis.png` - Research type and temporal distribution
- `temporal_trends_analysis.png`  - Time-series analysis and trends
- `subject_areas_analysis.png` - Subject area categorization
- `aireloom_analysis.db` (~4.5MB) - Complete structured dataset


Console output:
- Real-time progress tracking
- Executive summary table
- Key insights and recommendations


## Script overview

The script includes comprehensive error handling:

- Automatic throttling and retry logic
- Schema enforcement and data quality checks
- Connection timeout and retry mechanisms
- Proper cleanup of database connections

And includes these considerations for performance:
- Efficient data insertion (100 records per batch)
- Memory-efficient data retrieval using cursor indexing
- Optimized query performance w/ indexed sql db
- Async, non-blocking I/O for API calls

