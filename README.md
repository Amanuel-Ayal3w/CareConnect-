# CareConnect Ghana

**AI-powered healthcare intelligence platform for identifying medical deserts and analyzing healthcare coverage in Ghana.**

CareConnect transforms messy, unverified healthcare data into trusted, region-level decisions that help NGOs and governments act faster.

---

## Features

- **Multi-Agent AI System** — Three specialized AI agents collaborate through a shared LangGraph state graph
- **Medical Desert Detection** — Identifies underserved regions by analyzing facility distribution across all of Ghana
- **Trust Scoring** — Rates facility data quality (0–100) across completeness, consistency, validation, and anomaly detection
- **Facility Recommendations** — RAG-powered semantic search over healthcare facilities with natural language queries
- **Interactive Map** — Geographic visualization of facilities and medical desert regions
- **Facility Search** — Filter and explore organizations by name, type, location, and specialty

---

## Architecture

```
User Query
    │
    ▼
┌──────────────────┐
│  LLM Router      │  GPT-4o-mini classifies intent
│  (graph.py)      │  Supports multi-agent dispatch
└────────┬─────────┘
         │
    ┌────▼─────┐
    │Dispatcher │  Pops agents from queue one by one
    └────┬─────┘
         │
    ┌────┴──────────────────────────────┐
    │            │                      │
    ▼            ▼                      ▼
┌─────────┐ ┌──────────┐ ┌──────────────────┐
│Medical   │ │Trust     │ │Recommendation    │
│Desert    │ │Scoring   │ │Agent             │
│Agent     │ │Agent     │ │(RAG + pgvector)  │
└────┬─────┘ └────┬─────┘ └────────┬─────────┘
     │            │                │
     └────────────┴────────────────┘
                  │
           ┌──────▼──────┐
           │ Synthesizer  │  Combines multi-agent results
           └──────┬───────┘
                  │
                  ▼
            Final Response
```

**Agent Communication:** Agents share results through a common `AgentState`. Each agent stores its output in `agent_outputs`, so downstream agents can read and incorporate previous findings. The dispatcher loop enables sequential multi-agent execution for complex queries (e.g., "find a trustworthy hospital" triggers both recommendation + trust scoring).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Orchestration** | LangGraph (agentic workflows) |
| **LLM** | OpenAI GPT-4o-mini |
| **Embeddings** | OpenAI text-embedding-3-small (1536d) |
| **Vector Search** | pgvector (cosine similarity) |
| **Database** | Supabase (Postgres 15+) |
| **Frontend** | Streamlit |
| **Maps** | Folium (Leaflet.js) |
| **Charts** | Plotly |
| **API** | FastAPI |
| **Package Manager** | UV |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-org/CareConnect.git
cd CareConnect
uv sync
```

### 2. Configure environment

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY` — Your OpenAI API key
- `DATABASE_URL` — PostgreSQL connection string (Supabase)
- `SUPABASE_URL` — Your Supabase project URL
- `SUPABASE_KEY` — Your Supabase anon key

### 3. Set up the database

```bash
uv run python backend/setup_db.py
uv run python backend/ingest_data.py
uv run python backend/generate_embeddings.py
```

### 4. Run the app

```bash
uv run streamlit run frontend/app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

To also run the FastAPI backend (optional):

```bash
uv run uvicorn backend.api:app --port 8000
```

---

## Project Structure

```
CareConnect/
├── frontend/
│   ├── app.py                          # Main Streamlit entry point
│   ├── components/
│   │   ├── data_loader.py              # Data loading utilities
│   │   └── map_viz.py                  # Map visualization
│   └── pages/
│       ├── 1_🗺️_Map.py                # Interactive facility map
│       ├── 2_🤖_Agent.py               # AI agent chat interface
│       └── 3_🔍_Search.py              # Facility search & filter
│
├── backend/
│   ├── agents/
│   │   ├── graph.py                    # LangGraph orchestration + router + synthesizer
│   │   ├── state.py                    # Shared agent state definition
│   │   ├── tools.py                    # LangChain tools (RAG, DB queries)
│   │   ├── medical_desert_agent.py     # Regional healthcare analysis
│   │   ├── recommendation_agent.py     # RAG-powered facility recommendations
│   │   └── trust_scoring_agent.py      # Facility trust scoring (0-100)
│   ├── api.py                          # FastAPI REST endpoints
│   ├── database.py                     # Database connection management
│   ├── schema.py                       # PostgreSQL schema definitions
│   ├── rag_retrieval.py                # Semantic search with pgvector
│   ├── generate_embeddings.py          # Embedding generation pipeline
│   ├── ingest_data.py                  # CSV data ingestion
│   └── setup_db.py                     # Database setup
│
├── prompts_and_pydantic_models/
│   ├── organization_extraction.py      # Organization name extraction
│   ├── facility_and_ngo_fields.py      # Structured facility/NGO models
│   ├── medical_specialties.py          # Medical specialty classification
│   └── free_form.py                    # Free-form fact extraction
│
├── .env.example                        # Environment variable template
├── pyproject.toml                      # UV dependencies
└── run_app.sh                          # Launch script
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent/query` | POST | Send a query to the multi-agent system |
| `/api/search/facilities` | POST | Semantic facility search |
| `/api/medical-deserts/analyze` | GET | Regional medical desert analysis |
| `/api/trust-score/calculate` | POST | Calculate facility trust score |
| `/api/stats/summary` | GET | System-wide statistics |

---

## License

MIT
