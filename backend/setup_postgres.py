import psycopg2
from psycopg2 import sql

# Connection parameters - use the password that works
conn_params = {
    "host": "localhost",
    "port": "5432",
    "database": "farmconnect_db",
    "user": "farmconnect_user",
    "password": "FarmConnect2024!"
}

print("=" * 60)
print("Setting up PostgreSQL Database for FarmConnect")
print("=" * 60)

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL successfully!")
    
    # Create all tables
    print("\n📋 Creating tables...")
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) UNIQUE NOT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(200) NOT NULL,
            role VARCHAR(50) DEFAULT 'farmer',
            phone VARCHAR(20),
            email VARCHAR(200),
            location VARCHAR(200),
            profile_picture VARCHAR(500),
            farm_size DECIMAL(10,2),
            main_crops TEXT,
            business_name VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            sms_alerts BOOLEAN DEFAULT TRUE,
            ussd_pin VARCHAR(10)
        )
    """)
    print("  ✓ users table created")
    
    # Commodities table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commodities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            category VARCHAR(100),
            unit VARCHAR(20) DEFAULT 'kg',
            icon VARCHAR(10),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ commodities table created")
    
    # Markets table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS markets (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) UNIQUE NOT NULL,
            region VARCHAR(100),
            district VARCHAR(100),
            market_days VARCHAR(200),
            gps_lat DECIMAL(10,8),
            gps_lon DECIMAL(11,8),
            contact_phone VARCHAR(50),
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ markets table created")
    
    # Market Prices table (main price storage)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_prices (
            id SERIAL PRIMARY KEY,
            market_id INTEGER REFERENCES markets(id),
            commodity_id INTEGER REFERENCES commodities(id),
            market_name VARCHAR(200),
            commodity_name VARCHAR(100),
            price DECIMAL(10,2) NOT NULL,
            unit VARCHAR(20) DEFAULT 'ZMW/kg',
            volume DECIMAL(10,2),
            quality VARCHAR(50),
            is_verified BOOLEAN DEFAULT FALSE,
            source_type VARCHAR(50),
            source_user_id VARCHAR(50),
            price_trend VARCHAR(20),
            recorded_at TIMESTAMP NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    print("  ✓ market_prices table created")
    
    # Daily Price Aggregates
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_price_aggregates (
            id SERIAL PRIMARY KEY,
            commodity_id INTEGER REFERENCES commodities(id),
            commodity_name VARCHAR(100),
            market_id INTEGER REFERENCES markets(id),
            market_name VARCHAR(200),
            date DATE NOT NULL,
            avg_price DECIMAL(10,2),
            min_price DECIMAL(10,2),
            max_price DECIMAL(10,2),
            price_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(commodity_id, market_id, date)
        )
    """)
    print("  ✓ daily_price_aggregates table created")
    
    # Forecast Cache
    cur.execute("""
        CREATE TABLE IF NOT EXISTS forecast_cache (
            id SERIAL PRIMARY KEY,
            commodity_id INTEGER REFERENCES commodities(id),
            commodity_name VARCHAR(100),
            market_id INTEGER REFERENCES markets(id),
            market_name VARCHAR(200),
            forecast_days INTEGER,
            forecast_data JSONB NOT NULL,
            current_price DECIMAL(10,2),
            predicted_change_percent DECIMAL(5,2),
            confidence_score DECIMAL(5,2),
            model_used VARCHAR(100),
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    print("  ✓ forecast_cache table created")
    
    # News table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            slug VARCHAR(500) UNIQUE,
            content TEXT NOT NULL,
            summary TEXT,
            image_url VARCHAR(500),
            category VARCHAR(100),
            author_id VARCHAR(50),
            author_name VARCHAR(200),
            status VARCHAR(20) DEFAULT 'published',
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ news table created")
    
    # Messages table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id VARCHAR(100),
            from_user_id VARCHAR(50),
            to_user_id VARCHAR(50),
            subject VARCHAR(500),
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ messages table created")
    
    # SMS Subscriptions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sms_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            commodity_name VARCHAR(100),
            market_name VARCHAR(200),
            alert_type VARCHAR(50),
            threshold DECIMAL(10,2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_notified_at TIMESTAMP
        )
    """)
    print("  ✓ sms_subscriptions table created")
    
    # Activity Logs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            username VARCHAR(100),
            action VARCHAR(200),
            entity_type VARCHAR(100),
            entity_id VARCHAR(100),
            old_values JSONB,
            new_values JSONB,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ activity_logs table created")
    
    # Token Blacklist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS token_blacklist (
            id SERIAL PRIMARY KEY,
            token_jti VARCHAR(200) UNIQUE NOT NULL,
            user_id VARCHAR(50),
            invalidated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ token_blacklist table created")
    
    # Insert seed data
    print("\n🌱 Inserting seed data...")
    
    # Insert commodities
    cur.execute("""
        INSERT INTO commodities (name, category, icon) VALUES
        ('Maize', 'Grain', '🌽'),
        ('Tomatoes', 'Vegetable', '🍅'),
        ('Beans', 'Legume', '🫘'),
        ('Groundnuts', 'Legume', '🥜'),
        ('Rice', 'Grain', '🍚'),
        ('Soybeans', 'Legume', '🌱'),
        ('Cassava', 'Root', '🌿'),
        ('Sweet Potatoes', 'Root', '🍠'),
        ('Onions', 'Vegetable', '🧅'),
        ('Cabbage', 'Vegetable', '🥬')
        ON CONFLICT (name) DO NOTHING
    """)
    print("  ✓ Inserted 10 commodities")
    
    # Insert markets
    cur.execute("""
        INSERT INTO markets (name, region, district, market_days) VALUES
        ('Lusaka City Market', 'Lusaka', 'Lusaka', 'Mon-Sat'),
        ('Soweto Market', 'Lusaka', 'Lusaka', 'Daily'),
        ('Kabwe Central Market', 'Central', 'Kabwe', 'Mon-Sat'),
        ('Ndola Main Market', 'Copperbelt', 'Ndola', 'Daily'),
        ('Kitwe Market', 'Copperbelt', 'Kitwe', 'Daily'),
        ('Livingstone Market', 'Southern', 'Livingstone', 'Mon-Sat'),
        ('Chipata Central Market', 'Eastern', 'Chipata', 'Mon-Fri'),
        ('Solwezi Market', 'North-Western', 'Solwezi', 'Mon-Sat')
        ON CONFLICT (name) DO NOTHING
    """)
    print("  ✓ Inserted 8 markets")
    
    # Insert sample prices
    cur.execute("""
        INSERT INTO market_prices (market_name, commodity_name, price, recorded_at, is_verified, source_type) VALUES
        ('Lusaka City Market', 'Maize', 6.80, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Lusaka City Market', 'Tomatoes', 8.50, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Lusaka City Market', 'Beans', 12.50, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Kabwe Central Market', 'Maize', 6.60, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Ndola Main Market', 'Maize', 6.90, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Kitwe Market', 'Beans', 12.00, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Chipata Central Market', 'Groundnuts', 18.00, CURRENT_TIMESTAMP, TRUE, 'system'),
        ('Livingstone Market', 'Maize', 6.70, CURRENT_TIMESTAMP, TRUE, 'system')
    """)
    print("  ✓ Inserted 8 sample prices")
    
    # Insert sample news
    cur.execute("""
        INSERT INTO news (title, content, category, status, published_at) VALUES
        ('Zambia Announces New Agricultural Subsidy Program', 'The government has launched a new subsidy program for small-scale farmers.', 'Policy', 'published', CURRENT_TIMESTAMP),
        ('Maize Prices Expected to Rise', 'Market analysts predict a 15% increase in maize prices.', 'Market', 'published', CURRENT_TIMESTAMP),
        ('New Farming Techniques Boost Yields', 'Local farmers report increased yields after adopting modern methods.', 'Tips', 'published', CURRENT_TIMESTAMP)
    """)
    print("  ✓ Inserted 3 news articles")
    
    # Insert demo users
    cur.execute("""
        INSERT INTO users (user_id, username, password_hash, name, role, phone, email, location) VALUES
        ('admin1', 'admin1', 'admin123', 'Admin User', 'admin', '+260971234569', 'admin@farmconnect.zm', 'Lusaka'),
        ('farmer1', 'farmer1', 'farmer123', 'John Farmer', 'farmer', '+260971234567', 'john@farmconnect.zm', 'Lusaka'),
        ('trader1', 'trader1', 'trader123', 'Sarah Trader', 'trader', '+260971234568', 'sarah@farmconnect.zm', 'Kabwe')
        ON CONFLICT (user_id) DO NOTHING
    """)
    print("  ✓ Inserted 3 demo users")
    
    # Verify setup
    print("\n📊 Verification:")
    cur.execute("SELECT COUNT(*) as count FROM commodities")
    result = cur.fetchone()
    print(f"  Commodities: {result[0]}")
    
    cur.execute("SELECT COUNT(*) as count FROM markets")
    result = cur.fetchone()
    print(f"  Markets: {result[0]}")
    
    cur.execute("SELECT COUNT(*) as count FROM market_prices")
    result = cur.fetchone()
    print(f"  Market Prices: {result[0]}")
    
    cur.execute("SELECT COUNT(*) as count FROM users")
    result = cur.fetchone()
    print(f"  Users: {result[0]}")
    
    cur.execute("SELECT COUNT(*) as count FROM news")
    result = cur.fetchone()
    print(f"  News: {result[0]}")
    
    print("\n" + "=" * 60)
    print("🎉 DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nYou can now run your Flask application:")
    print("  python app.py")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check your password in the connection string")
    print("3. Verify the database exists")