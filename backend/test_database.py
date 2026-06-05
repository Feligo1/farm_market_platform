# test_database.py
import sqlite3
import os

DATABASE = "farm_market.db"

def check_database():
    """Check database structure and content"""
    if not os.path.exists(DATABASE):
        print("❌ Database file not found!")
        return False
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 60)
    print("📊 DATABASE CHECK")
    print("=" * 60)
    
    # Get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    
    print(f"📁 Database: {DATABASE}")
    print(f"📋 Total tables: {len(tables)}")
    print("\nTables found:")
    for table in tables:
        table_name = table['name']
        print(f"  • {table_name}")
        
        # Get row count
        try:
            cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cur.fetchone()['count']
            print(f"    - Rows: {count}")
            
            # Get column names for key tables
            if table_name in ['market_prices', 'users', 'buyers']:
                cur.execute(f"PRAGMA table_info({table_name})")
                columns = cur.fetchall()
                col_names = [col[1] for col in columns]
                print(f"    - Columns: {', '.join(col_names[:5])}...")
        except:
            print(f"    - (Could not read table)")
    
    print("\n" + "=" * 60)
    
    # Check specific data
    print("\n🔍 KEY DATA CHECKS:")
    
    # Market prices
    try:
        cur.execute("SELECT COUNT(*) as count FROM market_prices")
        price_count = cur.fetchone()['count']
        print(f"  • Market Prices: {price_count}")
        
        cur.execute("SELECT DISTINCT commodity FROM market_prices LIMIT 5")
        commodities = cur.fetchall()
        if commodities:
            print(f"    Commodities: {', '.join([c['commodity'] for c in commodities])}")
    except:
        print("  • Market Prices: Table not found")
    
    # Users
    try:
        cur.execute("SELECT COUNT(*) as count FROM users")
        user_count = cur.fetchone()['count']
        print(f"  • Users: {user_count}")
    except:
        print("  • Users: Table not found")
    
    # Buyers
    try:
        cur.execute("SELECT COUNT(*) as count FROM buyers")
        buyer_count = cur.fetchone()['count']
        print(f"  • Buyers: {buyer_count}")
    except:
        print("  • Buyers: Table not found")
    
    # USSD tables
    try:
        cur.execute("SELECT COUNT(*) as count FROM ussd_sessions")
        session_count = cur.fetchone()['count']
        print(f"  • USSD Sessions: {session_count}")
    except:
        print("  • USSD Sessions: Table not found")
    
    conn.close()
    print("\n" + "=" * 60)
    return True

# Also test the USSD app connection
def test_ussd_connection():
    """Test if USSD app can connect to database"""
    print("\n📱 USSD APP CONNECTION TEST")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        # Test market prices query (what USSD uses)
        cur.execute("SELECT commodity, price, market FROM market_prices WHERE verified=1 LIMIT 3")
        results = cur.fetchall()
        
        if results:
            print("✅ USSD can access market prices")
            for row in results:
                print(f"   • {row[0]}: {row[1]} at {row[2]}")
        else:
            print("⚠️  No market prices found (USSD will use sample data)")
        
        # Test buyers query
        cur.execute("SELECT name, commodity FROM buyers WHERE status='active' LIMIT 3")
        buyers = cur.fetchall()
        
        if buyers:
            print("✅ USSD can access buyers")
            for buyer in buyers:
                print(f"   • {buyer[0]} buys {buyer[1]}")
        
        conn.close()
        print("\n✅ Database connection successful!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    check_database()
    test_ussd_connection()