# CareConnect API - Usage Guide

## Architecture

CareConnect now has a **separated architecture**:

1. **FastAPI Backend** (Port 8000) - REST API for all business logic
2. **Streamlit Frontend** (Port 8501) - User interface

This allows:
- ✅ Backend can run independently
- ✅ Can scale backend separately
- ✅ Multiple frontends can use the same API
- ✅ Better for production deployment

---

## Running the Services

### Option 1: Run Everything Together (Recommended for Development)
```bash
./run_app.sh
```

This starts both FastAPI backend and Streamlit frontend.

### Option 2: Run Services Separately

**Terminal 1 - Backend:**
```bash
uv run uvicorn backend.api:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
uv run streamlit run frontend/app.py --server.port 8501
```

---

## API Endpoints

### Base URL
`http://localhost:8000`

### 1. Health Check
```bash
GET /
```

**Response:**
```json
{
  "status": "ok",
  "service": "CareConnect API",
  "version": "1.0.0"
}
```

### 2. Agent Query
```bash
POST /api/agent/query
```

**Request Body:**
```json
{
  "query": "Which regions in Ghana are medical deserts?",
  "thread_id": "user123"
}
```

**Response:**
```json
{
  "response": "Medical Desert Analysis for Ghana...",
  "agent_used": "auto-routed"
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find pediatric hospitals in Accra"}'
```

### 3. Facility Search
```bash
POST /api/search/facilities
```

**Request Body:**
```json
{
  "query": "eye hospital specialist",
  "city": "Accra",
  "top_k": 5,
  "min_similarity": 0.5
}
```

**Response:**
```json
{
  "count": 5,
  "facilities": [
    {
      "id": "uuid",
      "name": "New Vision Optical",
      "facility_type": "clinic",
      "city": "Accra",
      "phone": ["+233..."],
      "specialties": ["ophthalmology"],
      "similarity_score": 0.68
    }
  ]
}
```

### 4. Medical Desert Analysis
```bash
GET /api/medical-deserts/analyze
```

**Response:**
```json
{
  "total_regions": 51,
  "total_facilities": 920,
  "average_per_region": 18.0,
  "desert_threshold": 9.0,
  "medical_deserts": [
    {
      "region": "Techiman Municipal",
      "total_facilities": 1,
      "hospitals": 1,
      "clinics": 0
    }
  ],
  "best_served": [...]
}
```

### 5. Trust Score
```bash
POST /api/trust-score/calculate
```

**Request Body:**
```json
{
  "facility_id": "uuid-of-facility"
}
```

**Response:**
```json
{
  "facility_name": "Korle Bu Teaching Hospital",
  "trust_score": 62,
  "assessment": "Trustworthy - Good data quality",
  "breakdown": {
    "completeness": 12,
    "consistency": 25,
    "validation": 0,
    "anomaly_check": 25
  },
  "flags": []
}
```

### 6. Facility Details
```bash
GET /api/facilities/{facility_id}
```

**Response:** Full facility object

### 7. Summary Statistics
```bash
GET /api/stats/summary
```

**Response:**
```json
{
  "total_facilities": 920,
  "total_ngos": 67,
  "total_regions": 51,
  "facilities_by_type": {
    "hospital": 450,
    "clinic": 470
  },
  "medical_deserts_count": 42,
  "average_facilities_per_region": 18.0
}
```

---

## API Documentation

Once the backend is running, visit:

**Swagger UI (Interactive docs):**
```
http://localhost:8000/docs
```

**ReDoc (Alternative docs):**
```
http://localhost:8000/redoc
```

---

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8000/

# Get stats
curl http://localhost:8000/api/stats/summary

# Query agent
curl -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find hospitals in Accra"}'

# Search facilities
curl -X POST http://localhost:8000/api/search/facilities \
  -H "Content-Type: application/json" \
  -d '{"query": "pediatric", "city": "Accra", "top_k": 3}'
```

### Using Python
```python
import requests

# Query the agent
response = requests.post(
    "http://localhost:8000/api/agent/query",
    json={"query": "Which regions are medical deserts?"}
)
print(response.json())

# Search facilities
response = requests.post(
    "http://localhost:8000/api/search/facilities",
    json={"query": "eye care", "city": "Accra"}
)
print(response.json())
```

---

## Environment Variables

The backend uses these from `.env`:
- `DATABASE_URL` - Supabase PostgreSQL connection
- `OPENAI_API_KEY` - For embeddings and agent LLM
- `OPENAI_MODEL` - Model to use (default: gpt-4o-mini)

---

## Production Deployment

### Docker (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t careconnect-api .
docker run -p 8000:8000 --env-file .env careconnect-api
```

### Cloud Platforms

**Railway / Render / Fly.io:**
- Set environment variables
- Deploy command: `uvicorn backend.api:app --host 0.0.0.0 --port $PORT`

**AWS Lambda (Serverless):**
- Use Mangum adapter for FastAPI

---

## Frontend Integration

The Streamlit frontend can now call the API instead of importing backend directly.

**Example update needed in `frontend/pages/2_🤖_Agent.py`:**

```python
import requests

API_URL = "http://localhost:8000"

# Instead of:
# from backend.agents.graph import invoke_agent
# response = invoke_agent(prompt)

# Use:
response = requests.post(
    f"{API_URL}/api/agent/query",
    json={"query": prompt, "thread_id": st.session_state.user_id}
)
agent_response = response.json()['response']
```

---

## Benefits of This Architecture

1. **Scalability** - Backend can scale independently
2. **Multiple Clients** - Mobile app, web app, CLI can all use same API
3. **Separation of Concerns** - Frontend doesn't know about DB/AI logic
4. **Caching** - Can add Redis cache layer at API level
5. **Rate Limiting** - Can limit API requests per user
6. **Authentication** - Can add JWT/OAuth at API level
7. **Monitoring** - Can monitor API performance separately

---

## Next Steps

1. Update Streamlit frontend to use API instead of direct imports
2. Add authentication (JWT tokens)
3. Add rate limiting (slowapi)
4. Add caching (Redis)
5. Deploy backend to cloud
6. Set up CI/CD pipeline
7. Add API versioning (/api/v1/...)

---

**CareConnect API is now running! 🚀**

Visit http://localhost:8000/docs to explore the interactive API documentation.
