# fix_database_schema.py
import sqlite3
import os

def fix_database_schema():
    """Fix missing columns in database tables"""
    DATABASE = "farm_market.db"
    
    if not os.path.exists(DATABASE):
        print("❌ Database file not found!")
        return False
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    print("=" * 60)
    print("🔧 FIXING DATABASE SCHEMA")
    print("=" * 60)
    
    # Check market_prices table structure
    print("\n1. Checking market_prices table...")
    try:
        cur.execute("PRAGMA table_info(market_prices)")
        columns = cur.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"   Existing columns: {column_names}")
        
        # Check for missing columns
        missing_columns = []
        
        if 'price_trend' not in column_names:
            missing_columns.append('price_trend')
            print("   ❌ Missing: price_trend")
        
        if 'region' not in column_names:
            missing_columns.append('region')
            print("   ❌ Missing: region")
        
        if 'market_lat' not in column_names:
            missing_columns.append('market_lat')
            print("   ❌ Missing: market_lat")
        
        if 'market_lon' not in column_names:
            missing_columns.append('market_lon')
            print("   ❌ Missing: market_lon")
        
        # Add missing columns
        if missing_columns:
            print(f"\n2. Adding {len(missing_columns)} missing columns...")
            for column in missing_columns:
                try:
                    if column == 'price_trend':
                        cur.execute(f"ALTER TABLE market_prices ADD COLUMN {column} TEXT DEFAULT 'stable'")
                    elif column == 'region':
                        cur.execute(f"ALTER TABLE market_prices ADD COLUMN {column} TEXT")
                    elif column in ['market_lat', 'market_lon']:
                        cur.execute(f"ALTER TABLE market_prices ADD COLUMN {column} REAL")
                    
                    print(f"   ✅ Added: {column}")
                except Exception as e:
                    print(f"   ⚠️  Error adding {column}: {e}")
            
            conn.commit()
        else:
            print("   ✅ All columns present!")
        
    except Exception as e:
        print(f"   ❌ Error checking table: {e}")
    
    # Fix buyers table
    print("\n3. Checking buyers table...")
    try:
        cur.execute("PRAGMA table_info(buyers)")
        columns = cur.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'status' not in column_names:
            print("   ❌ Missing: status")
            try:
                cur.execute("ALTER TABLE buyers ADD COLUMN status TEXT DEFAULT 'active'")
                conn.commit()
                print("   ✅ Added: status column")
            except Exception as e:
                print(f"   ⚠️  Error adding status: {e}")
        else:
            print("   ✅ status column exists")
            
    except Exception as e:
        print(f"   ❌ Error checking buyers table: {e}")
    
    # Fix data_sources table
    print("\n4. Checking data_sources table...")
    try:
        cur.execute("SELECT COUNT(*) FROM data_sources")
        count = cur.fetchone()[0]
        print(f"   Data sources: {count}")
    except:
        print("   ⚠️  Could not check data_sources")
    
    # Create missing endpoints tables
    print("\n5. Creating missing API endpoint tables...")
    
    # Check if buyers endpoint should return data from buyers table
    print("   Buyers endpoint: Should query 'buyers' table")
    
    # Check other endpoints
    endpoints_to_check = [
        ('/api/buyers', 'buyers'),
        ('/api/data/status', 'collection_logs, data_sources'),
        ('/api/user/profile', 'users')
    ]
    
    for endpoint, expected_table in endpoints_to_check:
        try:
            cur.execute(f"SELECT 1 FROM {expected_table.split(',')[0].strip()} LIMIT 1")
            print(f"   ✅ {endpoint}: Table exists")
        except:
            print(f"   ❌ {endpoint}: Table missing")
    
    # Update some sample data to have price_trend
    print("\n6. Updating sample data with price_trend...")
    try:
        cur.execute("UPDATE market_prices SET price_trend='stable' WHERE price_trend IS NULL")
        updated = cur.rowcount
        conn.commit()
        print(f"   ✅ Updated {updated} records with price_trend='stable'")
    except Exception as e:
        print(f"   ⚠️  Error updating price_trend: {e}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database schema fixes completed!")
    print("=" * 60)
    
    return True

