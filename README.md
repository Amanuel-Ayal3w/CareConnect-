# CareConnect - Healthcare Intelligence Platform

A clean, professional healthcare intelligence platform for identifying medical deserts and analyzing healthcare coverage in Ghana.

## Features

- **Dashboard**: Overview of healthcare facilities and NGOs with key metrics
- **Facility Search**: Search and filter organizations by name, type, and location
- **Map View**: Geographic distribution of healthcare resources
- **Analytics**: In-depth analysis of specialties, capacity, and regional coverage

## Quick Start

### Installation

Install dependencies with UV:
```bash
uv sync --no-install-project
```

### Running the Application

```bash
uv run streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Data

The application uses the Virtue Foundation Ghana v0.3 dataset containing healthcare facilities and NGO information.

## Technology Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly, Folium
- **Data Processing**: Pandas

## Project Structure

```
CareConnect/
├── app.py                          # Main Streamlit application
├── pyproject.toml                  # UV dependencies and project config
├── Virtue Foundation Ghana v0.3 - Sheet1.csv  # Data file
└── prompts_and_pydantic_models/   # Data models
```

## License

MIT
