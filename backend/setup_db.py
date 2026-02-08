"""
Database setup CLI tool for CareConnect.
Run this script to initialize the database schema.

Usage:
    python backend/setup_db.py              # Interactive setup
    python backend/setup_db.py --setup      # Auto setup
    python backend/setup_db.py --reset      # Reset database (CAUTION!)
    python backend/setup_db.py --test-connection  # Test connection only
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_database_config
from backend.schema import setup_database, reset_database


def test_connection():
    """Test database connection"""
    print("Testing database connection...")
    
    try:
        config = get_database_config()
        print(f"✓ Environment variables loaded")
        
        # Test Supabase connection
        supabase = config.get_supabase_client()
        print(f"✓ Supabase client connected to: {config.supabase_url}")
        
        # Test PostgreSQL connection
        conn = config.get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL connected: {version[:60]}...")
        cursor.close()
        conn.close()
        
        print("\n✓ All connections successful!")
        return True
    
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease create a .env file with:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_KEY=your_anon_key")
        print("  DATABASE_URL=postgresql://...")
        return False
    
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        return False


def run_setup():
    """Run database setup"""
    print("=" * 60)
    print("CareConnect Database Setup")
    print("=" * 60)
    
    if not test_connection():
        return False
    
    print("\nSetting up database schema...")
    
    try:
        config = get_database_config()
        conn = config.get_postgres_connection()
        
        # Create main schema
        setup_database(conn)
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ Database setup complete!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. View tables in Supabase dashboard")
        print("  2. Run data ingestion: python backend/ingest_data.py")
        print("  3. Start the LangGraph agents")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_reset():
    """Reset database (CAUTION!)"""
    print("=" * 60)
    print("WARNING: Database Reset")
    print("=" * 60)
    print("\nThis will DELETE ALL DATA and recreate the schema.")
    
    response = input("\nAre you sure? Type 'yes' to continue: ")
    
    if response.lower() != 'yes':
        print("Reset cancelled.")
        return False
    
    try:
        config = get_database_config()
        conn = config.get_postgres_connection()
        
        reset_database(conn)
        
        conn.close()
        
        print("\n✓ Database reset complete!")
        return True
    
    except Exception as e:
        print(f"\n✗ Reset failed: {e}")
        return False


def interactive_setup():
    """Interactive setup wizard"""
    print("=" * 60)
    print("CareConnect Database Setup Wizard")
    print("=" * 60)
    
    # Check for .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("\n.env file not found!")
        print("\nPlease create a .env file with your Supabase credentials.")
        print("You can copy .env.example and fill in your values:")
        print("  cp .env.example .env")
        print("  # Then edit .env with your credentials")
        return False
    
    print("\nWhat would you like to do?")
    print("1. Test connection")
    print("2. Set up database (create tables)")
    print("3. Reset database (CAUTION: deletes all data)")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        return test_connection()
    elif choice == "2":
        return run_setup()
    elif choice == "3":
        return run_reset()
    elif choice == "4":
        print("Exiting...")
        return True
    else:
        print("Invalid choice")
        return False


def main():
    parser = argparse.ArgumentParser(description="CareConnect Database Setup")
    parser.add_argument("--setup", action="store_true", help="Run database setup")
    parser.add_argument("--reset", action="store_true", help="Reset database (CAUTION!)")
    parser.add_argument("--test-connection", action="store_true", help="Test connection only")
    
    args = parser.parse_args()
    
    if args.test_connection:
        success = test_connection()
    elif args.setup:
        success = run_setup()
    elif args.reset:
        success = run_reset()
    else:
        success = interactive_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


def test_connection():
    """Test Supabase connection"""
    print("Testing Supabase connection...\n")
    
    try:
        supabase = get_supabase()
        print("✓ Supabase client initialized successfully!")
        print(f"✓ Connected to project")
        
        # Try to query a simple health check
        try:
            # List existing tables
            result = supabase.table('facilities').select("count", count='exact').limit(0).execute()
            print(f"✓ Database accessible (facilities table exists with {result.count} rows)")
        except Exception as e:
            if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                print("⚠️  Tables not yet created. Run setup instructions below.")
            else:
                print(f"⚠️  Could not query database: {e}")
        
        print("\n" + "="*80)
        print("CONNECTION SUCCESSFUL!")
        print("="*80)
        return True
    
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease check your .env file has:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_KEY=your-anon-key")
        return False
    
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def show_sql():
    """Print the SQL schema"""
    print("="*80)
    print("SUPABASE SQL SCHEMA FOR CARECONNECT")
    print("="*80)
    print("\nCopy and paste this into Supabase SQL Editor:\n")
    print(SETUP_SQL)
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="CareConnect Database Setup (Supabase Free Tier)")
    parser.add_argument("--test", action="store_true", help="Test Supabase connection")
    parser.add_argument("--sql", action="store_true", help="Print SQL schema")
    
    args = parser.parse_args()
    
    if args.test:
        success = test_connection()
        sys.exit(0 if success else 1)
    elif args.sql:
        show_sql()
        sys.exit(0)
    else:
        print(get_setup_instructions())
        sys.exit(0)


if __name__ == "__main__":
    main()
