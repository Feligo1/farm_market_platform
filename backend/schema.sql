-- =========================================================
-- SIMPLIFIED FARM CONNECT POSTGRESQL SCHEMA
-- =========================================================

-- Drop existing tables if they exist (in correct order to avoid foreign key errors)
DROP TABLE IF EXISTS daily_predictions CASCADE;
DROP TABLE IF EXISTS forecast_cache CASCADE;
DROP TABLE IF EXISTS forecast_models CASCADE;
DROP TABLE IF EXISTS daily_price_aggregates CASCADE;
DROP TABLE IF EXISTS price_alerts CASCADE;
DROP TABLE IF EXISTS market_prices CASCADE;
DROP TABLE IF EXISTS price_sources CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS seller_offers CASCADE;
DROP TABLE IF EXISTS buyer_requests CASCADE;
DROP TABLE IF EXISTS buyers CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS news_comments CASCADE;
DROP TABLE IF EXISTS news CASCADE;
DROP TABLE IF EXISTS sms_subscriptions CASCADE;
DROP TABLE IF EXISTS ussd_logs CASCADE;
DROP TABLE IF EXISTS ussd_sessions CASCADE;
DROP TABLE IF EXISTS sms_logs CASCADE;
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS token_blacklist CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS commodities CASCADE;
DROP TABLE IF EXISTS markets CASCADE;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(200) NOT NULL,
    role VARCHAR(50) DEFAULT 'farmer',
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(200) UNIQUE,
    location VARCHAR(200),
    profile_picture VARCHAR(500),
    farm_size DECIMAL(10,2),
    main_crops TEXT,
    business_name VARCHAR(200),
    license_number VARCHAR(100),
    rating DECIMAL(3,2) DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    sms_alerts BOOLEAN DEFAULT TRUE,
    ussd_pin VARCHAR(10)
);

-- Commodities table
CREATE TABLE commodities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100),
    unit VARCHAR(20) DEFAULT 'kg',
    seasonal_peak_start INTEGER,
    seasonal_peak_end INTEGER,
    icon VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE
);

-- Markets table
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    region VARCHAR(100),
    province VARCHAR(100),
    district VARCHAR(100),
    gps_lat DECIMAL(10,8),
    gps_lon DECIMAL(11,8),
    market_days VARCHAR(200),
    contact_phone VARCHAR(50),
    active BOOLEAN DEFAULT TRUE
);

-- Main Market Prices table (stores ALL price history)
CREATE TABLE market_prices (
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
    region VARCHAR(100),
    price_trend VARCHAR(20),
    daily_change_percent DECIMAL(5,2),
    recorded_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Daily Price Aggregates (for quick reporting)
CREATE TABLE daily_price_aggregates (
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
    UNIQUE(commodity_id, market_id, date)
);

-- Forecast Cache
CREATE TABLE forecast_cache (
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
);

-- Buyers table
CREATE TABLE buyers (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE REFERENCES users(user_id),
    company_name VARCHAR(200),
    business_type VARCHAR(100),
    purchase_volume_monthly DECIMAL(10,2),
    verification_status VARCHAR(20) DEFAULT 'pending'
);

-- Sellers table
CREATE TABLE sellers (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE REFERENCES users(user_id),
    farm_name VARCHAR(200),
    cooperative_name VARCHAR(200),
    production_capacity DECIMAL(10,2),
    verification_status VARCHAR(20) DEFAULT 'pending'
);

-- Transactions
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE,
    buyer_id INTEGER REFERENCES buyers(id),
    seller_id INTEGER REFERENCES sellers(id),
    commodity_id INTEGER REFERENCES commodities(id),
    commodity_name VARCHAR(100),
    quantity DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    buyer_rating INTEGER,
    seller_rating INTEGER,
    buyer_feedback TEXT,
    seller_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- News table
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    category VARCHAR(100),
    author_id VARCHAR(50) REFERENCES users(user_id),
    author_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'published',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100),
    from_user_id VARCHAR(50) REFERENCES users(user_id),
    to_user_id VARCHAR(50) REFERENCES users(user_id),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SMS Subscriptions
CREATE TABLE sms_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    commodity_name VARCHAR(100),
    alert_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity Logs
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    username VARCHAR(100),
    action VARCHAR(200),
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token Blacklist
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token_jti VARCHAR(200) UNIQUE NOT NULL,
    user_id VARCHAR(50),
    invalidated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SMS Logs
