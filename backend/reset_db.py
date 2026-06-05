# reset_db.py
import os
import sqlite3
import time

DATABASE = "farm_market.db"

def reset_database():
    # Wait a moment to ensure database is not locked
    time.sleep(1)
    
    # Close any existing connections
    try:
        conn = sqlite3.connect(DATABASE)
        conn.close()
        print("✅ Closed database connection")
    except:
        pass
    
    # Delete the database file
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"🗑️  Deleted {DATABASE}")
    
    # Recreate with simple schema
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Create basic tables
    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            username TEXT UNIQUE,
            password_hash TEXT,
            name TEXT,
            role TEXT,
            phone TEXT,
            email TEXT,
            location TEXT,
            farm_size REAL,
            main_crops TEXT,
            business_name TEXT,
            license_number TEXT,
            trading_commodities TEXT,
            created_at TEXT,
            last_login TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    cur.execute("""
        CREATE TABLE prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market TEXT,
            commodity TEXT,
            price REAL,
            volume REAL,
            notes TEXT,
            verified BOOLEAN DEFAULT 0,
            added_by TEXT,
            recorded_at TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE buyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            commodity TEXT,
            location TEXT,
            max_price REAL,
            min_volume REAL,
            notes TEXT,
            verified BOOLEAN DEFAULT 0,
            rating REAL DEFAULT 4.0,
            added_by TEXT,
            created_at TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            commodity TEXT,
            target_price REAL,
            alert_type TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TEXT
        )
    """)
    
    # Add demo users
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    import uuid
    import random
    
    demo_users = [
        ('farmer1', generate_password_hash('farmer123'), 'John Farmer', 'farmer', '+260971234567', 'john@example.com', 'Lusaka', 10.5, 'Maize, Tomatoes'),
        ('trader1', generate_password_hash('trader123'), 'Sarah Trader', 'trader', '+260971234568', 'sarah@example.com', 'Kabwe', None, None, 'Agri Trading Ltd'),
        ('admin1', generate_password_hash('admin123'), 'Admin User', 'admin', '+260971234569', 'admin@example.com', 'Ndola')
    ]
    
    for username, pwd_hash, name, role, phone, email, location, farm_size, crops, business in demo_users:
        user_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (user_id, username, password_hash, name, role, phone, email, location, farm_size, main_crops, business_name, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, pwd_hash, name, role, phone, email, location, farm_size, crops, business, datetime.now().isoformat(), 'active'))
    
    # Add demo prices
    markets = ['Lusaka Central', 'Kabwe Main', 'Ndola Market']
    commodities = ['Maize', 'Tomatoes', 'Beans']
    
    for i in range(20):
        market = random.choice(markets)
        commodity = random.choice(commodities)
        price = round(random.uniform(50, 250), 2)
        volume = random.randint(500, 3000)
        
        cur.execute("""
            INSERT INTO prices (market, commodity, price, volume, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (market, commodity, price, volume, datetime.now().isoformat()))
    
    # Add demo buyers
    demo_buyers = [
        ('Agri Trading Ltd', '+260971111111', 'Maize', 'Lusaka', 140.0, 1000, 'Bulk buyer', 1, 4.5),
        ('Fresh Produce Co.', '+260972222222', 'Tomatoes', 'Kabwe', 90.0, 500, 'Daily collection', 1, 4.2),
        ('Grain Masters', '+260973333333', 'Maize', 'Ndola', 135.0, 2000, 'Weekly orders', 0, 3.8)
    ]
    
    for name, phone, commodity, location, max_price, min_volume, notes, verified, rating in demo_buyers:
        cur.execute("""
            INSERT INTO buyers (name, phone, commodity, location, max_price, min_volume, notes, verified, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, phone, commodity, location, max_price, min_volume, notes, verified, rating, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    print("✅ Database reset successfully with simple schema!")
    print("👤 Demo users created:")
    print("   - farmer1 / farmer123")
    print("   - trader1 / trader123")
    print("   - admin1 / admin123")

if __name__ == "__main__":
    reset_database()