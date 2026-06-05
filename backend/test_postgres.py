# test_postgres.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing PostgreSQL Connection...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"Port: {os.getenv('DB_PORT')}")
print(f"Database: {os.getenv('DB_NAME')}")
print(f"User: {os.getenv('DB_USER')}")

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'farmconnect_db'),
        user=os.getenv('DB_USER', 'farmconnect_user'),
        password=os.getenv('DB_PASSWORD', 'FarmConnect2024!')
    )
    print("\n✅ Connected to PostgreSQL successfully!")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT version()")
    version = cur.fetchone()
    print(f"PostgreSQL Version: {version['version']}")
    
    cur.execute("SELECT current_database()")
    db = cur.fetchone()
    print(f"Current Database: {db['current_database']}")
    
    cur.close()
    conn.close()
    print("\n✅ All good! Ready to run your app.")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nPlease ensure:")
    print("1. PostgreSQL is installed and running")
    print("2. Database 'farmconnect_db' exists")
    print("3. User 'farmconnect_user' has access")
    print("4. Password is correct")