def create_missing_endpoints():
    """Create missing API endpoints in a separate file"""
    missing_endpoints_code = '''
# =========================================================
# missing_endpoints.py - Add to your app.py
# =========================================================

@app.route("/api/buyers", methods=["GET"])
def get_buyers():
    """Get buyer listings"""
    conn = get_db()
    cur = conn.cursor()
    
    commodity = request.args.get("commodity", "all")
    location = request.args.get("location", "all")
    verified_only = request.args.get("verified", "true").lower() == "true"
    min_rating = float(request.args.get("min_rating", 3.0))
    limit = int(request.args.get("limit", 50))
    
    query = """
        SELECT id, name, phone, commodity, location, max_price, min_volume, 
               notes, verified, rating, added_by, created_at, status
        FROM buyers 
        WHERE status = 'active'
    """
    params = []
    
    if commodity != "all":
        query += " AND commodity=?"
        params.append(commodity)
    
    if location != "all":
        query += " AND location=?"
        params.append(location)
    
    if verified_only:
        query += " AND verified=1"
    
    query += " AND rating >= ?"
    params.append(min_rating)
    
    query += " ORDER BY rating DESC, verified DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    buyers = [dict(row) for row in cur.fetchall()]
    
    # Get statistics
    cur.execute("SELECT COUNT(*) as total FROM buyers WHERE status='active'")
    total_buyers = cur.fetchone()["total"]
    
    cur.execute("SELECT COUNT(DISTINCT commodity) as commodities FROM buyers WHERE status='active'")
    unique_commodities = cur.fetchone()["commodities"]
    
    cur.execute("SELECT COUNT(DISTINCT location) as locations FROM buyers WHERE status='active'")
    unique_locations = cur.fetchone()["locations"]
    
    conn.close()
    
    return jsonify({
        "buyers": buyers,
        "statistics": {
            "total": total_buyers,
            "verified": len([b for b in buyers if b["verified"]]),
            "unique_commodities": unique_commodities,
            "unique_locations": unique_locations,
            "returned": len(buyers)
        }
    })

@app.route("/api/data/status", methods=["GET"])
def get_data_status():
    """Get data collection status"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get total counts
        cur.execute("SELECT COUNT(*) FROM market_prices")
        total_prices = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM market_prices WHERE verified = 1")
        verified_prices = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM data_sources WHERE enabled = 1")
        active_sources = cur.fetchone()[0]
        
        # Get recent collections
        cur.execute("""
            SELECT source_name, status, records_collected, collected_at
            FROM collection_logs 
            ORDER BY collected_at DESC 
            LIMIT 10
        """)
        recent_logs = [dict(row) for row in cur.fetchall()]
        
        # Get source statistics
        cur.execute("""
            SELECT name, type, url, enabled, priority, last_updated, success_rate, total_attempts, total_success
            FROM data_sources 
            ORDER BY priority, name
        """)
        sources = [dict(row) for row in cur.fetchall()]
        
        # Get data freshness
        cur.execute("""
            SELECT MAX(recorded_at) as latest_update,
                   MIN(recorded_at) as oldest_update,
                   COUNT(DISTINCT commodity) as unique_commodities,
                   COUNT(DISTINCT market) as unique_markets
            FROM market_prices 
            WHERE verified = 1
        """)
        freshness = dict(cur.fetchone())
        
        conn.close()
        
        return jsonify({
            "status": "active",
            "total_prices": total_prices,
            "verified_prices": verified_prices,
            "verification_rate": f"{(verified_prices/total_prices*100):.1f}%" if total_prices > 0 else "0%",
            "active_sources": active_sources,
            "data_freshness": freshness,
            "recent_collections": recent_logs,
            "sources": sources
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/profile", methods=["GET"])
@token_required
def get_user_profile():
    """Get current user profile"""
    user = request.user
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT user_id, username, name, role, phone, email, location, 
               farm_size, main_crops, business_name, license_number, 
               trading_commodities, created_at, sms_alerts
        FROM users 
        WHERE user_id=?
    """, (user["user_id"],))
    
    user_data = cur.fetchone()
    conn.close()
    
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"user": dict(user_data)})
    '''
    
    print("\n" + "=" * 60)
    print("📋 MISSING ENDPOINTS TO ADD TO APP.PY")
    print("=" * 60)
    print(missing_endpoints_code)
    print("=" * 60)
    
    # Save to file
    with open('missing_endpoints.txt', 'w') as f:
        f.write(missing_endpoints_code)
    
    print("✅ Missing endpoints code saved to 'missing_endpoints.txt'")
    print("=" * 60)

