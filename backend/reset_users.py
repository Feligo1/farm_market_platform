# reset_users.py
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid

DATABASE = 'farm_market.db'

def reset_users():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Delete all existing users
    cur.execute("DELETE FROM users")
    print("✅ Removed all existing users")
    
    # Create new admin user
    uid = str(uuid.uuid4())
    username = "Felix"
    password = "3969"
    password_hash = generate_password_hash(password)
    name = "Felix Daka"
    role = "admin"
    phone = "+260971234569"
    email = "felix.daka@mulungushi.ac.zm"
    location = "Lusaka"
    ussd_pin = "3969"
    
    try:
        cur.execute("""
            INSERT INTO users
            (user_id, username, password_hash, name, role, phone, email,
             location, farm_size, main_crops, business_name, license_number,
             trading_commodities, created_at, status, sms_alerts, ussd_pin)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (uid, username, password_hash, name, role, phone, email,
              location, None, None, None, None, None,
              datetime.now().isoformat(), 'active', 1, ussd_pin))
        
        print(f"✅ Created admin user:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Name: {name}")
        print(f"   Role: {role}")
        print(f"   USSD PIN: {ussd_pin}")
        
        conn.commit()
        
        # Verify the user was created
        cur.execute("SELECT username, name, role FROM users")
        users = cur.fetchall()
        print(f"\n📊 Total users in database: {len(users)}")
        for user in users:
            print(f"   - {user['username']} ({user['name']}) - {user['role']}")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("  Resetting Users - FarmConnect")
    print("=" * 50)
    reset_users()
    print("\n" + "=" * 50)