-- =========================================================
-- FarmConnect Database Schema (CORRECTED)
-- Cloud-Based Market Information Platform for Farmers
-- Mulungushi University - ICT 431 Capstone Project
-- Student: Daka Felix (202206453)
-- =========================================================

-- =========================================================
-- SYSTEM SETTINGS (Create first since triggers may reference it)
-- =========================================================

CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

-- =========================================================
-- USERS & AUTHENTICATION
-- =========================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('farmer', 'trader', 'admin')),
    phone TEXT,
    email TEXT,
    location TEXT,
    farm_size REAL,
    main_crops TEXT,
    business_name TEXT,
    license_number TEXT,
    trading_commodities TEXT,
    ussd_pin TEXT,
    sms_alerts INTEGER DEFAULT 1,
    profile_picture TEXT,
    created_at TEXT NOT NULL,
    last_login TEXT,
    last_sms_sent TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended', 'deleted')),
    verified INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS token_blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_jti TEXT UNIQUE NOT NULL,
    user_id TEXT,
    invalidated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- MARKET DATA
-- =========================================================

CREATE TABLE IF NOT EXISTS markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    region TEXT,
    district TEXT,
    province TEXT,
    gps_lat REAL,
    gps_lon REAL,
    market_days TEXT,
    operating_hours TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    notes TEXT,
    active INTEGER DEFAULT 1,
    last_updated TEXT
);

CREATE TABLE IF NOT EXISTS commodities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    unit TEXT DEFAULT 'kg',
    min_price REAL,
    max_price REAL,
    season_start TEXT,
    season_end TEXT,
    image_url TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS market_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,
    commodity TEXT NOT NULL,
    price REAL NOT NULL,
    unit TEXT DEFAULT 'ZMW/kg',
    volume REAL,
    quality TEXT,
    source TEXT,
    source_user_id TEXT,
    verified INTEGER DEFAULT 0,
    verified_by TEXT,
    verified_at TEXT,
    recorded_at TEXT NOT NULL,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
    region TEXT,
    market_lat REAL,
    market_lon REAL,
    price_trend TEXT,
    notes TEXT,
    FOREIGN KEY (source_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity TEXT NOT NULL,
    market TEXT NOT NULL,
    price REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    source TEXT
);

-- =========================================================
-- BUYER & TRADER CONNECTIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    commodity TEXT NOT NULL,
    location TEXT NOT NULL,
    max_price REAL NOT NULL,
    min_volume REAL,
    max_volume REAL,
    payment_terms TEXT,
    delivery_requirements TEXT,
    notes TEXT,
    verified INTEGER DEFAULT 0,
    verified_by TEXT,
    rating REAL DEFAULT 4.0,
    total_transactions INTEGER DEFAULT 0,
    added_by TEXT,
    created_at TEXT,
    last_contact TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'blacklisted'))
);

CREATE TABLE IF NOT EXISTS buyer_inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER NOT NULL,
    farmer_id TEXT NOT NULL,
    commodity TEXT NOT NULL,
    quantity REAL,
    message TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'completed')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    responded_at TEXT,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    FOREIGN KEY (farmer_id) REFERENCES users(user_id)
);

-- =========================================================
-- SMS & NOTIFICATIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS sms_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'notification',
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'failed', 'delivered', 'simulated')),
    provider TEXT,
    message_id TEXT,
    cost REAL DEFAULT 0.0,
    sent_at TEXT,
    queued_at TEXT DEFAULT CURRENT_TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    error_message TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS sms_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    commodity TEXT NOT NULL,
    market TEXT,
    alert_type TEXT DEFAULT 'price_change' CHECK(alert_type IN ('price_change', 'forecast', 'both')),
    threshold REAL DEFAULT 5.0,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_triggered TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS price_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    commodity TEXT NOT NULL,
    market TEXT,
    target_price REAL,
    alert_type TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT,
    triggered_at TEXT,
    triggered_price REAL,
    acknowledged INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- =========================================================
-- USSD SESSION MANAGEMENT
-- =========================================================

CREATE TABLE IF NOT EXISTS ussd_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    phone_number TEXT NOT NULL,
    service_code TEXT,
    current_menu TEXT,
    menu_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired', 'completed'))
);

CREATE TABLE IF NOT EXISTS ussd_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    phone_number TEXT,
    input_text TEXT,
    response_text TEXT,
    menu_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- FORECAST & ML MODELS
-- =========================================================

CREATE TABLE IF NOT EXISTS forecast_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity TEXT NOT NULL,
    market TEXT NOT NULL,
    forecast_days INTEGER NOT NULL,
    forecast_data TEXT NOT NULL,
    recommendations TEXT,
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    model_used TEXT,
    accuracy_score REAL,
    UNIQUE(commodity, market, forecast_days)
);

CREATE TABLE IF NOT EXISTS ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_path TEXT,
    model_type TEXT,
    trained_on TEXT,
    accuracy REAL,
    mae REAL,
    rmse REAL,
    active INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- ANALYTICS & LOGGING
