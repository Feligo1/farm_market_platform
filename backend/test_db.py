import psycopg2

print("=" * 50)
print("Testing PostgreSQL Connection")
print("=" * 50)

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="farmconnect_db",
        user="farmconnect_user",
        password="56451051",
        connect_timeout=10
    )
    print("✅ Connected to PostgreSQL successfully!")
    
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()
    print(f"📦 Version: {version[0][:60]}...")
    
    cur.execute("SELECT current_database(), current_user")
    db_info = cur.fetchone()
    print(f"💾 Database: {db_info[0]}")
    print(f"👤 User: {db_info[1]}")
    
    cur.close()
    conn.close()
    
    print("\n✅ SUCCESS! Your database is ready!")
    print("\nNow run: python app.py")
    
except Exception as e:
    print(f"❌ Error: {e}")