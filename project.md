# MVP Plan: Bridging Medical Deserts

**Project:** Intelligent Document Parsing Agent for Virtue Foundation  
**Dataset:** Ghana Facility & NGO Dataset  
**Purpose:** Assist NGOs and governments in identifying medical deserts and prioritizing healthcare interventions.

---

## 1. Agent Overview

The AI Agent is a **digital health intelligence layer** that reads unstructured medical facility and NGO documents, verifies claims, aggregates regional data, and provides **actionable insights**.  

**Key Responsibilities:**
1. Extract structured data from unstructured fields (`procedure`, `equipment`, `capability`).
2. Verify facility claims against available resources and assign trust/confidence scores.
3. Aggregate facility data to compute region-level insights and identify medical deserts.
4. Generate **actionable recommendations** for NGOs and governments.
5. Output results to **map and dashboard** visualizations.

---

## 2. Agent Architecture

**Layers & Responsibilities:**

### Data Layer
- Stores original datasets (CSV/JSON) and parsed outputs.
- Holds embeddings for RAG if using vector search.

### AI / Reasoning Layer
- **IDP Module:** Parses unstructured text and converts it into structured JSON.
- **Verification Module:** Assigns trust scores based on staff, equipment, and claimed capabilities.
- **Planning Agent (Optional):** Generates recommendations using aggregated regional insights.

### Aggregation & Logic Layer
- Groups facilities by region (`address_stateOrRegion` + `address_city`).
- Calculates coverage metrics and medical desert scores.
- Prepares inputs for visualization and decision-making.

### Presentation Layer
- Map: Color-coded regions showing medical deserts.
- Dashboard: Tables of high-risk facilities, capability gaps, and actionable insights.
- Optional chat/planning interface for scenario-based recommendations.

**Data Flow:**  
---

## 3. Input / Output Specification

### Inputs
- **Facility documents:** `procedure`, `equipment`, `capability`, `specialties`
- **Structured metadata:** `facilityTypeId`, `operatorTypeId`, `numberDoctors`, `capacity`, `address_*`
- **NGO metadata:** `missionStatement`, `organizationDescription`, `countries`

### Outputs

#### Structured Facility JSON
```json
{
  "facility_name": "Kumasi District Hospital",
  "capabilities": ["Emergency Surgery", "Level II trauma center"],
  "procedures": ["C-section", "Endoscopy"],
  "equipment": ["Siemens CT Scanner"],
  "specialties": ["gynecologyAndObstetrics", "pediatrics"],
  "trust_scores": {"Emergency Surgery": 0.4, "ICU": 0.9},
  "region": "Ashanti Region"
}

{
  "region": "Northern Region",
  "medical_desert": true,
  "services_missing": ["ICU", "Trauma Care"],
  "high_risk_facilities": ["Facility A", "Facility B"],
  "recommendations": ["Upgrade ICU at Facility A", "Deploy mobile clinic in X district"]
}

4. AI Logic / Workflow
Document Parsing (IDP)

Extract capabilities, procedures, equipment, specialties.

Output structured JSON per facility.

Claim Verification

Compare capabilities vs available staff/equipment.

Assign trust/confidence scores.

Regional Aggregation

Group facilities by region.

Compute medical desert score and gaps for critical services.

Actionable Recommendations (Optional)

Simulate interventions to maximize population coverage.

Output ranked recommendations with reasoning.

5. MVP Timeline
Day	Task
1	Environment setup, ingest dataset, parse 5–10 documents
2	Full IDP parsing + trust scoring
3	Regional aggregation & medical desert detection
4	Map + dashboard visualization
5	Polishing dashboard, optional planning agent, demo prep
6. User Interaction / Interface

Map: Visualizes medical deserts; click a region → shows facility-level data and trust scores.

Dashboard: Displays tables of high-risk facilities, capability gaps, regional metrics, and AI recommendations.

Optional Planning Agent: Chat-like interface for NGOs to query “where to intervene” and get reasoning-backed recommendations.

7. Success Criteria

Accuracy: Correctly verifies facility claims and computes trust scores.

Impact: Identifies medical deserts and helps prioritize interventions.

User Experience: Dashboard/map is intuitive for NGOs/governments.

Innovation: Demonstrates AI reasoning on unstructured medical data.

8. Notes / Assumptions

MVP focuses on Ghana dataset only.

AI outputs structured JSON for downstream visualization.

Trust scores are relative for demonstration purposes.

Map + dashboard is static visualization; dynamic real-time updates are out of scope.

9. Stretch Goals (Optional)

Row-level citations for AI reasoning.

Multi-step agent reasoning trace.

Scenario simulations: “What if we upgrade Facility A?”

Mobile-responsive dashboard.


---

## **File 2: `tech_stack.md`**

```markdown
# Detailed Tech Stack: Bridging Medical Deserts AI Agent