CREATE TABLE sms_logs (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    message TEXT,
    status VARCHAR(20),
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- SEED INITIAL DATA
-- =========================================================

-- Insert commodities
INSERT INTO commodities (name, category, unit, seasonal_peak_start, seasonal_peak_end, icon) VALUES
('Maize', 'Grain', 'kg', 6, 7, '🌽'),
('Tomatoes', 'Vegetable', 'kg', 12, 1, '🍅'),
('Beans', 'Legume', 'kg', 6, 8, '🫘'),
('Groundnuts', 'Legume', 'kg', 6, 8, '🥜'),
('Rice', 'Grain', 'kg', 7, 9, '🍚'),
('Soybeans', 'Legume', 'kg', 6, 7, '🌱'),
('Cassava', 'Root', 'kg', 9, 11, '🌿'),
('Sweet Potatoes', 'Root', 'kg', 5, 6, '🍠'),
('Onions', 'Vegetable', 'kg', 11, 12, '🧅'),
('Cabbage', 'Vegetable', 'kg', 5, 6, '🥬')
ON CONFLICT (name) DO NOTHING;

-- Insert markets
INSERT INTO markets (name, region, province, district, market_days) VALUES
('Lusaka City Market', 'Lusaka', 'Lusaka', 'Lusaka', 'Mon-Sat'),
('Soweto Market', 'Lusaka', 'Lusaka', 'Lusaka', 'Daily'),
('Kabwe Central Market', 'Central', 'Central', 'Kabwe', 'Mon-Sat'),
('Ndola Main Market', 'Copperbelt', 'Copperbelt', 'Ndola', 'Daily'),
('Kitwe Market', 'Copperbelt', 'Copperbelt', 'Kitwe', 'Daily'),
('Livingstone Market', 'Southern', 'Southern', 'Livingstone', 'Mon-Sat'),
('Chipata Central Market', 'Eastern', 'Eastern', 'Chipata', 'Mon-Fri'),
('Solwezi Market', 'North-Western', 'North-Western', 'Solwezi', 'Mon-Sat')
ON CONFLICT (name) DO NOTHING;

-- Insert sample market prices
INSERT INTO market_prices (market_name, commodity_name, price, recorded_at, is_verified, source_type) VALUES
('Lusaka City Market', 'Maize', 6.80, CURRENT_TIMESTAMP, TRUE, 'system'),
('Lusaka City Market', 'Tomatoes', 8.50, CURRENT_TIMESTAMP, TRUE, 'system'),
('Lusaka City Market', 'Beans', 12.50, CURRENT_TIMESTAMP, TRUE, 'system'),
('Kabwe Central Market', 'Maize', 6.60, CURRENT_TIMESTAMP, TRUE, 'system'),
('Ndola Main Market', 'Maize', 6.90, CURRENT_TIMESTAMP, TRUE, 'system'),
('Kitwe Market', 'Beans', 12.00, CURRENT_TIMESTAMP, TRUE, 'system'),
('Chipata Central Market', 'Groundnuts', 18.00, CURRENT_TIMESTAMP, TRUE, 'system'),
('Livingstone Market', 'Maize', 6.70, CURRENT_TIMESTAMP, TRUE, 'system');

-- Insert sample news
INSERT INTO news (title, content, category, status, published_at) VALUES
('Zambia Announces New Agricultural Subsidy Program', 'The Zambian government has launched a new subsidy program for small-scale farmers...', 'Policy', 'published', CURRENT_TIMESTAMP),
('Maize Prices Expected to Rise', 'Market analysts predict a 15% increase in maize prices...', 'Market', 'published', CURRENT_TIMESTAMP),
('New Farming Techniques Boost Yields', 'Local farmers report increased yields after adopting modern methods...', 'Tips', 'published', CURRENT_TIMESTAMP);

-- Insert demo users (passwords will be hashed by the app)
INSERT INTO users (user_id, username, password_hash, name, role, phone, email, location, created_at, status) VALUES
('admin1', 'admin1', 'admin123', 'Admin User', 'admin', '+260971234569', 'admin@farmconnect.zm', 'Lusaka', CURRENT_TIMESTAMP, 'active'),
('farmer1', 'farmer1', 'farmer123', 'John Farmer', 'farmer', '+260971234567', 'john@farmconnect.zm', 'Lusaka', CURRENT_TIMESTAMP, 'active'),
('trader1', 'trader1', 'trader123', 'Sarah Trader', 'trader', '+260971234568', 'sarah@farmconnect.zm', 'Kabwe', CURRENT_TIMESTAMP, 'active');

SELECT 'Database setup complete!' as status;