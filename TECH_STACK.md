# 🛠️ CareConnect Technology Stack

## Overview

CareConnect is built with a modern, AI-first architecture designed for hackathons with production-ready components.

---

## Tech Stack Summary

### **Backend**
- **Language**: Python 3.12+
- **AI Orchestration**: LangGraph (agentic workflows)
- **LLM Provider**: OpenAI (GPT-4o-mini / GPT-4)
- **Database**: Supabase (Postgres 15+)
- **Vector Search**: pgvector
- **Embeddings**: OpenAI text-embedding-3-small
- **API Framework**: FastAPI (future)
- **Data Processing**: Pandas, NumPy

### **Frontend**
- **Framework**: Streamlit
- **Maps**: Folium (Leaflet.js wrapper)
- **Charts**: Plotly, Altair
- **Deployment**: Streamlit Cloud

### **Infrastructure**
- **Package Manager**: UV (ultra-fast Python package manager)
- **Containerization**: Docker + Docker Compose
- **Version Control**: Git
- **Environment Management**: python-dotenv

### **AI & ML**
- **LLM**: OpenAI GPT-4o-mini (cost-effective) / GPT-4 (advanced reasoning)
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Orchestration**: LangGraph (state-based + agentic workflows)
- **RAG**: pgvector with semantic search
- **Structured Output**: Pydantic v2 models

---

## Why These Choices?

### 1. **LangGraph over LangChain/CrewAI**
✅ **State-based workflows** - Perfect for multi-step analysis
✅ **Agentic capabilities** - Agents can decide next steps dynamically
✅ **Better control** - Fine-grained control over agent behavior
✅ **Debuggable** - Clear state transitions
✅ **Production-ready** - Used by major companies

**Example**: Our medical desert detection needs multiple agents (parser → verifier → analyzer) with decision points.

### 2. **Supabase (Postgres + pgvector) over DuckDB/SQLite**
✅ **Cloud-hosted** - No server management
✅ **pgvector** - Native vector search (no separate vector DB needed)
✅ **Scalable** - Auto-scaling, connection pooling
✅ **Real-time** - Built-in subscriptions for live updates
✅ **Free tier** - 500MB database, perfect for hackathons
✅ **Production-ready** - Used by thousands of companies
✅ **Dashboard** - Visual table editor, SQL editor

**Why not DuckDB?** DuckDB is great for local analytics but lacks cloud hosting and vector search.

### 3. **OpenAI Embeddings over Local Models**
✅ **No PyTorch** - Saves ~3GB+ of dependencies
✅ **Fast setup** - No model downloads
✅ **High quality** - State-of-the-art embeddings
✅ **Cost-effective** - $0.02 per 1M tokens
✅ **API-based** - Works anywhere, no GPU needed

**Cost Example**: Embedding 1000 facilities (~500K tokens) = $0.01

### 4. **Streamlit over React/Next.js**
✅ **Python-native** - No context switching
✅ **Rapid development** - Build UIs in minutes
✅ **Built-in components** - Maps, charts, forms
✅ **Easy deployment** - Streamlit Cloud (free)
✅ **Perfect for demos** - Ideal for hackathons

### 5. **UV over pip**
✅ **10-100x faster** - Rust-based
✅ **Better dependency resolution** - Smarter than pip
✅ **Modern** - Supports pyproject.toml
✅ **Compatible** - Works with existing pip workflows

---

## Architecture Comparison


### After (Current Design - User Specified)
```
┌─────────────────────────────────────┐
│  Streamlit Frontend                 │
│  - Maps (Folium)                    │
│  - Dashboard (Plotly)               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  LangGraph Agent System             │
│  - Agentic Workflows                │
│  - State Management                 │
│  - Multi-step Reasoning             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Supabase (Cloud)                   │
│  ├─ Postgres (structured data)      │
│  └─ pgvector (embeddings + RAG)     │
└─────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  OpenAI API                         │
│  - GPT-4o-mini / GPT-4              │
│  - text-embedding-3-small           │
└─────────────────────────────────────┘
```

**Benefits:**
- ✅ Single database (Postgres) handles both structured data + vectors
- ✅ Cloud-hosted (no local setup)
- ✅ Agentic workflows (dynamic decision-making)
- ✅ No PyTorch dependencies
- ✅ Production-ready

---

## Dependency Tree

