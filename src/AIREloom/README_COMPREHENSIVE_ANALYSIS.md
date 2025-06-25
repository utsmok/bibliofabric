# AIREloom Comprehensive Analysis Script

## Overview

This repository demonstrates a comprehensive data analysis pipeline using the AIREloom library to retrieve, analyze, and visualize OpenAIRE research data. The script performs an integrated workflow including:

- **Data Collection**: Retrieves research outputs from University of Twente (2024+)
- **Local Storage**: Stores data in an optimized DuckDB database
- **Comprehensive Analytics**: Generates detailed insights and visualizations
- **Executive Reporting**: Produces summary reports with actionable insights

## 🚀 Features

### Data Retrieval
- **Research Products**: Retrieves 4,824+ research outputs from University of Twente
- **Filtering**: Focuses on recent research (2024+) for current insights
- **Rate Limiting**: Implements courteous API usage with proper throttling
- **Progress Tracking**: Real-time progress indication using Rich progress bars

### Data Storage & Processing
- **DuckDB Integration**: High-performance local analytical database
- **Optimized Schema**: Structured tables for research outputs, projects, and relationships
- **Batch Processing**: Efficient data insertion with batch operations
- **Data Quality**: Comprehensive data validation and cleaning

### Analytics & Visualizations
- **Output Distribution Analysis**: Research type and temporal distribution
- **Author Collaboration Networks**: NetworkX-based collaboration analysis
- **Impact Metrics**: Citation analysis and influence scoring
- **Subject Area Analysis**: Research domain categorization and trends
- **Open Access Analysis**: Access rights and availability assessment
- **Temporal Trends**: Time-series analysis of research patterns

### Generated Outputs
- **Visualizations**: 3 high-quality PNG charts and graphs
- **Database**: 4.5MB DuckDB database with structured research data
- **Executive Summary**: Rich console table with key metrics and insights

## 📊 Key Results

From the University of Twente analysis:

- **Total Research Outputs**: 4,824 publications
- **Unique Researchers**: 20,697 active contributors
- **Data Quality Score**: 78.4% completeness
- **Average Collaboration Size**: High multi-author research
- **Research Productivity**: Active research environment

### Key Insights Generated:
- Strong collaborative culture with high average collaboration size
- Opportunity for increased research visibility and impact
- High research productivity indicating active research environment
- Potential for improved open access adoption

## 🛠️ Technical Implementation

### Dependencies
```toml
# Core dependencies
aireloom = "^1.0.0"
duckdb = "^1.2.0"
polars = "^1.0.0"
pyarrow = "^20.0.0"

# Visualization
matplotlib = "^3.10.0"
seaborn = "^0.13.0"
plotly = "^6.1.0"

# Analysis
pandas = "^2.3.0"
numpy = "^2.3.0"
networkx = "^3.5.0"

# CLI & Progress
rich = "^14.0.0"
python-dotenv = "^1.0.0"
requests = "^2.32.0"
```

### Architecture

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

**Research Outputs Table**:
- Comprehensive metadata (title, type, publication date)
- Author information (names, counts, affiliations)
- Impact metrics (citations, influence, popularity)
- Access rights and open access information
- Subject classifications and keywords

**Projects Table**:
- Project metadata and funding information
- Timeline and budget details
- Open access mandates

**Scholix Relationships Table**:
- Cross-references between research entities
- Relationship types and metadata

## 🔧 Usage

### Prerequisites
1. **Python Environment**: Python 3.11+ with uv package manager
2. **OpenAIRE Credentials**: Client ID and Secret from OpenAIRE
3. **Environment Setup**: Create `secrets.env` file

### Setup Instructions

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd AIREloom
   ```

2. **Create Environment File**:
   ```bash
   # secrets.env
   AIRELOOM_OPENAIRE_CLIENT_ID=your_client_id_here
   AIRELOOM_OPENAIRE_CLIENT_SECRET=your_client_secret_here
   ```

3. **Install Dependencies**:
   ```bash
   uv sync
   ```

4. **Run Analysis**:
   ```bash
   uv run aireloom_comprehensive_analysis.py
   ```

### Expected Runtime
- **Data Retrieval**: ~35-40 seconds (4,824 research outputs)
- **Analytics Generation**: ~3-5 seconds
- **Total Runtime**: ~40-45 seconds
- **Output Size**: ~4.5MB database + 3 visualization files

## 📈 Generated Outputs

### 1. Visualization Files
- `output_distribution_analysis.png` (463KB) - Research type and temporal distribution
- `temporal_trends_analysis.png` (393KB) - Time-series analysis and trends
- `subject_areas_analysis.png` (331KB) - Subject area categorization

### 2. Database
- `aireloom_analysis.db` (4.5MB) - Complete structured dataset

### 3. Console Output
- Real-time progress tracking
- Executive summary table
- Key insights and recommendations

## 🎯 Use Cases

### Research Institution Analysis
- **Performance Assessment**: Evaluate research output and impact
- **Collaboration Analysis**: Understand research networks and partnerships
- **Strategic Planning**: Identify research strengths and opportunities

### Funding Organization Insights
- **Portfolio Analysis**: Assess funded research outcomes
- **Impact Measurement**: Track citation and influence metrics
- **Policy Development**: Inform open access and collaboration policies

### Academic Benchmarking
- **Comparative Analysis**: Compare institutional performance
- **Trend Identification**: Spot emerging research areas
- **Quality Assessment**: Evaluate research completeness and accessibility

## 🔍 Advanced Features

### Customization Options
- **Institution Filtering**: Change target organization ID
- **Date Range**: Modify publication date filters
- **Output Limits**: Adjust maximum retrieval counts
- **Visualization Themes**: Customize chart styling

### Extensibility
- **Additional Metrics**: Add custom analysis functions
- **Export Formats**: Extend output options (CSV, JSON, etc.)
- **API Integrations**: Connect to other research databases
- **Reporting Templates**: Create automated report generation

## 🚨 Error Handling

The script includes comprehensive error handling:

- **API Rate Limiting**: Automatic throttling and retry logic
- **Data Validation**: Schema enforcement and data quality checks
- **Network Resilience**: Connection timeout and retry mechanisms
- **Resource Management**: Proper cleanup of database connections

## 📚 Technical Notes

### Performance Optimizations
- **Batch Processing**: Efficient data insertion (100 records per batch)
- **Cursor Pagination**: Memory-efficient data retrieval
- **Database Indexing**: Optimized query performance
- **Async Operations**: Non-blocking I/O for API calls

### Data Quality Features
- **Completeness Scoring**: Automated data quality assessment
- **Schema Validation**: Pydantic model enforcement
- **Null Handling**: Graceful handling of missing data
- **Type Coercion**: Automatic data type conversion

## 🤝 Contributing

This script demonstrates production-ready patterns for:
- Research data analysis pipelines
- API integration best practices
- Database optimization techniques
- Visualization generation workflows

## 📄 License

This project uses the AIREloom library and follows OpenAIRE data usage policies.

---

**Generated by AIREloom Comprehensive Analysis Script**
*Demonstrating advanced research data analytics with Python*
