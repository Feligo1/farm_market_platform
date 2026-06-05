# migrate_db.py
"""
Database Migration Script for FarmConnect
Handles schema updates and data migrations
"""

import sqlite3
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE = "farm_market.db"

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE)

def run_migration(migration_name, sql_commands):
    """Run a database migration"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create migrations table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                applied_at TIMESTAMP,
                success BOOLEAN
            )
        ''')
        
        # Check if migration already applied
        cursor.execute("SELECT id FROM migrations WHERE name = ?", (migration_name,))
        if cursor.fetchone():
            logger.info(f"Migration {migration_name} already applied")
            conn.close()
            return
        
        # Apply migration
        cursor.executescript(sql_commands)
        cursor.execute(
            "INSERT INTO migrations (name, applied_at, success) VALUES (?, ?, ?)",
            (migration_name, datetime.now().isoformat(), True)
        )
        
        conn.commit()
        logger.info(f"✅ Migration {migration_name} applied successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration {migration_name} failed: {e}")
        cursor.execute(
            "INSERT INTO migrations (name, applied_at, success) VALUES (?, ?, ?)",
            (migration_name, datetime.now().isoformat(), False)
        )
        conn.commit()
        raise
    
    finally:
        conn.close()

def migrate_v1_initial_schema():
    """Initial database schema"""
    sql = """
    -- Add indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_market_prices_commodity_date 
    ON market_prices(commodity, recorded_at DESC);
    
    CREATE INDEX IF NOT EXISTS idx_sms_history_phone_date 
    ON sms_history(phone, sent_at DESC);
    
    CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
    CREATE INDEX IF NOT EXISTS idx_users_ussd_pin ON users(ussd_pin);
    
    -- Add new columns to users table
    ALTER TABLE users ADD COLUMN last_ussd_access TIMESTAMP;
    ALTER TABLE users ADD COLUMN total_ussd_requests INTEGER DEFAULT 0;
    ALTER TABLE users ADD COLUMN total_sms_received INTEGER DEFAULT 0;
    
    -- Add new columns to market_prices
    ALTER TABLE market_prices ADD COLUMN confidence_score REAL;
    ALTER TABLE market_prices ADD COLUMN prediction_model TEXT;
    
    -- Create price_history table
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commodity TEXT NOT NULL,
        market TEXT NOT NULL,
        price REAL NOT NULL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source TEXT,
        FOREIGN KEY (commodity, market) REFERENCES market_prices(commodity, market)
    );
    
    -- Create ussd_analytics table
    CREATE TABLE IF NOT EXISTS ussd_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        phone_number TEXT,
        menu_path TEXT,
        time_spent INTEGER,
        completed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    run_migration("v1_initial_schema", sql)

def migrate_v2_add_sms_tracking():
    """Add SMS tracking enhancements"""
    sql = """
    -- Add delivery tracking to sms_history
    ALTER TABLE sms_history ADD COLUMN delivery_status TEXT DEFAULT 'pending';
    ALTER TABLE sms_history ADD COLUMN delivery_time TIMESTAMP;
    ALTER TABLE sms_history ADD COLUMN retry_count INTEGER DEFAULT 0;
    
    -- Create sms_delivery_logs table
    CREATE TABLE IF NOT EXISTS sms_delivery_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT,
        phone_number TEXT,
        status TEXT,
        status_code INTEGER,
        status_description TEXT,
        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Add indexes
    CREATE INDEX IF NOT EXISTS idx_sms_history_delivery_status 
    ON sms_history(delivery_status);
    
    CREATE INDEX IF NOT EXISTS idx_sms_delivery_logs_message_id 
    ON sms_delivery_logs(message_id);
    """
    run_migration("v2_add_sms_tracking", sql)

def migrate_v3_add_forecast_cache():
    """Add forecast caching improvements"""
    sql = """
    -- Add new columns to forecast_cache
    ALTER TABLE forecast_cache ADD COLUMN model_parameters TEXT;
    ALTER TABLE forecast_cache ADD COLUMN error_margin REAL;
    
    -- Create forecast_accuracy table
    CREATE TABLE IF NOT EXISTS forecast_accuracy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commodity TEXT,
        market TEXT,
        forecast_date DATE,
        actual_price REAL,
        predicted_price REAL,
        error_percent REAL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Add indexes
    CREATE INDEX IF NOT EXISTS idx_forecast_accuracy_commodity 
    ON forecast_accuracy(commodity, forecast_date);
    """
    run_migration("v3_add_forecast_cache", sql)

def migrate_v4_add_user_preferences():
    """Add user preferences and settings"""
    sql = """
    -- Create user_settings table
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        language TEXT DEFAULT 'en',
        timezone TEXT DEFAULT 'Africa/Lusaka',
        notification_preferences TEXT,
        dashboard_layout TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    -- Create user_favorites table
    CREATE TABLE IF NOT EXISTS user_favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        item_type TEXT, -- 'commodity', 'market', 'buyer'
        item_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, item_type, item_id)
    );
    
    -- Add indexes
    CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id);
    """
    run_migration("v4_add_user_preferences", sql)

def migrate_v5_add_analytics():
    """Add analytics tables"""
    sql = """
    -- Create user_analytics table
    CREATE TABLE IF NOT EXISTS user_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        session_id TEXT,
        page_views TEXT,
        actions_taken TEXT,
        session_duration INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    -- Create system_health_logs table
    CREATE TABLE IF NOT EXISTS system_health_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        component TEXT,
        status TEXT,
        response_time REAL,
        error_message TEXT,
        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Add indexes
    CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON user_analytics(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_analytics_created_at ON user_analytics(created_at);
    CREATE INDEX IF NOT EXISTS idx_system_health_logs_component ON system_health_logs(component);
    """
    run_migration("v5_add_analytics", sql)

def run_all_migrations():
    """Run all pending migrations"""
    logger.info("Starting database migrations...")
    
    migrations = [
        migrate_v1_initial_schema,
        migrate_v2_add_sms_tracking,
        migrate_v3_add_forecast_cache,
        migrate_v4_add_user_preferences,
        migrate_v5_add_analytics
    ]
    
    for migration in migrations:
        try:
            migration()
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    logger.info("✅ All migrations completed successfully")
    return True

if __name__ == "__main__":
    run_all_migrations()