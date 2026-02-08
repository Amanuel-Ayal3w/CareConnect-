"""
RAG Retrieval System for CareConnect
Semantic search using vector similarity with pgvector
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def get_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for search query using OpenAI
    
    Args:
        query: Natural language search query
        
    Returns:
        1536-dimension embedding vector
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    return response.data[0].embedding


def semantic_search(
    query: str,
    top_k: int = 5,
    entity_type: Optional[str] = None,
    filters: Optional[Dict] = None,
    min_similarity: float = 0.0
) -> List[Dict]:
    """
    Semantic search using vector similarity
    
    Args:
        query: Natural language query
        top_k: Number of results to return
        entity_type: Filter by 'facility' or 'ngo'
        filters: Additional filters:
            - city: Filter by address_city
            - region: Filter by address_state_or_region
            - specialty: Filter facilities by specialty (contains)
            - facility_type: Filter by facility_type_id
        min_similarity: Minimum cosine similarity threshold (0-1)
    
    Returns:
        List of results with entity data, similarity scores, metadata
    """
    # Generate query embedding
    query_embedding = get_query_embedding(query)
    
    # Build SQL query with filters
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Base query with cosine similarity
    sql = """
        SELECT 
            e.entity_id,
            e.entity_type,
            e.content,
            e.metadata,
            1 - (e.embedding <=> %s::vector) AS similarity_score,
            CASE 
                WHEN e.entity_type = 'facility' THEN row_to_json(f.*)
                WHEN e.entity_type = 'ngo' THEN row_to_json(n.*)
            END AS entity_data
        FROM embeddings e
        LEFT JOIN facilities f ON e.entity_id = f.id AND e.entity_type = 'facility'
        LEFT JOIN ngos n ON e.entity_id = n.id AND e.entity_type = 'ngo'
        WHERE 1=1
    """
    
    params = [json.dumps(query_embedding)]
    
    # Entity type filter
    if entity_type:
        sql += " AND e.entity_type = %s"
        params.append(entity_type)
    
    # Metadata filters
    if filters:
        if filters.get('city'):
            sql += " AND (e.metadata->>'city' ILIKE %s)"
            params.append(f"%{filters['city']}%")
        
        if filters.get('region'):
            sql += " AND (e.metadata->>'region' ILIKE %s)"
            params.append(f"%{filters['region']}%")
        
        if filters.get('specialty') and entity_type == 'facility':
            sql += " AND (e.metadata->'specialties' ? %s)"
            params.append(filters['specialty'])
    
    # Minimum similarity threshold
    sql += f" AND 1 - (e.embedding <=> %s::vector) >= %s"
    params.extend([json.dumps(query_embedding), min_similarity])
    
    # Order by similarity and limit
    sql += " ORDER BY e.embedding <=> %s::vector LIMIT %s"
    params.extend([json.dumps(query_embedding), top_k])
    
    cursor.execute(sql, params)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Format results
    formatted_results = []
    for row in results:
        result = {
            'id': row['entity_id'],
            'type': row['entity_type'],
            'similarity_score': float(row['similarity_score']),
            'metadata': row['metadata'],
            'entity_data': row['entity_data']
        }
        formatted_results.append(result)
    
    return formatted_results


def search_facilities_by_location(
    query: str,
    city: Optional[str] = None,
    region: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    Search facilities within a specific location
    
    Args:
        query: Natural language query
        city: Filter by city name
        region: Filter by region/state
        top_k: Number of results
        
    Returns:
        List of facility results
    """
    filters = {}
    if city:
        filters['city'] = city
    if region:
        filters['region'] = region
    
    return semantic_search(
        query=query,
        top_k=top_k,
        entity_type='facility',
        filters=filters
    )


def search_facilities_by_specialty(
    specialty: str,
    city: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    Search facilities offering specific medical specialty
    
    Args:
        specialty: Medical specialty (e.g., 'cardiology', 'ophthalmology')
        city: Optional city filter
        top_k: Number of results
        
    Returns:
        List of facility results
    """
    # Use specialty as the query
    query = f"medical facilities specializing in {specialty}"
    
    filters = {'specialty': specialty}
    if city:
        filters['city'] = city
    
    return semantic_search(
        query=query,
        top_k=top_k,
        entity_type='facility',
        filters=filters,
        min_similarity=0.3  # Lower threshold for specialty filtering
    )


def search_ngos_by_mission(
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """
    Search NGOs by mission alignment
    
    Args:
        query: Mission description or focus area
        top_k: Number of results
        
    Returns:
        List of NGO results
    """
    return semantic_search(
        query=query,
        top_k=top_k,
        entity_type='ngo'
    )


def format_search_results(results: List[Dict]) -> Dict:
    """
    Format search results for display or agent consumption
    
    Args:
        results: Raw search results from semantic_search
        
    Returns:
        Formatted results dictionary
    """
    formatted = []
    
    for result in results:
        entity = result['entity_data']
        
        formatted_result = {
            'id': result['id'],
            'name': entity.get('name'),
            'type': result['type'],
            'similarity_score': round(result['similarity_score'], 3),
            'location': {
                'city': entity.get('address_city'),
                'region': entity.get('address_state_or_region'),
                'country': entity.get('address_country', 'Ghana')
            }
        }
        
        # Add type-specific fields
        if result['type'] == 'facility':
            formatted_result.update({
                'facility_type': entity.get('facility_type_id'),
                'specialties': entity.get('specialties') or [],
                'capacity': entity.get('capacity'),
                'phone_numbers': entity.get('phone_numbers') or [],
                'email': entity.get('email'),
                'description': entity.get('description', '')[:200] if entity.get('description') else None
            })
        elif result['type'] == 'ngo':
            formatted_result.update({
                'mission': entity.get('mission_statement', '')[:200] if entity.get('mission_statement') else None,
                'countries': entity.get('countries') or [],
                'phone_numbers': entity.get('phone_numbers') or [],
                'email': entity.get('email')
            })
        
        formatted.append(formatted_result)
    
    return {
        'results': formatted,
        'total_results': len(formatted)
    }


def facility_search_tool(query: str, location: str = None) -> str:
    """
    LangGraph tool for searching facilities
    
    Args:
        query: Natural language query
        location: Optional city/region filter
        
    Returns:
        Formatted string for agent consumption
    """
    filters = {'city': location} if location else None
    
    results = semantic_search(
        query=query,
        top_k=5,
        entity_type='facility',
        filters=filters
    )
    
    formatted = format_search_results(results)
    
    # Convert to text for agent
    output = []
    for i, result in enumerate(formatted['results'], 1):
        output.append(f"{i}. {result['name']} ({result['facility_type'] or 'facility'})")
        output.append(f"   Location: {result['location']['city']}, {result['location']['region']}")
        output.append(f"   Similarity: {result['similarity_score']}")
        if result.get('specialties'):
            output.append(f"   Specialties: {', '.join(result['specialties'][:3])}")
        if result.get('description'):
            output.append(f"   Description: {result['description']}")
        output.append("")
    
    return "\n".join(output)


if __name__ == "__main__":
    # Quick test
    print("Testing RAG retrieval...")
    results = semantic_search("hospitals with ICU in Accra", top_k=3)
    formatted = format_search_results(results)
    
    print(f"\nFound {formatted['total_results']} results:")
    for result in formatted['results']:
        print(f"- {result['name']} (score: {result['similarity_score']})")
        print(f"  Location: {result['location']['city']}")
