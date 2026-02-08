"""
Database configuration and connection for CareConnect.
Handles Supabase client and PostgreSQL connections.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration manager"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        # Validate required environment variables
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY in .env\n"
                "Get these from: Supabase Dashboard → Project Settings → API"
            )
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client for API operations"""
        return create_client(self.supabase_url, self.supabase_key)
    
    def get_postgres_connection(self):
        """Get direct PostgreSQL connection (if DATABASE_URL is set)"""
        if not self.database_url:
            raise ValueError("DATABASE_URL not set in .env")
        return psycopg2.connect(self.database_url)


# Global instances
_db_config: Optional[DatabaseConfig] = None


def get_database_config() -> DatabaseConfig:
    """Get or create database configuration singleton"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


# Convenience functions
def get_supabase() -> Client:
    """Quick access to Supabase client"""
    return get_database_config().get_supabase_client()


def get_postgres_connection():
    """Quick access to PostgreSQL connection"""
    return get_database_config().get_postgres_connection()
