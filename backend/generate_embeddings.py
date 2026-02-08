"""
Generate embeddings for facilities and NGOs using OpenAI
Stores vectors in pgvector for RAG similarity search
"""

import os
import sys
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

def create_content_for_embedding(entity: Dict, entity_type: str) -> str:
    """
    Create rich searchable text content from entity data
    Combines name, specialties, procedures, description, location
    """
    parts = []
    
    # Name and type
    parts.append(entity['name'])
    parts.append(f"Type: {entity_type}")
    
    if entity_type == 'facility':
        # Facility type
        if entity.get('facility_type_id'):
            parts.append(f"Facility type: {entity['facility_type_id']}")
        
        # Specialties
        if entity.get('specialties'):
            try:
                specialties = json.loads(entity['specialties']) if isinstance(entity['specialties'], str) else entity['specialties']
                if specialties:
                    parts.append(f"Specialties: {', '.join(specialties[:10])}")
            except:
                pass
        
        # Procedures
        if entity.get('procedures'):
            try:
                procedures = json.loads(entity['procedures']) if isinstance(entity['procedures'], str) else entity['procedures']
                if procedures:
                    parts.append(f"Procedures: {', '.join(procedures[:10])}")
            except:
                pass
        
        # Equipment
        if entity.get('equipment'):
            try:
                equipment = json.loads(entity['equipment']) if isinstance(entity['equipment'], str) else entity['equipment']
                if equipment:
                    parts.append(f"Equipment: {', '.join(equipment[:5])}")
            except:
                pass
        
        # Capacity
        if entity.get('capacity'):
            parts.append(f"Capacity: {entity['capacity']} beds")
    
    elif entity_type == 'ngo':
        # Mission statement (truncate to 200 chars)
        if entity.get('mission_statement'):
            mission = entity['mission_statement'][:200]
            parts.append(f"Mission: {mission}")
        
        # Organization description
        if entity.get('organization_description'):
            desc = entity['organization_description'][:200]
            parts.append(f"Description: {desc}")
    
    # Location
    location_parts = []
    if entity.get('address_city'):
        location_parts.append(entity['address_city'])
    if entity.get('address_state_or_region'):
        location_parts.append(entity['address_state_or_region'])
    if entity.get('address_country'):
        location_parts.append(entity['address_country'])
    
    if location_parts:
        parts.append(f"Location: {', '.join(location_parts)}")
    
    # Description
    if entity.get('description') and entity_type == 'facility':
        desc = entity['description'][:300]
        parts.append(f"Description: {desc}")
    
    return "\n".join(parts)

def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using OpenAI
    Returns list of embedding vectors
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    
    return [item.embedding for item in response.data]

def fetch_entities(conn, entity_type: str, limit: Optional[int] = None) -> List[Dict]:
    """Fetch facilities or NGOs from database"""
    cursor = conn.cursor()
    
    table = 'facilities' if entity_type == 'facility' else 'ngos'
    
    # Check what's already embedded
    query = f"""
        SELECT e.* 
        FROM {table} e
        LEFT JOIN embeddings emb ON emb.entity_id = e.id
        WHERE emb.id IS NULL
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    entities = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    cursor.close()
    return entities

def store_embeddings(conn, embeddings_data: List[Dict]):
    """Batch insert embeddings into database"""
    if not embeddings_data:
        return 0
    
    cursor = conn.cursor()
    
    values = [
        (
            e['entity_id'],
            e['entity_type'],
            e['content'],
            json.dumps(e['embedding']),  # Store as JSON
            json.dumps(e['metadata'])
        )
        for e in embeddings_data
    ]
    
    query = """
        INSERT INTO embeddings (
            entity_id, entity_type, content, embedding, metadata
        ) VALUES %s
    """
    
    execute_values(cursor, query, values)
    inserted = cursor.rowcount
    conn.commit()
    cursor.close()
    
    return inserted

def process_entities(conn, entity_type: str, batch_size: int = 100, limit: Optional[int] = None):
    """
    Process entities: fetch, generate embeddings, store
    """
    print(f"\nFetching {entity_type}s...")
    entities = fetch_entities(conn, entity_type, limit=limit)
    
    if not entities:
        print(f"No new {entity_type}s to embed")
        return 0
    
    print(f"✓ Found {len(entities)} {entity_type}s to embed")
    
    total_inserted = 0
    
    # Process in batches
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(entities) + batch_size - 1) // batch_size
        
        print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
        
        # Create content strings
        contents = [create_content_for_embedding(e, entity_type) for e in batch]
        
        # Generate embeddings
        try:
            embeddings = generate_embeddings_batch(contents)
        except Exception as e:
            print(f"  ✗ Error generating embeddings: {e}")
            continue
        
        # Prepare data for storage
        embeddings_data = []
        for entity, content, embedding in zip(batch, contents, embeddings):
            metadata = {
                'name': entity['name'],
                'type': entity_type,
                'city': entity.get('address_city'),
                'region': entity.get('address_state_or_region'),
            }
            
            if entity_type == 'facility' and entity.get('specialties'):
                try:
                    specialties = json.loads(entity['specialties']) if isinstance(entity['specialties'], str) else entity['specialties']
                    metadata['specialties'] = specialties[:5] if specialties else []
                except:
                    pass
            
            embeddings_data.append({
                'entity_id': entity['id'],
                'entity_type': entity_type,
                'content': content,
                'embedding': embedding,
                'metadata': metadata
            })
        
        # Store in database
        inserted = store_embeddings(conn, embeddings_data)
        total_inserted += inserted
        print(f"  ✓ Stored {inserted} embeddings")
    
    return total_inserted

def main(limit: Optional[int] = None):
    """Main pipeline for generating embeddings"""
    print("============================================================")
    print("CareConnect Embedding Generation")
    print("============================================================")
    
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        # Process facilities
        facilities_count = process_entities(conn, 'facility', limit=limit)
        
        # Process NGOs
        ngoscount = process_entities(conn, 'ngo', limit=limit)
        
        print(f"\n{'='*60}")
        print(f"✓ Embedding generation complete!")
        print(f"{'='*60}")
        print(f"  Facilities: {facilities_count}")
        print(f"  NGOs: {ngoscount}")
        print(f"  Total: {facilities_count + ngoscount}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate embeddings for RAG")
    parser.add_argument('--limit', type=int, help='Limit number of entities to process (for testing)')
    args = parser.parse_args()
    
    main(limit=args.limit)
