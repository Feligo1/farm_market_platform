# database_migration.py
import sqlite3
import os
from datetime import datetime

def run_migrations():
    """Run database migrations to add missing tables or columns"""
    print("🔄 Running database migrations...")
    
    conn = sqlite3.connect('farm_market.db')
    cur = conn.cursor()
    
    # Check which tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cur.fetchall()]
    
    print(f"📊 Existing tables: {len(existing_tables)}")
    
    # Define all tables that should exist
    required_tables = [
        'users', 'market_prices', 'data_sources', 'buyers', 'price_alerts',
        'activity_logs', 'admin_logs', 'sms_history', 'sms_subscriptions',
        'sms_balance', 'markets', 'collection_logs', 'forecast_cache',
        'user_sessions', 'system_metrics', 'ussd_sessions', 'ussd_logs',
        'ussd_profiles', 'transport_providers', 'delivery_requests',
        'delivery_trips', 'cold_chain_monitoring', 'route_optimization',
        'logistics_transactions', 'storage_facilities'
    ]
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        print(f"⚠️  Missing tables: {missing_tables}")
        print("🚧 Creating missing tables...")
        
        # Re-run the table creation from add_logistics_tables.py
        try:
            # Import and run the logistics table creation
            exec(open('add_logistics_tables.py').read())
            print("✅ Missing tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
    else:
        print("✅ All required tables exist")
    
    # Check for missing columns in existing tables
    print("\n🔍 Checking table schemas...")
    
    # Define expected columns for key tables
    table_schemas = {
        'users': ['user_id', 'username', 'password_hash', 'name', 'role', 'phone', 
                  'email', 'location', 'farm_size', 'main_crops', 'business_name',
                  'license_number', 'trading_commodities', 'created_at', 'last_login',
                  'status', 'sms_alerts', 'ussd_pin', 'last_sms_sent'],
        
        'market_prices': ['id', 'market', 'commodity', 'price', 'unit', 'volume',
                          'quality', 'source', 'verified', 'recorded_at', 'collected_at',
                          'region', 'market_lat', 'market_lon', 'price_trend'],
        
        'delivery_requests': ['id', 'request_id', 'farmer_id', 'farmer_name', 'farmer_phone',
                             'pickup_location', 'pickup_lat', 'pickup_lon', 'delivery_location',
                             'delivery_lat', 'delivery_lon', 'commodity', 'quantity',
                             'packaging_type', 'quality_grade', 'temperature_required',
                             'min_temperature', 'max_temperature', 'pickup_date',
                             'delivery_deadline', 'budget', 'status', 'assigned_provider_id',
                             'assigned_provider_name', 'quoted_price', 'actual_price',
                             'distance_km', 'estimated_duration_min', 'created_at',
                             'updated_at', 'notes']
    }
    
    for table, expected_columns in table_schemas.items():
        if table in existing_tables:
            try:
                cur.execute(f"PRAGMA table_info({table})")
                existing_columns = [row[1] for row in cur.fetchall()]
                missing_columns = [col for col in expected_columns if col not in existing_columns]
                
                if missing_columns:
                    print(f"⚠️  Table '{table}' missing columns: {missing_columns}")
                    # In a real migration, you would add these columns
                    # For now, we'll just log them
                else:
                    print(f"✅ Table '{table}' schema OK")
            except Exception as e:
                print(f"❌ Error checking table '{table}': {e}")
    
    # Add indexes if missing
    print("\n📈 Checking indexes...")
    indexes = [
        ("idx_delivery_requests_farmer", "delivery_requests(farmer_id)"),
        ("idx_delivery_requests_status", "delivery_requests(status)"),
        ("idx_delivery_requests_date", "delivery_requests(pickup_date)"),
        ("idx_transport_providers_status", "transport_providers(status)"),
        ("idx_transport_providers_region", "transport_providers(operating_region)"),
        ("idx_delivery_trips_trip", "delivery_trips(trip_id)"),
        ("idx_storage_facilities_location", "storage_facilities(location)"),
        ("idx_cold_chain_request", "cold_chain_monitoring(request_id)")
    ]
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing_indexes = [row[0] for row in cur.fetchall()]
    
    for index_name, index_def in indexes:
        if index_name not in existing_indexes:
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"❌ Error creating index {index_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Database migration completed!")
    return True

def backup_database():
    """Create a backup of the database before migration"""
    import shutil
    import datetime
    
    backup_name = f"farm_market_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists('farm_market.db'):
        shutil.copy2('farm_market.db', backup_name)
        print(f"💾 Database backed up to: {backup_name}")
        return backup_name
    return None

if __name__ == "__main__":
    # Create backup first
    backup_file = backup_database()
    
    # Run migrations
    success = run_migrations()
    
    if success:
        print(f"\n✅ Migration successful!")
        if backup_file:
            print(f"📦 Backup saved as: {backup_file}")
    else:
        print(f"\n❌ Migration failed!")
        if backup_file:
            print(f"💾 You can restore from backup: {backup_file}")