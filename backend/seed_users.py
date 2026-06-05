# seed_users.py
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid

DATABASE = 'farm_market.db'

def seed_users():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Check if users exist
    cur.execute("SELECT COUNT(*) as count FROM users")
    count = cur.fetchone()[0]
    
    if count == 0:
        print("Seeding demo users...")
        demo_users = [
            ('farmer1', generate_password_hash('farmer123'), 'John Farmer',
             'farmer', '+260971234567', 'john@example.com', 'Lusaka',
             10.5, 'Maize, Tomatoes', None, None, None, '1234'),
            ('trader1', generate_password_hash('trader123'), 'Sarah Trader',
             'trader', '+260971234568', 'sarah@example.com', 'Kabwe',
             None, None, 'Agri Trading Ltd', 'LIC-2024-001', 'Maize, Beans', '5678'),
            ('admin1',  generate_password_hash('admin123'),  'Admin User',
             'admin',  '+260971234569', 'admin@example.com', 'Ndola',
             None, None, None, None, None, '9999'),
        ]
        
        for u in demo_users:
            uid = str(uuid.uuid4())
            try:
                cur.execute("""
                    INSERT INTO users
                    (user_id, username, password_hash, name, role, phone, email,
                     location, farm_size, main_crops, business_name, license_number,
                     trading_commodities, created_at, status, sms_alerts, ussd_pin)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (uid, u[0], u[1], u[2], u[3], u[4], u[5], u[6],
                      u[7], u[8], u[9], u[10], u[11],
                      datetime.now().isoformat(), 'active', 1, u[12]))
                print(f"  ✅ Created user: {u[0]}")
            except Exception as e:
                print(f"  ❌ Error creating {u[0]}: {e}")
        
        conn.commit()
        print("\n✅ Users seeded successfully!")
    else:
        print(f"✅ Users already exist ({count} users)")
        
        # Show existing users
        cur.execute("SELECT username, name, role FROM users")
        for row in cur.fetchall():
            print(f"  - {row['username']} ({row['name']}) - {row['role']}")
    
    conn.close()

if __name__ == "__main__":
    seed_users()