#!/usr/bin/env python3
"""
Database Setup Script for FarmConnect
Run this to initialize the database with schema and seed data
"""

import os
import sys
import sqlite3
from datetime import datetime

def setup_database():
    """Initialize the database with schema and seed data"""
    
    db_path = "farm_market.db"
    
    # Remove existing database if it exists and --force is used
    if os.path.exists(db_path):
        if '--force' in sys.argv:
            os.remove(db_path)
            print(f"✅ Removed existing database: {db_path}")
        else:
            print(f"⚠️ Database already exists at {db_path}")
            response = input("Do you want to recreate it? (y/N): ")
            if response.lower() == 'y':
                os.remove(db_path)
                print(f"✅ Removed existing database: {db_path}")
            else:
                print("Exiting without changes.")
                return False
    
    # Read and execute schema
    schema_path = "database_schema.sql"
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        print("   Make sure database_schema.sql is in the current directory")
        return False
    
    print(f"📖 Loading schema from {schema_path}...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_sql)
        print("✅ Schema created successfully")
        conn.close()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Read and execute seed data
    seed_path = "seed_data.sql"
    if os.path.exists(seed_path):
        print(f"📖 Loading seed data from {seed_path}...")
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_sql = f.read()
        
        try:
            conn = sqlite3.connect(db_path)
            conn.executescript(seed_sql)
            print("✅ Seed data loaded successfully")
            conn.close()
        except sqlite3.Error as e:
            print(f"⚠️ Seed data error: {e}")
            print("   Continuing with schema only...")
    else:
        print(f"⚠️ Seed file not found: {seed_path}")
        print("   Creating database with schema only...")
    
    # Verify database
    print("\n" + "=" * 50)
    print("DATABASE VERIFICATION")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 {len(tables)} tables created:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   📋 {table}: {count} rows")
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"\n🔍 {len(indexes)} indexes created")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ DATABASE SETUP COMPLETE!")
    print("=" * 50)
    print(f"   Database file: {db_path}")
    print(f"   Size: {os.path.getsize(db_path) / 1024:.2f} KB")
    print("\n📝 Demo credentials:")
    print("   👨‍🌾 Farmer:  farmer1 / farmer123")
    print("   👨‍💼 Trader:  trader1 / trader123")
    print("   👨‍💻 Admin:   admin1 / admin123")
    print("\n📞 USSD Code: *384*7321#")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   FARMCONNECT DATABASE SETUP")
    print("   Mulungushi University - ICT 431")
    print("   Student: Daka Felix (202206453)")
    print("=" * 50 + "\n")
    
    success = setup_database()
    
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)