### Core Dependencies (Lightweight!)
```
careconnect/
├── python-dotenv (config)
├── pydantic (data validation)
│
├── openai (LLM + embeddings)
│   ├── httpx
│   └── typing-extensions
│
├── langchain (base)
│   ├── langchain-core
│   └── langchain-openai
│
├── langgraph (agentic workflows)
│   ├── langchain
│   └── pydantic
│
├── supabase (database client)
│   ├── httpx
│   ├── postgrest-py
│   └── storage3
│
├── psycopg2-binary (Postgres adapter)
├── pgvector (vector support)
│
├── pandas (data processing)
├── numpy
│
├── streamlit (frontend)
│   ├── plotly
│   ├── altair
│   └── folium (via streamlit-folium)
│
└── fastapi (future API)
    └── uvicorn
```

**Total Install Size**: ~500MB (vs ~3.5GB with PyTorch!)

---

## OpenAI Models Used

### 1. **GPT-4o-mini** (Primary)
- **Purpose**: Document parsing, reasoning, recommendations
- **Cost**: $0.15 / 1M input tokens, $0.60 / 1M output tokens
- **Speed**: Fast (~500ms response)
- **Use Cases**: 
  - Parse facility documents
  - Calculate trust scores
  - Generate recommendations

**Example Cost**: Processing 1000 facilities × 2 calls = ~$0.30

### 2. **GPT-4** (Advanced - Optional)
- **Purpose**: Complex medical reasoning
- **Cost**: $5 / 1M input tokens, $15 / 1M output tokens
- **Speed**: Slower (~2s response)
- **Use Cases**:
  - Medical specialty classification
  - Complex capability verification
  - Critical decision-making

**Recommendation**: Use GPT-4o-mini for MVP, upgrade to GPT-4 for production.

### 3. **text-embedding-3-small** (Embeddings)
- **Purpose**: Vector embeddings for RAG
- **Cost**: $0.02 / 1M tokens
- **Dimensions**: 1536
- **Speed**: Very fast (~100ms for batch)

**Example Cost**: Embedding 1000 facilities = $0.01

---

## Development Tools

