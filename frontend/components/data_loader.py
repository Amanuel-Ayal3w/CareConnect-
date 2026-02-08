"""
Data loading utilities for Streamlit frontend
Handles database connections and caching
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_facilities():
    """
    Load all facilities from database
    
    Returns:
        pandas.DataFrame with facility data
    """
    conn = psycopg2.connect(DATABASE_URL)
    
    query = """
        SELECT 
            id,
            name,
            facility_type_id,
            organization_type,
            address_city,
            address_state_or_region,
            address_country,
            latitude,
            longitude,
            phone_numbers,
            email,
            official_website,
            specialties,
            capacity,
            description,
            year_established
        FROM facilities
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY name
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df


@st.cache_data(ttl=300)
def load_regional_statistics():
    """
    Load regional facility statistics
    
    Returns:
        dict with regional analysis data
    """
    from backend.agents.medical_desert_agent import analyze_regional_distribution
    return analyze_regional_distribution()


@st.cache_data(ttl=300)
def get_facility_counts_by_region():
    """
    Get facility counts per region for map coloring
    
    Returns:
        pandas.DataFrame with columns: region, facility_count, is_desert
    """
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            COALESCE(address_state_or_region, 'Unknown') as region,
            COUNT(*) as facility_count
        FROM facilities
        GROUP BY address_state_or_region
        ORDER BY facility_count ASC
    """)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    df = pd.DataFrame(results)
    
    # Calculate average and mark deserts
    avg_count = df['facility_count'].mean()
    desert_threshold = avg_count * 0.5
    df['is_desert'] = df['facility_count'] < desert_threshold
    
    return df


@st.cache_data(ttl=300)
def search_facilities_cached(query: str = "", city: str = None, facility_type: str = None, min_trust: int = 0):
    """
    Search facilities with filters (cached)
    
    Args:
        query: Search term
        city: Filter by city
        facility_type: Filter by type (hospital, clinic)
        min_trust: Minimum trust score
    
    Returns:
        pandas.DataFrame with matching facilities
    """
    from backend.rag_retrieval import semantic_search
    
    # Build filters
    filters = {}
    if city and city != "All":
        filters['city'] = city
    
    # Use RAG search if query provided
    if query:
        results = semantic_search(
            query=query,
            top_k=50,
            entity_type='facility',
            filters=filters if filters else None
        )
        
        # Convert to DataFrame
        facilities_list = []
        for r in results:
            facilities_list.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'facility_type': r.get('facility_type_id'),
                'city': r.get('address_city'),
                'region': r.get('address_state_or_region'),
                'phone': ', '.join(r.get('phone_numbers', [])) if r.get('phone_numbers') else None,
                'specialties': r.get('specialties'),
                'description': r.get('description'),
                'similarity': r.get('similarity_score', 0)
            })
        
        df = pd.DataFrame(facilities_list)
    else:
        # Direct database query for no search term
        df = load_facilities()
        
        if city and city != "All":
            df = df[df['address_city'].str.contains(city, case=False, na=False)]
    
    # Apply type filter
    if facility_type and facility_type != "All":
        df = df[df['facility_type_id'] == facility_type.lower()]
    
    return df


def calculate_trust_score_simple(facility_row):
    """
    Simple trust score calculation for display
    (Full calculation is in trust_scoring_agent)
    """
    score = 50  # Base score
    
    val = facility_row.get('phone_numbers')
    if isinstance(val, list) and val:
        score += 20
        
    if pd.notna(facility_row.get('email')):
        score += 10
    if pd.notna(facility_row.get('official_website')):
        score += 10
    if pd.notna(facility_row.get('description')):
        score += 10
    if pd.notna(facility_row.get('capacity')):
        score += 10
    
    return min(score, 100)
