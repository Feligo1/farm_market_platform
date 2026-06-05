# quick_column_fix.py
import sqlite3

def quick_fix():
    """Quick fix for missing price_trend column"""
    conn = sqlite3.connect('farm_market.db')
    cur = conn.cursor()
    
    print("🔧 Adding price_trend column to market_prices table...")
    
    try:
        # Check if column exists
        cur.execute("PRAGMA table_info(market_prices)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'price_trend' not in columns:
            # Add the column
            cur.execute("ALTER TABLE market_prices ADD COLUMN price_trend TEXT DEFAULT 'stable'")
            conn.commit()
            print("✅ Added price_trend column")
            
            # Update existing records
            cur.execute("UPDATE market_prices SET price_trend='stable' WHERE price_trend IS NULL")
            updated = cur.rowcount
            conn.commit()
            print(f"✅ Updated {updated} records with price_trend='stable'")
        else:
            print("✅ price_trend column already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    conn.close()
    print("✅ Quick fix completed!")

if __name__ == "__main__":
    quick_fix()