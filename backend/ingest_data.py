"""
Data Ingestion Pipeline for CareConnect
Loads CSV data of healthcare organizations into PostgreSQL database
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, List, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from uuid import uuid4

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def parse_json_field(value: str) -> Optional[List]:
    """Parse JSON string fields from CSV"""
    if pd.isna(value) or not value or value in ['[]', 'null', '']:
        return None
    
    try:
        # Handle stringified JSON
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        return None
    except (json.JSONDecodeError, ValueError):
        return None

def parse_facility(row: pd.Series) -> Dict:
    """Convert CSV row to facility dict"""
    return {
        'name': row['name'] if pd.notna(row['name']) else None,
        'organization_type': 'facility',
        'facility_type_id': row.get('facilityTypeId') if pd.notna(row.get('facilityTypeId')) else None,
        'operator_type_id': row.get('operatorTypeId') if pd.notna(row.get('operatorTypeId')) else None,
        'specialties': parse_json_field(row.get('specialties')),
        'procedures': parse_json_field(row.get('procedure')),
        'equipment': parse_json_field(row.get('equipment')),
        'capabilities': parse_json_field(row.get('capability')),
        'description': row.get('description') if pd.notna(row.get('description')) else None,
        'address_line1': row.get('address_line1') if pd.notna(row.get('address_line1')) else None,
        'address_line2': row.get('address_line2') if pd.notna(row.get('address_line2')) else None,
        'address_city': row.get('address_city') if pd.notna(row.get('address_city')) else None,
        'address_state_or_region': row.get('address_stateOrRegion') if pd.notna(row.get('address_stateOrRegion')) else None,
        'address_country': row.get('address_country', 'Ghana') if pd.notna(row.get('address_country')) else 'Ghana',
        'phone_numbers': parse_json_field(row.get('phone_numbers')),
        'email': row.get('email') if pd.notna(row.get('email')) else None,
        'websites': parse_json_field(row.get('websites')),
        'official_website': row.get('officialWebsite') if pd.notna(row.get('officialWebsite')) else None,
        'year_established': int(row['yearEstablished']) if pd.notna(row.get('yearEstablished')) else None,
        'capacity': int(row['capacity']) if pd.notna(row.get('capacity')) else None,
        'area': row.get('area') if pd.notna(row.get('area')) else None,
        'number_doctors': int(row['numberDoctors']) if pd.notna(row.get('numberDoctors')) else None,
        'source_url': row.get('source_url') if pd.notna(row.get('source_url')) else None,
        'source_id': row.get('unique_id') if pd.notna(row.get('unique_id')) else str(uuid4()),
    }
def parse_ngo(row: pd.Series) -> Dict:
    """Convert CSV row to NGO dict"""
    return {
        'name': row['name'] if pd.notna(row['name']) else None,
        'organization_type': 'ngo',
        'countries': parse_json_field(row.get('countries')),
        'mission_statement': row.get('missionStatement') if pd.notna(row.get('missionStatement')) else None,
        'organization_description': row.get('organizationDescription') if pd.notna(row.get('organizationDescription')) else None,
        'address_line1': row.get('address_line1') if pd.notna(row.get('address_line1')) else None,
        'address_line2': row.get('address_line2') if pd.notna(row.get('address_line2')) else None,
        'address_city': row.get('address_city') if pd.notna(row.get('address_city')) else None,
        'address_state_or_region': row.get('address_stateOrRegion') if pd.notna(row.get('address_stateOrRegion')) else None,
        'address_country': row.get('address_country', 'Ghana') if pd.notna(row.get('address_country')) else 'Ghana',
        'phone_numbers': parse_json_field(row.get('phone_numbers')),
        'email': row.get('email') if pd.notna(row.get('email')) else None,
        'websites': parse_json_field(row.get('websites')),
        'official_website': row.get('officialWebsite') if pd.notna(row.get('officialWebsite')) else None,
        'year_established': int(row['yearEstablished']) if pd.notna(row.get('yearEstablished')) else None,
        'accepts_volunteers': row.get('acceptsVolunteers') if pd.notna(row.get('acceptsVolunteers')) else None,
        'facebook_link': row.get('facebookLink') if pd.notna(row.get('facebookLink')) else None,
        'twitter_link': row.get('twitterLink') if pd.notna(row.get('twitterLink')) else None,
        'linkedin_link': row.get('linkedinLink') if pd.notna(row.get('linkedinLink')) else None,
        'source_url': row.get('source_url') if pd.notna(row.get('source_url')) else None,
        'source_id': row.get('unique_id') if pd.notna(row.get('unique_id')) else str(uuid4()),
    }

def load_csv(csv_path: str) -> pd.DataFrame:
    """Load CSV file into pandas DataFrame"""
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"✓ Loaded {len(df)} rows")
    return df

def insert_facilities(conn, facilities: List[Dict]) -> int:
    """Batch insert facilities into database"""
    if not facilities:
        return 0
    
    cursor = conn.cursor()
    
    # Prepare data for batch insert
    values = [
        (
            f['name'],
            f['organization_type'],
            f.get('facility_type_id'),
            f.get('operator_type_id'),
            json.dumps(f['specialties']) if f['specialties'] else None,
            json.dumps(f['procedures']) if f['procedures'] else None,
            json.dumps(f['equipment']) if f['equipment'] else None,
            json.dumps(f['capabilities']) if f['capabilities'] else None,
            f.get('description'),
            f.get('address_line1'),
            f.get('address_line2'),
            f.get('address_city'),
            f.get('address_state_or_region'),
            f.get('address_country'),
            json.dumps(f['phone_numbers']) if f['phone_numbers'] else None,
            f.get('email'),
            json.dumps(f['websites']) if f['websites'] else None,
            f.get('official_website'),
            f.get('year_established'),
            f.get('capacity'),
            f.get('area'),
            f.get('number_doctors'),
            f.get('source_url'),
            f.get('source_id')
        )
        for f in facilities
    ]
    
    query = """
        INSERT INTO facilities (
            name, organization_type, facility_type_id, operator_type_id,
            specialties, procedures, equipment, capabilities, description,
            address_line1, address_line2, address_city, address_state_or_region, address_country,
            phone_numbers, email, websites, official_website,
            year_established, capacity, area, number_doctors,
            source_url, source_id
        ) VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
            name = EXCLUDED.name,
            specialties = EXCLUDED.specialties,
            updated_at = NOW()
    """
    
    execute_values(cursor, query, values)
    inserted = cursor.rowcount
    conn.commit()
    cursor.close()
    
    return inserted

def insert_ngos(conn, ngos: List[Dict]) -> int:
    """Batch insert NGOs into database"""
    if not ngos:
        return 0
    
    cursor = conn.cursor()
    
    # Prepare data for batch insert
    values = [
        (
            n['name'],
            n['organization_type'],
            json.dumps(n['countries']) if n['countries'] else None,
            n.get('mission_statement'),
            n.get('organization_description'),
            n.get('address_line1'),
            n.get('address_line2'),
            n.get('address_city'),
            n.get('address_state_or_region'),
            n.get('address_country'),
            json.dumps(n['phone_numbers']) if n['phone_numbers'] else None,
            n.get('email'),
            json.dumps(n['websites']) if n['websites'] else None,
            n.get('official_website'),
            n.get('year_established'),
            n.get('accepts_volunteers'),
            n.get('facebook_link'),
            n.get('twitter_link'),
            n.get('linkedin_link'),
            n.get('source_url'),
            n.get('source_id')
        )
        for n in ngos
    ]
    
    query = """
        INSERT INTO ngos (
            name, organization_type, countries, mission_statement, organization_description,
            address_line1, address_line2, address_city, address_state_or_region, address_country,
            phone_numbers, email, websites, official_website,
            year_established, accepts_volunteers,
            facebook_link, twitter_link, linkedin_link,
            source_url, source_id
        ) VALUES %s
        ON CONFLICT (source_id) DO UPDATE SET
            name = EXCLUDED.name,
            mission_statement = EXCLUDED.mission_statement,
            updated_at = NOW()
    """
    
    execute_values(cursor, query, values)
    inserted = cursor.rowcount
    conn.commit()
    cursor.close()
    
    return inserted

def main(dry_run: bool = False):
    """Main ingestion pipeline"""
    csv_path = "Virtue Foundation Ghana v0.3 - Sheet1.csv"
    
    # Load CSV
    df = load_csv(csv_path)
    
    # Separate facilities and NGOs
    facilities_df = df[df['organization_type'] == 'facility']
    ngos_df = df[df['organization_type'] == 'ngo']
    
    print(f"\n📊 Data Summary:")
    print(f"   Total rows: {len(df)}")
    print(f"   Facilities: {len(facilities_df)}")
    print(f"   NGOs: {len(ngos_df)}")
    
    if dry_run:
        print("\n✓ Dry run complete - no data inserted")
        return
    
    # Connect to database
    print(f"\nConnecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        # Parse and insert facilities
        print(f"\nParsing {len(facilities_df)} facilities...")
        facilities = []
        for _, row in facilities_df.iterrows():
            try:
                facilities.append(parse_facility(row))
            except Exception as e:
                print(f"  ⚠ Skipped row {row.get('pk_unique_id')}: {e}")
        
        print(f"Inserting {len(facilities)} facilities...")
        inserted_facilities = insert_facilities(conn, facilities)
        print(f"✓ Inserted/updated {inserted_facilities} facilities")
        
        # Parse and insert NGOs
        print(f"\nParsing {len(ngos_df)} NGOs...")
        ngos = []
        for _, row in ngos_df.iterrows():
            try:
                ngos.append(parse_ngo(row))
            except Exception as e:
                print(f"  ⚠ Skipped row {row.get('pk_unique_id')}: {e}")
        
        print(f"Inserting {len(ngos)} NGOs...")
        inserted_ngos = insert_ngos(conn, ngos)
        print(f"✓ Inserted/updated {inserted_ngos} NGOs")
        
        print(f"\n{'='*60}")
        print(f"✓ Data ingestion complete!")
        print(f"{'='*60}")
        print(f"  Facilities: {inserted_facilities}")
        print(f"  NGOs: {inserted_ngos}")
        print(f"  Total: {inserted_facilities + inserted_ngos}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest CSV data into PostgreSQL")
    parser.add_argument('--dry-run', action='store_true', help='Parse CSV without inserting to database')
    args = parser.parse_args()
    
    main(dry_run=args.dry_run)