**Purpose:** Explain each technology choice for the MVP, including how Databricks can serve as the database/backend.

---

## 1. AI / LLM Layer

**Role:** Parse unstructured medical text and generate structured JSON outputs.

- **Options:**
  - **GPT-4 API:** Simple, cloud-based, powerful LLM for text parsing and reasoning.
  - **LLaMA 2:** Open-source alternative if cost or offline execution is preferred.
- **Orchestration:** 
  - **LangGraph or CrewAI** for building agentic workflows and chaining multiple reasoning steps.

**Responsibilities:**
- Convert free-text fields (`procedure`, `capability`, `equipment`) into structured JSON.
- Generate trust/confidence scores for claims.
- Optional: multi-step reasoning for recommendations.

---

## 2. Retrieval-Augmented Generation (RAG)

**Role:** Provide context to the LLM from your dataset for more accurate responses.

- **Tools:**
  - **FAISS** – Vector database for fast similarity search.
  - **Databricks Vector Search** – Integrates well with the dataset and LLM workflows, good for hackathon MVP.

**Use Case in MVP:**
- Embed facility descriptions, equipment, and capabilities.
- Let AI retrieve relevant facility info when reasoning about gaps or medical deserts.

---

## 3. Data Modeling & Storage

**Role:** Organize input data, store parsed output, and support efficient queries.

- **Tech:**
  - **Pandas + Pydantic:** For validation and structured representation of parsed JSON.
  - **Databricks (Delta Tables):** Can serve as your primary backend, storing structured data, embeddings, and outputs.  
    - Easy query of facilities by region or specialty.  
    - Scales to larger datasets if needed later.

**Advantages of Databricks:**
- Combines **database + compute** → easy to run analysis without separate servers.
- Supports **Delta Lake** for versioned data.
- Integrates with MLflow for experiment tracking.

---

## 4. Dashboard & Visualization

**Role:** Allow NGOs / governments to explore insights and take action.

- **Map Visualization:** 
  - **Leaflet + OpenStreetMap** – lightweight, open-source, hackathon-friendly.
  - Color-coded regions to highlight medical deserts.
- **Dashboard:** 
  - **Streamlit or React** – quick UI to show tables, metrics, and AI recommendations.
  - Clickable regions → facility-level data + trust scores.

---

## 5. Logging & Traceability

**Role:** Track AI reasoning and decisions for transparency.

- **MLflow (optional)** – Log AI parsing outputs, trust scores, and recommendations.
- Can store reasoning traces to justify AI decisions.

---

## 6. Storage & Data Flow

**MVP Setup with Databricks:**
1. Load raw dataset (CSV/JSON) into **Databricks Delta Tables**.
2. Preprocess & parse documents using AI → store structured JSON outputs in Delta Tables.
3. Generate embeddings (for RAG) → store in Databricks Vector Database.
4. Aggregation and desert detection queries are run directly in Databricks.
5. Dashboard queries Databricks for regional metrics and facility details.

**Why Databricks is useful for MVP:**
- Single platform for storage, compute, and ML workflows.
- Easy to integrate with Python, Pandas, LLMs, and RAG workflows.
- Minimizes infrastructure overhead for hackathon MVP.

---

## 7. Summary

| Component | Technology | Role |
|-----------|-----------|------|
| AI / LLM | GPT-4 / LLaMA 2 | Parse unstructured text, generate structured JSON |
| RAG / Vector Search | FAISS / Databricks Vector Search | Retrieve relevant data for reasoning |
| Data Modeling | Pandas + Pydantic | Structure and validate parsed data |
| Database / Storage | Databricks Delta Tables | Store raw + structured data and embeddings |
| Dashboard | Streamlit / React | Visualize map, tables, recommendations |
| Map | Leaflet + OpenStreetMap | Highlight medical deserts by region |
| Logging | MLflow (optional) | Track AI reasoning and decisions |