-- =========================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    user_id TEXT,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    user_id TEXT,
    ip_address TEXT,
    method TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size INTEGER,
    response_size INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS webhook_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    payload TEXT,
    status TEXT,
    response TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    read INTEGER DEFAULT 0,
    action_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- =========================================================
-- INDEXES FOR PERFORMANCE
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_location ON users(location);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE INDEX IF NOT EXISTS idx_prices_commodity ON market_prices(commodity);
CREATE INDEX IF NOT EXISTS idx_prices_market ON market_prices(market);
CREATE INDEX IF NOT EXISTS idx_prices_region ON market_prices(region);
CREATE INDEX IF NOT EXISTS idx_prices_recorded_at ON market_prices(recorded_at);
CREATE INDEX IF NOT EXISTS idx_prices_verified ON market_prices(verified);
CREATE INDEX IF NOT EXISTS idx_prices_trend ON market_prices(price_trend);
CREATE INDEX IF NOT EXISTS idx_prices_composite ON market_prices(commodity, market, recorded_at);

CREATE INDEX IF NOT EXISTS idx_sms_phone ON sms_history(phone);
CREATE INDEX IF NOT EXISTS idx_sms_status ON sms_history(status);
CREATE INDEX IF NOT EXISTS idx_sms_type ON sms_history(type);
CREATE INDEX IF NOT EXISTS idx_sms_sent_at ON sms_history(sent_at);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON sms_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_commodity ON sms_subscriptions(commodity);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON sms_subscriptions(active);

CREATE INDEX IF NOT EXISTS idx_buyers_commodity ON buyers(commodity);
CREATE INDEX IF NOT EXISTS idx_buyers_location ON buyers(location);
CREATE INDEX IF NOT EXISTS idx_buyers_verified ON buyers(verified);

CREATE INDEX IF NOT EXISTS idx_ussd_sessions_session ON ussd_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_ussd_sessions_phone ON ussd_sessions(phone_number);
CREATE INDEX IF NOT EXISTS idx_ussd_logs_session ON ussd_logs(session_id);

CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user);
CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_api_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_created ON api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_user ON api_usage(user_id);

CREATE INDEX IF NOT EXISTS idx_forecast_commodity ON forecast_cache(commodity);
CREATE INDEX IF NOT EXISTS idx_forecast_market ON forecast_cache(market);
CREATE INDEX IF NOT EXISTS idx_forecast_expires ON forecast_cache(expires_at);

-- =========================================================
-- TRIGGERS (NO REFERENCES TO system_settings)
-- =========================================================

CREATE TRIGGER IF NOT EXISTS update_ussd_activity 
AFTER UPDATE ON ussd_sessions
BEGIN
    UPDATE ussd_sessions SET last_activity = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS record_price_history
AFTER INSERT ON market_prices
BEGIN
    INSERT INTO price_history (commodity, market, price, recorded_at, source)
    VALUES (NEW.commodity, NEW.market, NEW.price, NEW.recorded_at, NEW.source);
END;

-- =========================================================
-- INSERT DEFAULT SYSTEM SETTINGS
-- =========================================================

INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('system_name', 'FarmConnect Zambia', 'string', 'Platform display name'),
('system_version', '2.6.0', 'string', 'Current version'),
('ussd_code', '*384*7321#', 'string', 'USSD short code'),
('sms_enabled', 'true', 'boolean', 'Enable SMS notifications'),
('forecast_days_default', '7', 'integer', 'Default forecast days'),
('price_alert_threshold', '5.0', 'float', 'Default price alert percentage'),
('contact_email', 'support@farmconnect.zm', 'string', 'Support email'),
('contact_phone', '+260211123456', 'string', 'Support phone');
-- =========================================================
-- FARM CONNECT - COMPREHENSIVE MARKET DATA GENERATION
-- Realistic price variations across all Zambian markets
-- Generated for all commodities with proper price differences
-- =========================================================

-- =========================================================
-- STEP 1: ENSURE ALL MARKETS EXIST
-- =========================================================

