# fix_database.py
import sqlite3

def fix_buyers_table():
    """Fix buyers table missing status column"""
    conn = sqlite3.connect('farm_market.db')
    cur = conn.cursor()
    
    # Check if status column exists
    try:
        cur.execute("SELECT status FROM buyers LIMIT 1")
        print("✅ Buyers table has status column")
    except:
        print("⚠️ Adding status column to buyers table...")
        # Add status column if it doesn't exist
        cur.execute("ALTER TABLE buyers ADD COLUMN status TEXT DEFAULT 'active'")
        # Update existing rows
        cur.execute("UPDATE buyers SET status='active' WHERE status IS NULL")
        conn.commit()
        print("✅ Added status column to buyers table")
    
    conn.close()

def fix_sms_history_table():
    """Ensure sms_history table has correct schema"""
    conn = sqlite3.connect('farm_market.db')
    cur = conn.cursor()
    
    # Check table structure
    cur.execute("PRAGMA table_info(sms_history)")
    columns = cur.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"SMS History columns: {column_names}")
    
    # Add missing columns if needed
    missing_columns = []
    if 'message_id' not in column_names:
        missing_columns.append('message_id')
    
    for column in missing_columns:
        print(f"Adding column: {column}")
        cur.execute(f"ALTER TABLE sms_history ADD COLUMN {column} TEXT")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🔧 Fixing database issues...")
    fix_buyers_table()
    fix_sms_history_table()
    print("✅ Database fixes completed!")