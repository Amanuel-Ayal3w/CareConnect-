"""
Database schema setup for CareConnect.
Creates tables for facilities, NGOs, embeddings, and regions.
"""

CREATE_TABLES_SQL = """
-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Facilities table
CREATE TABLE IF NOT EXISTS facilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT,
    name TEXT NOT NULL,
    organization_type TEXT DEFAULT 'facility',
    
    -- Medical information
    specialties JSONB,
    procedures JSONB,
    equipment JSONB,
    capabilities JSONB,
    
    -- Contact information
    phone_numbers JSONB,
    email TEXT,
    websites JSONB,
    official_website TEXT,
    
    -- Address (flattened)
    address_line1 TEXT,
    address_line2 TEXT,
    address_line3 TEXT,
    address_city TEXT,
    address_state_or_region TEXT,
    address_zip_or_postcode TEXT,
    address_country TEXT,
    address_country_code TEXT,
    
    -- Geocoding
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    
    -- Facility-specific
    facility_type_id TEXT, -- hospital, clinic, pharmacy, doctor, dentist
    operator_type_id TEXT, -- public, private
    affiliation_type_ids JSONB,
    description TEXT,
    area INTEGER, -- square meters
    number_doctors INTEGER,
    capacity INTEGER, -- bed capacity
    
    -- Social media
    facebook_link TEXT,
    twitter_link TEXT,
    linkedin_link TEXT,
    instagram_link TEXT,
    logo TEXT,
    
    -- Metadata
    year_established INTEGER,
    accepts_volunteers BOOLEAN,
    source_id TEXT UNIQUE, -- unique ID from source data for deduplication
    
    -- AI-generated fields
    trust_score JSONB, -- AI confidence scores per capability
    verification_status TEXT, -- verified, pending, suspicious
    last_verified_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- NGOs table
CREATE TABLE IF NOT EXISTS ngos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT,
    name TEXT NOT NULL,
    organization_type TEXT DEFAULT 'ngo',
    
    -- Contact information
    phone_numbers JSONB,
    email TEXT,
    websites JSONB,
    official_website TEXT,
    
    -- Address
    address_line1 TEXT,
    address_line2 TEXT,
    address_line3 TEXT,
    address_city TEXT,
    address_state_or_region TEXT,
    address_zip_or_postcode TEXT,
    address_country TEXT,
    address_country_code TEXT,
    
    -- NGO-specific
    countries JSONB, -- ISO alpha-2 codes where NGO operates
    mission_statement TEXT,
    mission_statement_link TEXT,
    organization_description TEXT,
    
    -- Social media
    facebook_link TEXT,
    twitter_link TEXT,
    linkedin_link TEXT,
    instagram_link TEXT,
    logo TEXT,
    
    -- Metadata
    year_established INTEGER,
    accepts_volunteers BOOLEAN,
    source_id TEXT UNIQUE, -- unique ID from source data for deduplication
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings table for RAG (vector search)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL, -- facility or NGO id
    entity_type TEXT NOT NULL, -- 'facility' or 'ngo'
    content TEXT NOT NULL, -- text that was embedded
    embedding vector(1536), -- OpenAI text-embedding-3-small dimensions
    metadata JSONB, -- additional context
    created_at TIMESTAMP DEFAULT NOW()
);

-- Regions/Medical Deserts table
CREATE TABLE IF NOT EXISTS regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    region_type TEXT, -- city, state, district
    country_code TEXT,
    
    -- Geocoding
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    
    -- Aggregated metrics
    total_facilities INTEGER DEFAULT 0,
    total_ngos INTEGER DEFAULT 0,
    population INTEGER,
    
    -- Coverage metrics
    has_emergency_care BOOLEAN DEFAULT FALSE,
    has_icu BOOLEAN DEFAULT FALSE,
    has_trauma_care BOOLEAN DEFAULT FALSE,
    has_surgery BOOLEAN DEFAULT FALSE,
    
    -- Medical desert analysis
    is_medical_desert BOOLEAN DEFAULT FALSE,
    desert_severity TEXT, -- low, medium, high, critical
    missing_services JSONB,
    recommendations JSONB,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_facilities_city ON facilities(address_city);
CREATE INDEX IF NOT EXISTS idx_facilities_country ON facilities(address_country_code);
CREATE INDEX IF NOT EXISTS idx_facilities_type ON facilities(facility_type_id);
CREATE INDEX IF NOT EXISTS idx_facilities_operator ON facilities(operator_type_id);

CREATE INDEX IF NOT EXISTS idx_ngos_country ON ngos(address_country_code);

CREATE INDEX IF NOT EXISTS idx_embeddings_entity ON embeddings(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_regions_country ON regions(country_code);
CREATE INDEX IF NOT EXISTS idx_regions_desert ON regions(is_medical_desert);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_facilities_updated_at BEFORE UPDATE ON facilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ngos_updated_at BEFORE UPDATE ON ngos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_regions_updated_at BEFORE UPDATE ON regions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""

DROP_TABLES_SQL = """
DROP TABLE IF EXISTS embeddings CASCADE;
DROP TABLE IF EXISTS facilities CASCADE;
DROP TABLE IF EXISTS ngos CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
"""


def setup_database(conn):
    """
    Set up database schema using PostgreSQL connection
    
    Args:
        conn: PostgreSQL connection object
    """
    cursor = conn.cursor()
    
    try:
        print("Setting up database schema...")
        cursor.execute(CREATE_TABLES_SQL)
        conn.commit()
        print("✓ Database schema created successfully")
    except Exception as e:
        conn.rollback()
        print(f"✗ Error creating schema: {e}")
        raise
    finally:
        cursor.close()


def reset_database(conn):
    """
    Drop all tables and recreate schema (USE WITH CAUTION)
    
    Args:
        conn: PostgreSQL connection object
    """
    cursor = conn.cursor()
    
    try:
        print("Dropping existing tables...")
        cursor.execute(DROP_TABLES_SQL)
        conn.commit()
        print("✓ Tables dropped")
        
        print("Creating new schema...")
        cursor.execute(CREATE_TABLES_SQL)
        conn.commit()
        print("✓ Database reset successfully")
    except Exception as e:
        conn.rollback()
        print(f"✗ Error resetting database: {e}")
        raise
    finally:
        cursor.close()

