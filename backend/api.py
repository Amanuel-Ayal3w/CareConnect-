"""
FastAPI Backend Service for CareConnect
Provides REST API for agent system and RAG search
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.graph import invoke_agent
from backend.rag_retrieval import semantic_search, search_facilities_by_location
from backend.agents.medical_desert_agent import analyze_regional_distribution
from backend.agents.trust_scoring_agent import calculate_trust_score

# Create FastAPI app
app = FastAPI(
    title="CareConnect API",
    description="AI-powered healthcare facility mapping and analysis API",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class AgentQuery(BaseModel):
    query: str
    thread_id: Optional[str] = "default"

class AgentResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    city: Optional[str] = None
    region: Optional[str] = None
    top_k: int = 5
    min_similarity: float = 0.0

class FacilityResult(BaseModel):
    id: str
    name: str
    facility_type: Optional[str]
    city: Optional[str]
    region: Optional[str]
    phone: Optional[List[str]]
    specialties: Optional[List[str]]
    similarity_score: float

class TrustScoreRequest(BaseModel):
    facility_id: str

class TrustScoreResponse(BaseModel):
    facility_name: str
    trust_score: int
    assessment: str
    breakdown: dict
    flags: List[str]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "CareConnect API",
        "version": "1.0.0"
    }


@app.post("/api/agent/query", response_model=AgentResponse)
def query_agent(request: AgentQuery):
    """
    Query the AI agent system
    
    The agent will route to:
    - Medical Desert Analyzer - for regional analysis
    - Trust Scoring Agent - for facility verification
    - Recommendation Agent - for facility search
    """
    try:
        response = invoke_agent(request.query, thread_id=request.thread_id)
        
        return AgentResponse(
            response=response,
            agent_used="auto-routed"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.post("/api/search/facilities")
def search_facilities(request: SearchQuery):
    """
    Semantic search for healthcare facilities using RAG
    
    Returns top-K most relevant facilities based on query
    """
    try:
        # Build filters
        filters = {}
        if request.city:
            filters['city'] = request.city
        if request.region:
            filters['region'] = request.region
        
        # Perform semantic search
        results = semantic_search(
            query=request.query,
            top_k=request.top_k,
            entity_type='facility',
            filters=filters if filters else None,
            min_similarity=request.min_similarity
        )
        
        # Format results
        facilities = []
        for r in results:
            facilities.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'facility_type': r.get('facility_type_id'),
                'city': r.get('address_city'),
                'region': r.get('address_state_or_region'),
                'phone': r.get('phone_numbers'),
                'specialties': r.get('specialties'),
                'similarity_score': r.get('similarity_score', 0)
            })
        
        return {
            "count": len(facilities),
            "facilities": facilities
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/api/medical-deserts/analyze")
def get_medical_deserts():
    """
    Analyze regional distribution and identify medical deserts
    
    Returns statistics on facility distribution across regions
    """
    try:
        analysis = analyze_regional_distribution()
        
        return {
            "total_regions": analysis['total_regions'],
            "total_facilities": analysis['total_facilities'],
            "average_per_region": analysis['average_per_region'],
            "desert_threshold": analysis['desert_threshold'],
            "medical_deserts": analysis['medical_deserts'],
            "best_served": analysis['best_served'],
            "all_regions": analysis['all_regions']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.get("/api/facilities/{facility_id}")
def get_facility_details(facility_id: str):
    """
    Get detailed information about a specific facility
    """
    try:
        from backend.database import get_postgres_connection
        import psycopg2.extras
        
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM facilities WHERE id = %s
        """, (facility_id,))
        
        facility = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        
        return dict(facility)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/trust-score/calculate", response_model=TrustScoreResponse)
def get_trust_score(request: TrustScoreRequest):
    """
    Calculate trust score for a facility
    
    Returns 0-100 score with breakdown
    """
    try:
        from backend.database import get_postgres_connection
        import psycopg2.extras
        
        # Get facility data
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM facilities WHERE id = %s
        """, (request.facility_id,))
        
        facility = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        
        # Calculate trust score
        trust_result = calculate_trust_score(dict(facility))
        
        return TrustScoreResponse(
            facility_name=facility['name'],
            trust_score=trust_result['score'],
            assessment=trust_result['assessment'],
            breakdown=trust_result['breakdown'],
            flags=trust_result['flags']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trust scoring error: {str(e)}")


@app.get("/api/stats/summary")
def get_summary_stats():
    """
    Get overall system statistics
    """
    try:
        from backend.database import get_postgres_connection
        import psycopg2.extras
        
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Total facilities
        cursor.execute("SELECT COUNT(*) as count FROM facilities")
        total_facilities = cursor.fetchone()['count']
        
        # Total NGOs
        cursor.execute("SELECT COUNT(*) as count FROM ngos")
        total_ngos = cursor.fetchone()['count']
        
        # Facilities by type
        cursor.execute("""
            SELECT facility_type_id, COUNT(*) as count 
            FROM facilities 
            GROUP BY facility_type_id
        """)
        by_type = {row['facility_type_id']: row['count'] for row in cursor.fetchall()}
        
        # Regions
        cursor.execute("""
            SELECT COUNT(DISTINCT address_state_or_region) as count 
            FROM facilities
        """)
        total_regions = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        # Medical desert analysis
        medical_deserts = analyze_regional_distribution()
        
        return {
            "total_facilities": total_facilities,
            "total_ngos": total_ngos,
            "total_regions": total_regions,
            "facilities_by_type": by_type,
            "medical_deserts_count": len(medical_deserts['medical_deserts']),
            "average_facilities_per_region": medical_deserts['average_per_region']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


# ============================================================================
# Run server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