def quick_fix_app_py():
    """Quick fix for the get_real_prices function"""
    fix_code = '''
# =========================================================
# QUICK FIX FOR get_real_prices() FUNCTION
# Replace lines around 1970-1990 in app.py with:
# =========================================================

@app.route("/api/prices/real", methods=["GET"])
def get_real_prices():
    """Get real Zambian market prices - FIXED VERSION"""
    conn = get_db()
    cur = conn.cursor()
    
    commodity = request.args.get("commodity", "all")
    market = request.args.get("market", "all")
    region = request.args.get("region", "all")
    limit = request.args.get("limit", "100")
    verified_only = request.args.get("verified", "true").lower() == "true"
    latest_only = request.args.get("latest", "false").lower() == "true"
    
    if latest_only:
        # Get latest price for each commodity-market pair
        query = """
            SELECT mp1.* FROM market_prices mp1
            INNER JOIN (
                SELECT market, commodity, MAX(recorded_at) as latest
                FROM market_prices 
                WHERE verified = 1
                GROUP BY market, commodity
            ) mp2 ON mp1.market = mp2.market 
                   AND mp1.commodity = mp2.commodity 
                   AND mp1.recorded_at = mp2.latest
            WHERE 1=1
        """
    else:
        # FIXED: Removed price_trend from SELECT if column doesn't exist
        try:
            # Check if price_trend column exists
            cur.execute("PRAGMA table_info(market_prices)")
            columns = [col[1] for col in cur.fetchall()]
            if 'price_trend' in columns:
                select_columns = "id, market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend"
            else:
                select_columns = "id, market, commodity, price, unit, volume, quality, source, verified, recorded_at, region"
        except:
            select_columns = "id, market, commodity, price, unit, volume, quality, source, verified, recorded_at"
        
        query = f"""
            SELECT {select_columns}
            FROM market_prices 
            WHERE 1=1
        """
    
    params = []
    
    if commodity != "all":
        query += " AND commodity=?"
        params.append(commodity)
    
    if market != "all":
        query += " AND market LIKE ?"
        params.append(f"%{market}%")
    
    if region != "all":
        query += " AND region=?"
        params.append(region)
    
    if verified_only:
        query += " AND verified=1"
    
    if not latest_only:
        query += " ORDER BY recorded_at DESC LIMIT ?"
        params.append(int(limit))
    
    try:
        cur.execute(query, params)
        prices = [dict(row) for row in cur.fetchall()]
        
        # Get statistics
        cur.execute("SELECT COUNT(*) FROM market_prices WHERE verified = 1")
        total_verified = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT market) FROM market_prices WHERE verified = 1")
        unique_markets = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT commodity) FROM market_prices WHERE verified = 1")
        unique_commodities = cur.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "prices": prices,
            "statistics": {
                "total_verified": total_verified,
                "unique_markets": unique_markets,
                "unique_commodities": unique_commodities,
                "returned": len(prices)
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e), "query": query}), 500
    '''
    
    print("\n" + "=" * 60)
    print("🔧 QUICK FIX FOR APP.PY")
    print("=" * 60)
    print(fix_code)
    print("=" * 60)
    
    with open('app_fix.txt', 'w') as f:
        f.write(fix_code)
    
    print("✅ Fix code saved to 'app_fix.txt'")
    print("=" * 60)

if __name__ == "__main__":
    print("🚀 RUNNING DATABASE FIXES...")
    print("=" * 60)
    
    # Fix database schema
    fix_database_schema()
    
    # Show missing endpoints
    create_missing_endpoints()
    
    # Show app.py fix
    quick_fix_app_py()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run the database fix above")
    print("2. Add the missing endpoints to app.py")
    print("3. Replace get_real_prices() function with the fixed version")
    print("4. Restart the server")
    print("=" * 60)
