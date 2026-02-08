# **MedDesertAI – Software Design Specification (SDS) & Functional Requirements**

## **1\. Overview**

MedDesertAI is an **AI-powered agent** designed to read unstructured medical facility and NGO data, extract structured insights, identify gaps in healthcare coverage, and provide actionable recommendations via a dashboard and interactive map.

**Key Goals:**

1. Identify medical deserts and underserved regions.  
2. Verify claims of healthcare facilities and assign trust/confidence scores.  
3. Provide NGOs and government agencies with data-driven recommendations for intervention.  
4. Visualize results through maps and dashboards.

---

## **2\. Functional Requirements**

### **2.1 Data Ingestion**

* System must accept **CSV, JSON**, or structured API inputs of facility and NGO data.  
* System must normalize addresses and region data (city, state/region, country).  
* Must store raw and processed data in **Databricks Delta Tables** or local storage (JSON/SQLite for MVP).

### **2.2 Intelligent Document Parsing (IDP)**

* Extract facility capabilities, procedures, equipment, and specialties from free-text descriptions.  
* Extract NGO metadata: mission statements, operational countries, descriptions.  
* Validate extracted data using **Pydantic models**.

### **2.3 Verification & Trust Scoring**

* Compare facility claims with available staff and equipment.  
* Assign **trust/confidence scores** per capability or procedure.  
* Highlight suspicious or incomplete claims for human review.

### **2.4 Regional Aggregation**

* Group facilities by region (city, state, country).  
* Calculate **coverage metrics** for critical services (ICU, trauma care, surgery).  
* Identify **medical deserts** (regions with inadequate coverage).

### **2.5 Actionable Recommendations**

* Recommend interventions such as:  
  * Upgrading facilities with missing critical capabilities.  
  * Deploying mobile clinics to underserved regions.  
* Optional: Scenario-based planning (e.g., “What if Facility X adds ICU?”).

### **2.6 RAG (Retrieval-Augmented Generation)**

* System must embed facility and NGO data for similarity search.  
* Retrieve relevant context for AI reasoning and recommendation generation.

### **2.7 Dashboard & Map**

* Display a **map of regions**, color-coded by medical desert severity.  
* Clickable regions to show facility-level metrics and trust scores.  
* Tabular views for high-risk facilities, missing services, and recommended actions.  
* Optional: Planning agent interface for querying recommendations.

### **2.8 Logging & Traceability**

* Log AI reasoning steps, inputs, and outputs.  
* Maintain reproducibility for recommendations.  
* Optional: MLflow for tracking experiments and agent reasoning steps.

---

## **3\. Non-Functional Requirements**

| Requirement | Description |
| ----- | ----- |
| **Performance** | MVP should process a dataset of \~500 facilities within 2–5 minutes. |
| **Scalability** | Designed to scale with larger datasets using Databricks. |
| **Usability** | Dashboard/map interface must be intuitive for non-technical NGO users. |
| **Reliability** | AI agent should handle missing or incomplete data gracefully. |
| **Maintainability** | Code must be modular, documented, and structured for easy extension. |
| **Security** | Sensitive data (emails, phone numbers) must be stored securely. |
| **Portability** | System should run on local machines or cloud platforms (Databricks free edition for MVP). |

---

## **4\. System Architecture (High-Level)**

**Layers:**

1. **Data Layer**  
   * Stores raw and structured data (Databricks Delta Tables).  
   * Embeddings for RAG stored in vector DB.  
2. **AI / Reasoning Layer**  
   * IDP module for parsing unstructured text.  
   * Verification module for trust scoring.  
   * Planning/recommendation agent (optional).  
3. **Aggregation & Logic Layer**  
   * Regional aggregation, desert detection, and service gap computation.  
4. **Presentation Layer**  
   * Interactive map (Leaflet \+ OpenStreetMap).  
   * Dashboard (Streamlit / React) with tables and recommendations.

**Data Flow:**

Raw Dataset → AI Parsing (IDP) → Verification → Regional Aggregation → RAG → Map/Dashboard → NGO Actions

---

## **5\. Database Design (Simplified for MVP)**

**Entities / Tables:**

1. **Facilities**  
   * id, name, type, operatorTypeId, specialties, procedures, capabilities, equipment, numberDoctors, capacity, address, trust\_scores.  
2. **NGOs**  
   * id, name, missionStatement, description, countries, contact info, website, social links.  
3. **Regions**  
   * id, name, aggregated metrics, medical\_desert flag, missing\_services, recommendations.  
4. **Embeddings**  
   * facility\_id, vector\_embedding for RAG.

---

## **6\. Key Scenarios / Use Cases**

1. **NGO searches for medical deserts**  
   * Input: Country/Region  
   * Output: Map highlighting underserved regions, table of high-risk facilities.  
2. **AI verifies facility claims**  
   * Input: Facility description  
   * Output: Structured JSON with trust/confidence scores.  
3. **Scenario Planning**  
   * Input: “What if Facility X adds ICU?”  
   * Output: Updated desert map and recommendations.

