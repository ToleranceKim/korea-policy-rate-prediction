#!/usr/bin/env python3
"""
PostgreSQL connection test script for MPB Stance Mining project
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.db_insert_dohy import PostgreSQLInserter

def test_connection():
    """Test PostgreSQL database connection"""
    try:
        print("Testing PostgreSQL connection...")
        
        with PostgreSQLInserter() as db:
            # Test basic connection
            result = db.execute_query("SELECT version()")
            print(f"✅ Connection successful!")
            print(f"PostgreSQL version: {result[0]['version']}")
            
            # Test if our database exists
            db_check = db.execute_query(
                "SELECT current_database() as db_name, current_user as user_name"
            )
            print(f"✅ Database: {db_check[0]['db_name']}")
            print(f"✅ User: {db_check[0]['user_name']}")
            
            # Check if our tables exist
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
            tables = db.execute_query(tables_query)
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table['table_name']}")
            else:
                print("⚠️  No tables found. Run 'psql -f database/schema.sql' to initialize.")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running:")
        print("   brew services start postgresql")
        print("2. Create the database:")
        print("   createdb mpb_stance_mining")
        print("3. Copy and edit .env file:")
        print("   cp .env.example .env")
        print("4. Initialize the schema:")
        print("   psql -U postgres -d mpb_stance_mining -f database/schema.sql")
        return False

def test_basic_operations():
    """Test basic database operations"""
    try:
        print("\nTesting basic operations...")
        
        with PostgreSQLInserter() as db:
            # Test insert operation
            test_data = {
                'source_name': 'Test Source',
                'source_code': 'test',
                'description': 'Test data source for connection testing'
            }
            
            # Check if test data already exists
            existing = db.execute_query(
                "SELECT id FROM data_sources WHERE source_code = %s", 
                ('test',)
            )
            
            if not existing:
                db.insert_one('data_sources', test_data)
                print("✅ Insert operation successful")
            else:
                print("✅ Test data already exists")
            
            # Test select operation
            result = db.execute_query(
                "SELECT * FROM data_sources WHERE source_code = %s", 
                ('test',)
            )
            
            if result:
                print("✅ Select operation successful")
                print(f"   Retrieved: {result[0]['source_name']}")
            
            # Clean up test data
            db.execute_query(
                "DELETE FROM data_sources WHERE source_code = %s", 
                ('test',)
            )
            print("✅ Delete operation successful")
            
            return True
            
    except Exception as e:
        print(f"❌ Basic operations failed: {e}")
        return False

def main():
    """Main test function"""
    print("🐘 PostgreSQL Connection Test for MPB Stance Mining")
    print("=" * 50)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Test basic operations
    if not test_basic_operations():
        sys.exit(1)
    
    print("\n🎉 All tests passed! Database is ready for use.")
    print("\nNext steps:")
    print("1. Run crawlers to collect data")
    print("2. Process and clean text data")
    print("3. Perform n-gram analysis")
    print("4. Train and evaluate models")

if __name__ == "__main__":
    main()