-- Insert all major Zambian markets if not exists
INSERT OR IGNORE INTO markets (name, region, district, province, gps_lat, gps_lon, market_days, operating_hours, contact_phone, active, last_updated) VALUES
-- Lusaka Province
('Lusaka City Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.4167, 28.2833, 'Mon-Sat', '06:00-18:00', '+260211123456', 1, datetime('now')),
('Soweto Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.4278, 28.3022, 'Daily', '05:00-20:00', '+260211234567', 1, datetime('now')),
('Kalingalinga Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.3985, 28.3456, 'Daily', '06:00-19:00', '+260211345678', 1, datetime('now')),
('Chawama Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.4356, 28.2789, 'Daily', '06:00-19:00', '+260211456789', 1, datetime('now')),

-- Copperbelt Province
('Ndola Main Market', 'Copperbelt', 'Ndola', 'Copperbelt', -12.9587, 28.6366, 'Daily', '06:00-18:00', '+260212123456', 1, datetime('now')),
('Kitwe Central Market', 'Copperbelt', 'Kitwe', 'Copperbelt', -12.8024, 28.2132, 'Daily', '06:00-18:00', '+260212234567', 1, datetime('now')),
('Chingola Market', 'Copperbelt', 'Chingola', 'Copperbelt', -12.5387, 27.8823, 'Mon-Sat', '07:00-17:00', '+260212345678', 1, datetime('now')),
('Mufulira Market', 'Copperbelt', 'Mufulira', 'Copperbelt', -12.5514, 28.2412, 'Mon-Sat', '07:00-17:00', '+260212456789', 1, datetime('now')),
('Luanshya Market', 'Copperbelt', 'Luanshya', 'Copperbelt', -13.1377, 28.4164, 'Mon-Sat', '07:00-17:00', '+260212567890', 1, datetime('now')),

-- Central Province
('Kabwe Central Market', 'Central', 'Kabwe', 'Central', -14.4469, 28.4464, 'Mon-Sat', '06:00-18:00', '+260215123456', 1, datetime('now')),
('Kapiri Mposhi Market', 'Central', 'Kapiri Mposhi', 'Central', -13.9719, 28.6848, 'Mon-Sat', '07:00-17:00', '+260215234567', 1, datetime('now')),
('Serenje Market', 'Central', 'Serenje', 'Central', -13.2315, 30.2367, 'Mon-Fri', '08:00-17:00', '+260215345678', 1, datetime('now')),

-- Southern Province
('Livingstone Market', 'Southern', 'Livingstone', 'Southern', -17.8419, 25.8543, 'Mon-Sat', '06:00-18:00', '+260213123456', 1, datetime('now')),
('Choma Market', 'Southern', 'Choma', 'Southern', -16.8089, 26.9876, 'Mon-Sat', '07:00-17:00', '+260213234567', 1, datetime('now')),
('Monze Market', 'Southern', 'Monze', 'Southern', -16.2816, 27.4814, 'Mon-Sat', '07:00-17:00', '+260213345678', 1, datetime('now')),

-- Eastern Province
('Chipata Central Market', 'Eastern', 'Chipata', 'Eastern', -13.6433, 32.6442, 'Mon-Fri', '06:00-18:00', '+260216123456', 1, datetime('now')),
('Petauke Market', 'Eastern', 'Petauke', 'Eastern', -14.2489, 31.3256, 'Mon-Sat', '07:00-17:00', '+260216234567', 1, datetime('now')),
('Lundazi Market', 'Eastern', 'Lundazi', 'Eastern', -12.2903, 33.1797, 'Mon-Fri', '08:00-17:00', '+260216345678', 1, datetime('now')),

-- Western Province
('Mongu Market', 'Western', 'Mongu', 'Western', -15.2546, 23.1285, 'Mon-Sat', '07:00-18:00', '+260217123456', 1, datetime('now')),
('Kaoma Market', 'Western', 'Kaoma', 'Western', -14.7904, 24.8087, 'Mon-Fri', '08:00-17:00', '+260217234567', 1, datetime('now')),

-- North-Western Province
('Solwezi Market', 'North-Western', 'Solwezi', 'North-Western', -12.1777, 26.3968, 'Mon-Sat', '07:00-18:00', '+260218123456', 1, datetime('now')),
('Kasempa Market', 'North-Western', 'Kasempa', 'North-Western', -13.4571, 25.8315, 'Mon-Fri', '08:00-17:00', '+260218234567', 1, datetime('now')),

-- Luapula Province
('Mansa Market', 'Luapula', 'Mansa', 'Luapula', -11.2004, 28.8884, 'Mon-Sat', '07:00-17:00', '+260214123456', 1, datetime('now')),
('Kawambwa Market', 'Luapula', 'Kawambwa', 'Luapula', -9.7946, 29.0797, 'Mon-Fri', '08:00-17:00', '+260214234567', 1, datetime('now')),

-- Muchinga Province
('Chinsali Market', 'Muchinga', 'Chinsali', 'Muchinga', -10.5548, 32.0604, 'Mon-Sat', '07:00-17:00', '+260211987654', 1, datetime('now')),
('Mpika Market', 'Muchinga', 'Mpika', 'Muchinga', -11.8344, 31.4538, 'Mon-Fri', '08:00-17:00', '+260211876543', 1, datetime('now'));

-- =========================================================
-- STEP 2: ENSURE ALL COMMODITIES EXIST
-- =========================================================

INSERT OR IGNORE INTO commodities (name, category, unit, min_price, max_price, season_start, active) VALUES
-- Grains
('Maize', 'Grains', '50kg bag', 180, 350, 'April-June', 1),
('Rice', 'Grains', 'kg', 8, 18, 'May-July', 1),
('Sorghum', 'Grains', 'kg', 3, 7, 'April-June', 1),
('Millet', 'Grains', 'kg', 3.5, 8, 'April-June', 1),
('Wheat', 'Grains', 'kg', 4, 9, 'August-October', 1),

-- Legumes
('Beans', 'Legumes', 'kg', 10, 22, 'May-August', 1),
('Groundnuts', 'Legumes', 'kg', 12, 28, 'April-July', 1),
('Soybeans', 'Legumes', 'kg', 8, 18, 'April-June', 1),
('Cowpeas', 'Legumes', 'kg', 8, 15, 'May-July', 1),
('Pigeon Peas', 'Legumes', 'kg', 7, 14, 'June-August', 1),

-- Vegetables
('Tomatoes', 'Vegetables', 'kg', 5, 15, 'Year-round', 1),
('Onions', 'Vegetables', 'kg', 6, 14, 'June-September', 1),
('Cabbage', 'Vegetables', 'head', 4, 10, 'Year-round', 1),
('Rape', 'Vegetables', 'bunch', 2, 5, 'Year-round', 1),
('Okra', 'Vegetables', 'kg', 6, 15, 'December-March', 1),
('Eggplant', 'Vegetables', 'kg', 5, 12, 'Year-round', 1),
('Green Pepper', 'Vegetables', 'kg', 8, 20, 'Year-round', 1),

-- Tubers
('Cassava', 'Tubers', 'kg', 3, 8, 'Year-round', 1),
('Sweet Potatoes', 'Tubers', 'kg', 4, 10, 'Year-round', 1),
('Irish Potatoes', 'Tubers', 'kg', 8, 18, 'April-August', 1),

-- Fruits
('Bananas', 'Fruits', 'bunch', 8, 20, 'Year-round', 1),
('Oranges', 'Fruits', 'kg', 5, 12, 'June-October', 1),
('Mangoes', 'Fruits', 'kg', 4, 12, 'October-December', 1),
('Avocado', 'Fruits', 'each', 2, 5, 'January-March', 1),
('Pineapples', 'Fruits', 'each', 8, 18, 'October-December', 1),
('Watermelon', 'Fruits', 'kg', 3, 8, 'September-November', 1),

-- Cash Crops
('Cotton', 'Cash Crops', 'kg', 6, 12, 'April-June', 1),
('Sunflower', 'Cash Crops', 'kg', 8, 16, 'April-June', 1),

-- Livestock Products
('Beef', 'Livestock', 'kg', 40, 65, 'Year-round', 1),
('Chicken', 'Livestock', 'each', 25, 45, 'Year-round', 1),
('Goat Meat', 'Livestock', 'kg', 35, 55, 'Year-round', 1),
('Eggs', 'Livestock', 'tray', 18, 30, 'Year-round', 1),
('Milk', 'Livestock', 'litre', 10, 18, 'Year-round', 1),

-- Other
('Honey', 'Other', 'kg', 40, 80, 'September-November', 1),
('Coffee', 'Other', 'kg', 25, 50, 'May-August', 1);

-- =========================================================
-- STEP 3: GENERATE MARKET PRICES WITH REALISTIC VARIATIONS
-- Price factors: location (urban = higher), region (Copperbelt = higher due to mining salaries)
-- =========================================================

-- Price adjustment factors by market type
-- Urban markets (Lusaka, Ndola, Kitwe) have higher prices
-- Rural markets have lower prices
-- Remote markets have significantly lower prices

-- =========================================================
-- LUSAKA MARKETS (Highest prices - Capital city premium)
-- =========================================================

-- Lusaka City Market prices (Premium urban prices)
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Lusaka City Market',
    name,
    CASE name
        -- Grains
        WHEN 'Maize' THEN ROUND(7.20 + (RANDOM() % 40)/100, 2)
        WHEN 'Rice' THEN ROUND(14.50 + (RANDOM() % 100)/100, 2)
        WHEN 'Sorghum' THEN ROUND(6.50 + (RANDOM() % 50)/100, 2)
        WHEN 'Millet' THEN ROUND(7.00 + (RANDOM() % 50)/100, 2)
        WHEN 'Wheat' THEN ROUND(8.00 + (RANDOM() % 60)/100, 2)
        -- Legumes
        WHEN 'Beans' THEN ROUND(18.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(24.00 + (RANDOM() % 120)/100, 2)
        WHEN 'Soybeans' THEN ROUND(15.00 + (RANDOM() % 80)/100, 2)
        WHEN 'Cowpeas' THEN ROUND(13.00 + (RANDOM() % 80)/100, 2)
        WHEN 'Pigeon Peas' THEN ROUND(12.00 + (RANDOM() % 80)/100, 2)
        -- Vegetables
        WHEN 'Tomatoes' THEN ROUND(10.50 + (RANDOM() % 150)/100, 2)
        WHEN 'Onions' THEN ROUND(11.00 + (RANDOM() % 120)/100, 2)
        WHEN 'Cabbage' THEN ROUND(8.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Rape' THEN ROUND(4.00 + (RANDOM() % 50)/100, 2)
        WHEN 'Okra' THEN ROUND(12.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Eggplant' THEN ROUND(9.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Green Pepper' THEN ROUND(16.00 + (RANDOM() % 120)/100, 2)
        -- Tubers
        WHEN 'Cassava' THEN ROUND(6.50 + (RANDOM() % 60)/100, 2)
        WHEN 'Sweet Potatoes' THEN ROUND(8.00 + (RANDOM() % 80)/100, 2)
        WHEN 'Irish Potatoes' THEN ROUND(15.00 + (RANDOM() % 100)/100, 2)
        -- Fruits
        WHEN 'Bananas' THEN ROUND(16.00 + (RANDOM() % 120)/100, 2)
        WHEN 'Oranges' THEN ROUND(10.00 + (RANDOM() % 80)/100, 2)
        WHEN 'Mangoes' THEN ROUND(9.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Avocado' THEN ROUND(4.00 + (RANDOM() % 40)/100, 2)
        WHEN 'Pineapples' THEN ROUND(14.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Watermelon' THEN ROUND(6.00 + (RANDOM() % 60)/100, 2)
        -- Cash Crops
        WHEN 'Cotton' THEN ROUND(10.00 + (RANDOM() % 60)/100, 2)
        WHEN 'Sunflower' THEN ROUND(14.00 + (RANDOM() % 80)/100, 2)
        -- Livestock
        WHEN 'Beef' THEN ROUND(55.00 + (RANDOM() % 200)/100, 2)
        WHEN 'Chicken' THEN ROUND(40.00 + (RANDOM() % 150)/100, 2)
        WHEN 'Goat Meat' THEN ROUND(50.00 + (RANDOM() % 200)/100, 2)
        WHEN 'Eggs' THEN ROUND(28.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Milk' THEN ROUND(16.00 + (RANDOM() % 80)/100, 2)
        -- Other
        WHEN 'Honey' THEN ROUND(70.00 + (RANDOM() % 300)/100, 2)
        WHEN 'Coffee' THEN ROUND(45.00 + (RANDOM() % 200)/100, 2)
        ELSE 10.00
    END,
    'ZMW/kg',
    CASE name
        WHEN 'Maize' THEN 5000 + (RANDOM() % 3000)
        WHEN 'Rice' THEN 2000 + (RANDOM() % 1500)
        WHEN 'Beans' THEN 1500 + (RANDOM() % 1000)
        WHEN 'Tomatoes' THEN 3000 + (RANDOM() % 2000)
        WHEN 'Onions' THEN 2000 + (RANDOM() % 1500)
        ELSE 1000 + (RANDOM() % 2000)
    END,
    'Grade A',
    'Market Survey',
    1,
    datetime('now', '-1 days'),
    'Lusaka',
    CASE (RANDOM() % 3)
        WHEN 0 THEN 'up'
        WHEN 1 THEN 'down'
        ELSE 'stable'
    END,
    'Premium urban market price'
FROM commodities WHERE active = 1;

-- Soweto Market prices (Similar to Lusaka City)
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Soweto Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(7.10 + (RANDOM() % 40)/100, 2)
        WHEN 'Rice' THEN ROUND(14.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Beans' THEN ROUND(17.50 + (RANDOM() % 100)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(23.50 + (RANDOM() % 120)/100, 2)
        WHEN 'Tomatoes' THEN ROUND(10.00 + (RANDOM() % 150)/100, 2)
        WHEN 'Onions' THEN ROUND(10.50 + (RANDOM() % 120)/100, 2)
        WHEN 'Cabbage' THEN ROUND(7.80 + (RANDOM() % 100)/100, 2)
        WHEN 'Beef' THEN ROUND(54.00 + (RANDOM() % 200)/100, 2)
        WHEN 'Chicken' THEN ROUND(38.00 + (RANDOM() % 150)/100, 2)
        WHEN 'Eggs' THEN ROUND(27.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Milk' THEN ROUND(15.50 + (RANDOM() % 80)/100, 2)
        ELSE price * 0.98
    END,
    'ZMW/kg',
    CASE name
        WHEN 'Maize' THEN 4000 + (RANDOM() % 2500)
        ELSE 800 + (RANDOM() % 1500)
    END,
    'Grade A',
    'Market Survey',
    1,
    datetime('now', '-2 days'),
    'Lusaka',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' WHEN 1 THEN 'down' ELSE 'stable' END,
    'Major Lusaka market'
FROM commodities WHERE active = 1;

-- =========================================================
-- COPPERBELT MARKETS (High prices due to mining economy)
-- =========================================================

-- Ndola Main Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Ndola Main Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(6.90 + (RANDOM() % 40)/100, 2)
        WHEN 'Rice' THEN ROUND(13.50 + (RANDOM() % 100)/100, 2)
        WHEN 'Beans' THEN ROUND(17.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(23.00 + (RANDOM() % 120)/100, 2)
        WHEN 'Tomatoes' THEN ROUND(9.80 + (RANDOM() % 150)/100, 2)
        WHEN 'Onions' THEN ROUND(10.00 + (RANDOM() % 120)/100, 2)
        WHEN 'Beef' THEN ROUND(52.00 + (RANDOM() % 200)/100, 2)
        WHEN 'Chicken' THEN ROUND(37.00 + (RANDOM() % 150)/100, 2)
        ELSE price * 0.95
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 4500 + (RANDOM() % 3000) ELSE 700 + (RANDOM() % 1200) END,
    'Grade A',
    'Copperbelt Survey',
    1,
    datetime('now', '-1 days'),
    'Copperbelt',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' WHEN 1 THEN 'down' ELSE 'stable' END,
    'Major Copperbelt market'
FROM commodities WHERE active = 1;

-- Kitwe Central Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Kitwe Central Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(6.95 + (RANDOM() % 40)/100, 2)
        WHEN 'Rice' THEN ROUND(13.80 + (RANDOM() % 100)/100, 2)
        WHEN 'Beans' THEN ROUND(17.20 + (RANDOM() % 100)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(23.20 + (RANDOM() % 120)/100, 2)
        ELSE price * 0.96
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 4200 + (RANDOM() % 2800) ELSE 650 + (RANDOM() % 1000) END,
    'Grade A',
    'Copperbelt Survey',
    1,
    datetime('now', '-3 days'),
    'Copperbelt',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' WHEN 1 THEN 'down' ELSE 'stable' END,
    'Kitwe central hub'
FROM commodities WHERE active = 1;

-- =========================================================
-- CENTRAL PROVINCE MARKETS (Moderate prices)
-- =========================================================

-- Kabwe Central Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Kabwe Central Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(6.50 + (RANDOM() % 35)/100, 2)
        WHEN 'Rice' THEN ROUND(12.50 + (RANDOM() % 90)/100, 2)
        WHEN 'Beans' THEN ROUND(16.00 + (RANDOM() % 90)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(21.00 + (RANDOM() % 110)/100, 2)
        WHEN 'Tomatoes' THEN ROUND(8.50 + (RANDOM() % 130)/100, 2)
        WHEN 'Onions' THEN ROUND(9.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Beef' THEN ROUND(48.00 + (RANDOM() % 180)/100, 2)
        WHEN 'Chicken' THEN ROUND(34.00 + (RANDOM() % 130)/100, 2)
        ELSE price * 0.92
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 3500 + (RANDOM() % 2500) ELSE 500 + (RANDOM() % 800) END,
    'Standard Grade',
    'Central Province Survey',
    1,
    datetime('now', '-1 days'),
    'Central',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' WHEN 1 THEN 'down' ELSE 'stable' END,
    'Central province hub'
FROM commodities WHERE active = 1;

-- =========================================================
-- SOUTHERN PROVINCE MARKETS (Agricultural hub, moderate prices)
-- =========================================================

-- Livingstone Market (Tourist area, higher prices)
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Livingstone Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(6.80 + (RANDOM() % 40)/100, 2)
        WHEN 'Rice' THEN ROUND(13.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Beans' THEN ROUND(16.50 + (RANDOM() % 100)/100, 2)
        WHEN 'Tomatoes' THEN ROUND(9.50 + (RANDOM() % 140)/100, 2)
        ELSE price * 0.94
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 3000 + (RANDOM() % 2000) ELSE 400 + (RANDOM() % 700) END,
    'Fresh Grade',
    'Southern Survey',
    1,
    datetime('now', '-2 days'),
    'Southern',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' WHEN 1 THEN 'down' ELSE 'stable' END,
    'Tourist area market'
FROM commodities WHERE active = 1;

-- Choma Market (Agricultural area, lower prices)
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Choma Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(6.30 + (RANDOM() % 30)/100, 2)
        WHEN 'Beans' THEN ROUND(15.00 + (RANDOM() % 80)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(20.00 + (RANDOM() % 100)/100, 2)
        ELSE price * 0.90
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 2800 + (RANDOM() % 1800) ELSE 350 + (RANDOM() % 600) END,
    'Fresh Grade',
    'Agricultural Survey',
    1,
    datetime('now', '-1 days'),
    'Southern',
    'stable',
    'Agricultural production area'
FROM commodities WHERE active = 1;

-- =========================================================
-- EASTERN PROVINCE MARKETS (Lower prices, major production)
-- =========================================================

-- Chipata Central Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Chipata Central Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(6.00 + (RANDOM() % 30)/100, 2)
        WHEN 'Groundnuts' THEN ROUND(18.00 + (RANDOM() % 100)/100, 2)
        WHEN 'Soybeans' THEN ROUND(11.00 + (RANDOM() % 70)/100, 2)
        WHEN 'Cotton' THEN ROUND(7.50 + (RANDOM() % 50)/100, 2)
        ELSE price * 0.85
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 5000 + (RANDOM() % 4000) WHEN 'Cotton' THEN 3000 + (RANDOM() % 2000) ELSE 300 + (RANDOM() % 500) END,
    'Farm Fresh',
    'Eastern Province Survey',
    1,
    datetime('now', '-1 days'),
    'Eastern',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' WHEN 1 THEN 'down' ELSE 'stable' END,
    'Major agricultural hub'
FROM commodities WHERE active = 1;

-- =========================================================
-- WESTERN PROVINCE MARKETS (Lower prices, remote area)
-- =========================================================

-- Mongu Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Mongu Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(5.80 + (RANDOM() % 25)/100, 2)
        WHEN 'Rice' THEN ROUND(11.00 + (RANDOM() % 80)/100, 2)
        WHEN 'Cassava' THEN ROUND(4.50 + (RANDOM() % 30)/100, 2)
        ELSE price * 0.82
    END,
    'ZMW/kg',
    CASE name WHEN 'Cassava' THEN 2000 + (RANDOM() % 1500) ELSE 250 + (RANDOM() % 400) END,
    'Local Grade',
    'Western Survey',
    1,
    datetime('now', '-3 days'),
    'Western',
    'stable',
    'Remote market, lower prices'
FROM commodities WHERE active = 1;

-- =========================================================
-- NORTH-WESTERN PROVINCE (Mining area, higher prices)
-- =========================================================

-- Solwezi Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Solwezi Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(7.00 + (RANDOM() % 40)/100, 2)
        WHEN 'Beans' THEN ROUND(17.50 + (RANDOM() % 100)/100, 2)
        WHEN 'Beef' THEN ROUND(56.00 + (RANDOM() % 200)/100, 2)
        ELSE price * 0.97
    END,
    'ZMW/kg',
    CASE name WHEN 'Maize' THEN 3500 + (RANDOM() % 2500) ELSE 600 + (RANDOM() % 1000) END,
    'Premium Grade',
    'North-Western Survey',
    1,
    datetime('now', '-2 days'),
    'North-Western',
    CASE (RANDOM() % 3) WHEN 0 THEN 'up' ELSE 'stable' END,
    'Mining town premium prices'
FROM commodities WHERE active = 1;

-- =========================================================
-- LUAPULA PROVINCE (Remote, lower prices)
-- =========================================================

-- Mansa Market
INSERT INTO market_prices (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
SELECT 
    'Mansa Market',
    name,
    CASE name
        WHEN 'Maize' THEN ROUND(5.90 + (RANDOM() % 25)/100, 2)
        WHEN 'Cassava' THEN ROUND(4.00 + (RANDOM() % 30)/100, 2)
        ELSE price * 0.83
    END,
    'ZMW/kg',
    CASE name WHEN 'Cassava' THEN 2500 + (RANDOM() % 2000) ELSE 200 + (RANDOM() % 350) END,
    'Local Grade',
    'Luapula Survey',
    1,
    datetime('now', '-4 days'),
    'Luapula',
    'stable',
    'Remote Luapula market'
FROM commodities WHERE active = 1;

-- =========================================================
-- STEP 4: ADD PRICE HISTORY FOR TREND ANALYSIS
-- =========================================================

-- Insert historical prices for the last 30 days (simplified version)
INSERT INTO price_history (commodity, market, price, recorded_at, source)
SELECT 
    'Maize',
    'Lusaka City Market',
    ROUND(6.50 + (RANDOM() % 100)/100, 2),
    datetime('now', '-' || (abs(random() % 30) || ' days')),
    'Historical Data'
FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10);

INSERT INTO price_history (commodity, market, price, recorded_at, source)
SELECT 
    'Tomatoes',
    'Lusaka City Market',
    ROUND(8.00 + (RANDOM() % 150)/100, 2),
    datetime('now', '-' || (abs(random() % 30) || ' days')),
    'Historical Data'
FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10);

INSERT INTO price_history (commodity, market, price, recorded_at, source)
SELECT 
    'Beans',
    'Ndola Main Market',
    ROUND(14.00 + (RANDOM() % 100)/100, 2),
    datetime('now', '-' || (abs(random() % 30) || ' days')),
    'Historical Data'
FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10);

-- =========================================================
-- STEP 5: ADD SAMPLE BUYERS FOR EACH COMMODITY
-- =========================================================

INSERT OR IGNORE INTO buyers (name, phone, email, commodity, location, max_price, min_volume, max_volume, payment_terms, delivery_requirements, verified, rating, status, created_at) VALUES
-- Maize buyers
('Zambia Grain Traders', '+260971111111', 'trading@zambiagrains.com', 'Maize', 'Lusaka', 7.50, 5000, 50000, 'Bank transfer within 7 days', 'Clean, dry maize, moisture <14%', 1, 4.8, 'active', datetime('now')),
('Agri Export Ltd', '+260972222222', 'exports@agriltd.com', 'Maize', 'Ndola', 7.20, 10000, 100000, 'Letter of Credit', 'Grade A, non-GMO', 1, 4.5, 'active', datetime('now')),
('National Food Reserve', '+260973333333', 'procurement@nfr.gov.zm', 'Maize', 'Lusaka', 7.00, 50000, 500000, 'Government payment terms', 'FRA Grade A standard', 1, 4.9, 'active', datetime('now')),

-- Tomatoes buyers
('Fresh Produce Ltd', '+260974444444', 'fresh@produce.co.zm', 'Tomatoes', 'Lusaka', 12.00, 1000, 10000, 'Cash on delivery', 'Fresh, no blemishes', 1, 4.3, 'active', datetime('now')),
('Supermarket Chain', '+260975555555', 'procurement@supersave.zm', 'Tomatoes', 'Kitwe', 11.50, 2000, 15000, 'Net 15 days', 'Grade A, uniform size', 1, 4.2, 'active', datetime('now')),

-- Beans buyers
('Beans Exporters Inc', '+260976666666', 'beans@export.zm', 'Beans', 'Lusaka', 19.00, 3000, 25000, '30% deposit, balance on delivery', 'Premium grade, sorted', 1, 4.6, 'active', datetime('now')),
('Local Food Processors', '+260977777777', 'procurement@foodproc.zm', 'Beans', 'Kabwe', 17.50, 2000, 20000, 'Net 30 days', 'Clean, no stones', 1, 4.1, 'active', datetime('now')),

-- Groundnuts buyers
('Groundnut Oil Mills', '+260978888888', 'oil@groundnuts.zm', 'Groundnuts', 'Lusaka', 25.00, 2000, 20000, 'Bank transfer', 'High oil content >45%', 1, 4.4, 'active', datetime('now')),
('Snack Foods Ltd', '+260979999999', 'snacks@foods.zm', 'Groundnuts', 'Ndola', 24.00, 1000, 10000, 'Net 15 days', 'Roasting grade', 1, 4.0, 'active', datetime('now')),

-- Soybeans buyers
('Soybean Processors', '+260980000000', 'soy@processors.zm', 'Soybeans', 'Lusaka', 16.00, 5000, 50000, 'Letter of Credit', 'Non-GMO, high protein', 1, 4.7, 'active', datetime('now')),
('Animal Feed Ltd', '+260981111111', 'feed@animals.zm', 'Soybeans', 'Kitwe', 15.00, 3000, 30000, 'Net 30 days', 'For animal feed', 1, 4.2, 'active', datetime('now')),

-- Cassava buyers
('Cassava Processing', '+260982222222', 'cassava@process.zm', 'Cassava', 'Mansa', 7.00, 5000, 40000, 'Cash on delivery', 'Fresh, high starch', 1, 4.3, 'active', datetime('now')),

-- Sweet Potatoes buyers
('Fresh Produce Export', '+260983333333', 'export@fresh.zm', 'Sweet Potatoes', 'Lusaka', 9.00, 1000, 8000, 'Net 14 days', 'Orange-fleshed preferred', 1, 4.1, 'active', datetime('now')),

-- Beef buyers
('Butchery Chain', '+260984444444', 'meat@butchery.zm', 'Beef', 'Lusaka', 60.00, 500, 5000, 'Weekly payment', 'Grade A beef', 1, 4.5, 'active', datetime('now')),
('Hotel Suppliers Ltd', '+260985555555', 'supply@hotels.zm', 'Beef', 'Livingstone', 58.00, 300, 3000, 'Net 7 days', 'Premium cuts', 1, 4.4, 'active', datetime('now')),

-- Chicken buyers
('Poultry Processors', '+260986666666', 'poultry@process.zm', 'Chicken', 'Lusaka', 42.00, 500, 5000, 'Cash on delivery', 'Broilers 1.5-2kg', 1, 4.6, 'active', datetime('now')),
('Fast Food Chain', '+260987777777', 'procurement@fastfood.zm', 'Chicken', 'Ndola', 40.00, 300, 3000, 'Net 15 days', 'Fresh, not frozen', 1, 4.2, 'active', datetime('now')),

-- Eggs buyers
('Bakery Chain', '+260988888888', 'eggs@bakery.zm', 'Eggs', 'Lusaka', 30.00, 1000, 10000, 'Weekly payment', 'Large eggs, Grade A', 1, 4.7, 'active', datetime('now')),
('Hotel Group', '+260989999999', 'hotel@group.zm', 'Eggs', 'Livingstone', 29.00, 500, 5000, 'Net 14 days', 'Fresh eggs', 1, 4.3, 'active', datetime('now')),

-- Milk buyers
('Dairy Processors', '+260990000000', 'dairy@process.zm', 'Milk', 'Lusaka', 17.00, 2000, 20000, 'Bank transfer weekly', 'Raw milk, 3.5% fat', 1, 4.8, 'active', datetime('now')),
('Cheese Factory', '+260991111111', 'cheese@factory.zm', 'Milk', 'Kabwe', 16.50, 1000, 10000, 'Net 30 days', 'High quality', 1, 4.4, 'active', datetime('now')),

-- Multi-commodity buyers (trading houses)
('Agri Trading House', '+260992222222', 'trade@agri.zm', 'All Crops', 'Lusaka', 0, 10000, 0, 'Letter of Credit', 'Export quality only', 1, 4.9, 'active', datetime('now')),
('Zambia Commodities Exchange', '+260993333333', 'info@zce.co.zm', 'All Crops', 'Lusaka', 0, 5000, 0, 'Exchange settlement', 'Standard grades', 1, 4.8, 'active', datetime('now'));

-- =========================================================
-- STEP 6: UPDATE STATS COUNTS
-- =========================================================

-- Display summary of inserted data
SELECT '========================================' AS '';
SELECT 'DATA IMPORT SUMMARY' AS '';
SELECT '========================================' AS '';
SELECT COUNT(*) || ' markets loaded' AS '' FROM markets;
SELECT COUNT(*) || ' commodities loaded' AS '' FROM commodities;
SELECT COUNT(*) || ' market prices loaded' AS '' FROM market_prices;
SELECT COUNT(*) || ' price history records loaded' AS '' FROM price_history;
SELECT COUNT(*) || ' buyers loaded' AS '' FROM buyers;
SELECT '========================================' AS '';

-- =========================================================
-- END OF DATA GENERATION SCRIPT
-- =========================================================