### Package Management
```bash
# UV - Modern Python package manager



### Environment Variables
```bash
# .env file (never commit!)
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
DATABASE_URL=postgresql://...
```

### Version Control
```bash
# .gitignore
.env
.venv/
__pycache__/
*.pyc
data/outputs/
```

---

## Deployment Options

### Option 1: Streamlit Cloud (Recommended for MVP)
✅ **Free tier available**
✅ **Automatic deployments from GitHub**
✅ **Built-in secrets management**
✅ **No Docker needed**

**Steps:**
1. Push code to GitHub
2. Connect Streamlit Cloud
3. Add secrets (API keys)
4. Deploy!

### Option 2: Docker + Cloud Run / Railway / Render
✅ **Full control**
✅ **Works anywhere**
✅ **Includes Dockerfile**

**Steps:**
1. Build: `docker build -t careconnect .`
2. Push to registry
3. Deploy to cloud

### Option 3: Local Development
✅ **Fast iteration**
✅ **No deployment needed**

**Steps:**
```bash
uv pip install .
streamlit run frontend/streamlit_app.py
```

---

## Cost Estimates (Monthly)

### Free Tier (MVP)
- **Supabase**: Free (500MB database)
- **Streamlit Cloud**: Free (1 app)
- **OpenAI**: Pay-as-you-go
  - 1000 facilities processed: ~$0.50
  - 10K queries/month: ~$5
- **Total**: ~$5-10/month

### Production (1000 facilities, 10K users)
- **Supabase Pro**: $25/month (8GB database)
- **Streamlit Cloud**: $0-100/month
- **OpenAI**: ~$50-200/month
- **Total**: ~$75-325/month

---

## Performance Characteristics

### Response Times (Expected)
- **Document parsing**: 1-3 seconds (OpenAI API)
- **Trust score calculation**: <100ms (local)
- **Vector search**: <50ms (pgvector)
- **Dashboard load**: 1-2 seconds (Streamlit)
- **Map rendering**: 2-3 seconds (Folium + 1000 markers)

### Scalability
- **Facilities**: 10K+ (Postgres + pgvector)
- **Concurrent users**: 100+ (Streamlit)
- **Vector search**: 1M+ embeddings (pgvector)

---

## Security & Best Practices

### API Keys
✅ **Never commit** `.env` files
✅ **Use secrets management** in production
✅ **Rotate keys** regularly
✅ **Least privilege** access

### Database
✅ **Row-level security** (Supabase)
✅ **Connection pooling** (built-in)
✅ **Backups** (automatic daily)
✅ **SSL connections** (enforced)

### Code Quality
✅ **Type hints** (Pydantic models)
✅ **Error handling** (try/except)
✅ **Logging** (Python logging)
✅ **Testing** (pytest for critical paths)

---

## Tech Stack Maturity

| Technology | Maturity | Community | Documentation | Verdict |
|------------|----------|-----------|---------------|---------|
| **Python 3.12** | Stable | Huge | Excellent | ✅ Production |
| **LangGraph** | Beta | Growing | Good | ✅ Production |
| **OpenAI API** | Stable | Huge | Excellent | ✅ Production |
| **Supabase** | Stable | Large | Excellent | ✅ Production |
| **pgvector** | Stable | Growing | Good | ✅ Production |
| **Streamlit** | Stable | Large | Excellent | ✅ Production |
| **UV** | Beta | Growing | Good | ✅ Dev (pip fallback) |

---

## Future Enhancements

### Phase 2 (Post-Hackathon)
1. **FastAPI REST API** - Separate backend API
2. **Real-time updates** - Supabase subscriptions
3. **Authentication** - User accounts, roles
4. **Batch processing** - Queue system for large datasets
5. **Advanced visualizations** - Custom dashboards

### Phase 3 (Production)
1. **React/Next.js frontend** - Better UX
2. **Mobile app** - React Native
3. **Advanced RAG** - Multi-query, reranking
4. **Fine-tuned models** - Domain-specific LLM
5. **Monitoring** - Logs, metrics, alerts

---

## Comparison with Alternatives

### LangGraph vs CrewAI
| Feature | LangGraph | CrewAI |
|---------|-----------|--------|
| State management | ✅ Built-in | ⚠️ Limited |
| Agentic workflows | ✅ Yes | ✅ Yes |
| Control flow | ✅ Explicit | ⚠️ Implicit |
| Debugging | ✅ Easy | ❌ Hard |
| Community | ✅ Large | ⚠️ Smaller |
| **Verdict** | ✅ **Winner** | ⚠️ Good for simple tasks |

### Supabase vs Firebase
| Feature | Supabase | Firebase |
|---------|----------|----------|
| Database | ✅ Postgres | ⚠️ NoSQL |
| Vector search | ✅ pgvector | ❌ No |
| SQL | ✅ Full SQL | ⚠️ Limited |
| Open source | ✅ Yes | ❌ No |
| Cost | ✅ Cheaper | ⚠️ Expensive |
| **Verdict** | ✅ **Winner for AI apps** | ⚠️ Good for mobile |

### OpenAI vs Local Models (LLaMA 2)
| Feature | OpenAI | LLaMA 2 |
|---------|--------|---------|
| Setup | ✅ API key | ❌ Complex |
| Cost | ✅ Pay-as-go | ⚠️ GPU needed |
| Quality | ✅ SOTA | ⚠️ Good |
| Speed | ✅ Fast | ⚠️ Depends on GPU |
| Dependencies | ✅ Minimal | ❌ PyTorch (3GB+) |
| **Verdict** | ✅ **Winner for MVP** | ⚠️ Good for privacy |

---

## Installation Size Comparison

### With Local Models (Avoided)
```
Dependencies: 150+ packages
Size: ~3.5GB
Download time: 10-15 minutes
Includes:
  - PyTorch (~800MB)
  - CUDA libraries (~2GB)
  - Transformers (~500MB)
  - sentence-transformers (~200MB)
```

### With OpenAI APIs (Current)
```
Dependencies: ~80 packages
Size: ~500MB
Download time: 2-3 minutes
Includes:
  - openai (~5MB)
  - langchain (~50MB)
  - streamlit (~100MB)
  - pandas (~50MB)
  - supabase (~10MB)
```

**Result**: 7x smaller, 5x faster installation! 🚀

---

## Summary

CareConnect uses a modern, cloud-native stack optimized for:
- ✅ **Rapid development** (hackathon-friendly)
- ✅ **Production-ready** (scalable, secure)
- ✅ **Cost-effective** ($5-10/month for MVP)
- ✅ **AI-first** (LangGraph + OpenAI + RAG)
- ✅ **No heavy dependencies** (no PyTorch)
- ✅ **Easy deployment** (Streamlit Cloud, Docker)

**Tech Stack**: Python + LangGraph + OpenAI + Supabase + Streamlit
**Deployment**: Streamlit Cloud (free tier)
**Cost**: ~$5-10/month for MVP

**Perfect for hackathons and production! 🚀**
