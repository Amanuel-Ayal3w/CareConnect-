"""
Tools for CareConnect agents
Wraps database queries and RAG search as LangChain tools
"""

import os
import json
from typing import Optional
from langchain_core.tools import tool
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Import existing RAG functions
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.rag_retrieval import semantic_search, format_search_results

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


@tool
def search_healthcare_facilities(query: str, city: Optional[str] = None, top_k: int = 5) -> str:
    """
    Search for healthcare facilities using semantic search.
    
    Args:
        query: Natural language search query (e.g., "pediatric hospitals", "eye care")
        city: Optional city to filter results
        top_k: Number of results to return (default: 5)
        
    Returns:
        Formatted list of facilities with names, locations, specialties, and contact info
    """
    filters = {"city": city} if city else None
    results = semantic_search(query, top_k=top_k, entity_type="facility", filters=filters)
    formatted = format_search_results(results)
    
    if not formatted['results']:
        return "No facilities found matching your query."
    
    output = []
    for i, result in enumerate(formatted['results'], 1):
        facility = [
            f"{i}. {result['name']} ({result.get('facility_type', 'facility')})",
            f"   Location: {result['location']['city']}, {result['location']['region']}",
            f"   Relevance: {result['similarity_score']}"
        ]
        
        if result.get('specialties'):
            facility.append(f"   Specialties: {', '.join(result['specialties'][:3])}")
        
        if result.get('phone_numbers'):
            facility.append(f"   Phone: {', '.join(result['phone_numbers'][:2])}")
        
        if result.get('capacity'):
            facility.append(f"   Capacity: {result['capacity']} beds")
            
        output.append('\n'.join(facility))
    
    return '\n\n'.join(output)


@tool
def get_regional_facility_statistics(region: str) -> str:
    """
    Get healthcare facility statistics for a specific region.
    
    Args:
        region: Region name (e.g., "Greater Accra", "Ashanti", "Northern")
        
    Returns:
        Statistics including total facilities, facility types, and specialties available
    """
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get facility counts by type
    cursor.execute("""
        SELECT 
            facility_type_id,
            COUNT(*) as count
        FROM facilities
        WHERE address_state_or_region ILIKE %s
        GROUP BY facility_type_id
        ORDER BY count DESC
    """, (f"%{region}%",))
    
    type_counts = cursor.fetchall()
    
    # Get total count
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM facilities
        WHERE address_state_or_region ILIKE %s
    """, (f"%{region}%",))
    
    total = cursor.fetchone()['total']
    
    # Get top specialties
    cursor.execute("""
        SELECT 
            jsonb_array_elements_text(specialties) as specialty,
            COUNT(*) as count
        FROM facilities
        WHERE address_state_or_region ILIKE %s
        AND specialties IS NOT NULL
        GROUP BY specialty
        ORDER BY count DESC
        LIMIT 5
    """, (f"%{region}%",))
    
    specialties = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Format output
    output = [f"Healthcare Statistics for {region}:"]
    output.append(f"\nTotal Facilities: {total}")
    
    if type_counts:
        output.append("\nFacilities by Type:")
        for row in type_counts:
            if row['facility_type_id']:
                output.append(f"  - {row['facility_type_id'].title()}: {row['count']}")
    
    if specialties:
        output.append("\nTop Specialties Available:")
        for row in specialties:
            output.append(f"  - {row['specialty']}: {row['count']} facilities")
    
    return '\n'.join(output)


@tool
def get_facility_details(facility_name: str) -> str:
    """
    Get detailed information about a specific healthcare facility.
    
    Args:
        facility_name: Name of the facility
        
    Returns:
        Comprehensive facility information including services, contact, and location
    """
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT *
        FROM facilities
        WHERE name ILIKE %s
        LIMIT 1
    """, (f"%{facility_name}%",))
    
    facility = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not facility:
        return f"No facility found with name containing '{facility_name}'"
    
    output = [f"Facility: {facility['name']}"]
    
    if facility.get('facility_type_id'):
        output.append(f"Type: {facility['facility_type_id'].title()}")
    
    if facility.get('description'):
        output.append(f"\nDescription: {facility['description'][:300]}")
    
    # Location
    location_parts = []
    if facility.get('address_city'):
        location_parts.append(facility['address_city'])
    if facility.get('address_state_or_region'):
        location_parts.append(facility['address_state_or_region'])
    if location_parts:
        output.append(f"\nLocation: {', '.join(location_parts)}")
    
    if facility.get('address_line1'):
        output.append(f"Address: {facility['address_line1']}")
    
    # Services
    if facility.get('specialties'):
        specialties = facility['specialties']
        if isinstance(specialties, list) and specialties:
            output.append(f"\nSpecialties: {', '.join(specialties[:10])}")
    
    if facility.get('capacity'):
        output.append(f"Bed Capacity: {facility['capacity']}")
    
    # Contact
    if facility.get('phone_numbers'):
        phones = facility['phone_numbers']
        if isinstance(phones, list) and phones:
            output.append(f"\nPhone: {', '.join(phones[:2])}")
    
    if facility.get('email'):
        output.append(f"Email: {facility['email']}")
    
    if facility.get('official_website'):
        output.append(f"Website: {facility['official_website']}")
    
    return '\n'.join(output)


@tool  
def identify_medical_deserts(threshold: float = 0.02) -> str:
    """
    Identify regions that are medical deserts (underserved areas).
    
    Args:
        threshold: Minimum facilities per 1000 people threshold (default: 0.02 = 2 per 100k)
        
    Returns:
        List of underserved regions with facility counts
    """
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get facility counts by region
    cursor.execute("""
        SELECT 
            address_state_or_region as region,
            COUNT(*) as facility_count,
            COUNT(DISTINCT facility_type_id) as facility_types
        FROM facilities
        WHERE address_state_or_region IS NOT NULL
        GROUP BY address_state_or_region
        ORDER BY facility_count ASC
    """)
    
    regions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not regions:
        return "No regional data available"
    
    # Calculate average
    total_facilities = sum(r['facility_count'] for r in regions)
    avg_per_region = total_facilities / len(regions)
    
    output = ["Medical Desert Analysis:"]
    output.append(f"\nTotal Regions Analyzed: {len(regions)}")
    output.append(f"Average Facilities per Region: {avg_per_region:.1f}")
    
    # Identify underserved (< 50% of average)
    underserved_threshold = avg_per_region * 0.5
    underserved = [r for r in regions if r['facility_count'] < underserved_threshold]
    
    if underserved:
        output.append(f"\nUnderserved Regions ({len(underserved)} regions with < {underserved_threshold:.0f} facilities):")
        for region in underserved[:10]:
            output.append(f"  - {region['region']}: {region['facility_count']} facilities, {region['facility_types']} types")
    
    # Show top 3 best served for comparison
    output.append("\nBest Served Regions (for comparison):")
    for region in regions[-3:]:
        output.append(f"  - {region['region']}: {region['facility_count']} facilities")
    
    return '\n'.join(output)


# Export all tools
ALL_TOOLS = [
    search_healthcare_facilities,
    get_regional_facility_statistics,
    get_facility_details,
    identify_medical_deserts
]
