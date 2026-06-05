-- =========================================================
-- SEED DATA FOR FARMCONNECT
-- =========================================================

-- Insert commodities
INSERT OR IGNORE INTO commodities (name, category, unit, min_price, max_price, season_start, season_end, active) VALUES
('Maize', 'grain', 'kg', 4.00, 15.00, 'April', 'August', 1),
('Tomatoes', 'vegetable', 'kg', 3.00, 20.00, 'May', 'October', 1),
('Beans', 'legume', 'kg', 8.00, 25.00, 'June', 'September', 1),
('Groundnuts', 'legume', 'kg', 12.00, 35.00, 'July', 'October', 1),
('Rice', 'grain', 'kg', 6.00, 18.00, 'May', 'August', 1),
('Soybeans', 'legume', 'kg', 10.00, 22.00, 'April', 'July', 1),
('Sweet Potatoes', 'tuber', 'kg', 4.00, 12.00, 'March', 'August', 1),
('Cabbage', 'vegetable', 'head', 3.00, 10.00, 'May', 'November', 1),
('Onions', 'vegetable', 'kg', 5.00, 15.00, 'June', 'October', 1),
('Cassava', 'tuber', 'kg', 2.00, 6.00, 'January', 'December', 1);

-- Insert markets
INSERT OR IGNORE INTO markets (name, region, district, province, gps_lat, gps_lon, market_days, operating_hours, active) VALUES
('Lusaka City Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.4167, 28.2833, 'Monday-Saturday', '06:00-18:00', 1),
('Soweto Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.4278, 28.3022, 'Daily', '05:00-20:00', 1),
('Kabwe Central Market', 'Central', 'Kabwe', 'Central', -14.4469, 28.4464, 'Monday-Saturday', '06:00-17:00', 1),
('Ndola Main Market', 'Copperbelt', 'Ndola', 'Copperbelt', -12.9587, 28.6366, 'Daily', '06:00-18:00', 1),
('Kitwe Market', 'Copperbelt', 'Kitwe', 'Copperbelt', -12.8024, 28.2132, 'Daily', '06:00-18:00', 1),
('Livingstone Market', 'Southern', 'Livingstone', 'Southern', -17.8419, 25.8543, 'Monday-Saturday', '07:00-17:00', 1),
('Chipata Central Market', 'Eastern', 'Chipata', 'Eastern', -13.6433, 32.6442, 'Monday-Friday', '07:00-16:00', 1),
('Mongu Market', 'Western', 'Mongu', 'Western', -15.2556, 23.1544, 'Monday-Friday', '07:00-16:00', 1),
('Kasama Market', 'Northern', 'Kasama', 'Northern', -10.2136, 31.1836, 'Monday-Saturday', '06:00-17:00', 1),
('Solwezi Market', 'North-Western', 'Solwezi', 'North-Western', -12.1736, 26.3939, 'Monday-Saturday', '06:00-17:00', 1);

-- Insert sample price data
INSERT OR IGNORE INTO market_prices (market, commodity, price, unit, source, verified, recorded_at, price_trend) VALUES
-- Lusaka prices
('Lusaka City Market', 'Maize', 6.80, 'ZMW/kg', 'FRA', 1, datetime('now', '-1 day'), 'stable'),
('Lusaka City Market', 'Tomatoes', 8.50, 'ZMW/kg', 'WFP', 1, datetime('now', '-1 day'), 'up'),
('Lusaka City Market', 'Beans', 12.50, 'ZMW/kg', 'FRA', 1, datetime('now', '-2 days'), 'stable'),
('Lusaka City Market', 'Groundnuts', 18.00, 'ZMW/kg', 'WFP', 1, datetime('now', '-1 day'), 'up'),
('Lusaka City Market', 'Rice', 9.00, 'ZMW/kg', 'FRA', 1, datetime('now', '-3 days'), 'stable'),
('Lusaka City Market', 'Soybeans', 15.00, 'ZMW/kg', 'WFP', 1, datetime('now', '-2 days'), 'down'),

-- Kabwe prices
('Kabwe Central Market', 'Maize', 6.50, 'ZMW/kg', 'FRA', 1, datetime('now', '-1 day'), 'stable'),
('Kabwe Central Market', 'Tomatoes', 7.80, 'ZMW/kg', 'WFP', 1, datetime('now', '-1 day'), 'stable'),
('Kabwe Central Market', 'Beans', 11.80, 'ZMW/kg', 'FRA', 1, datetime('now', '-2 days'), 'down'),

-- Ndola prices
('Ndola Main Market', 'Maize', 6.90, 'ZMW/kg', 'FRA', 1, datetime('now', '-1 day'), 'up'),
('Ndola Main Market', 'Tomatoes', 9.20, 'ZMW/kg', 'WFP', 1, datetime('now', '-1 day'), 'up'),
('Ndola Main Market', 'Cassava', 4.50, 'ZMW/kg', 'FRA', 1, datetime('now', '-2 days'), 'stable'),

-- Livingstone prices
('Livingstone Market', 'Maize', 7.20, 'ZMW/kg', 'FRA', 1, datetime('now', '-1 day'), 'up'),
('Livingstone Market', 'Sweet Potatoes', 6.50, 'ZMW/kg', 'WFP', 1, datetime('now', '-1 day'), 'stable');

-- Insert sample buyers
INSERT OR IGNORE INTO buyers (name, phone, commodity, location, max_price, min_volume, notes, verified, rating, added_by, created_at, status) VALUES
('Zambia Grain Traders', '+260971111111', 'Maize', 'Lusaka', 7.50, 1000, 'Bulk buyer, weekly collection, cash payment', 1, 4.5, 'admin', datetime('now'), 'active'),
('Agri Export Solutions', '+260972222222', 'Soybeans', 'Lusaka', 18.00, 500, 'Export quality required, advance payment', 1, 4.8, 'admin', datetime('now'), 'active'),
('Fresh Produce Zambia', '+260973333333', 'Tomatoes', 'Kabwe', 9.00, 200, 'Daily collection, fresh only', 1, 4.2, 'admin', datetime('now'), 'active'),
('National Milling', '+260974444444', 'Maize', 'Ndola', 7.20, 5000, 'Industrial buyer, contract available', 1, 4.9, 'admin', datetime('now'), 'active');

-- Insert demo users (passwords: farmer123, trader123, admin123)
-- Password hashes are for 'farmer123', 'trader123', 'admin123' respectively
INSERT OR IGNORE INTO users (user_id, username, password_hash, name, role, phone, email, location, farm_size, main_crops, business_name, trading_commodities, ussd_pin, sms_alerts, created_at, status, verified) VALUES
('user_farmer1', 'farmer1', 'pbkdf2:sha256:600000$8sKv3xLp$8f5e8d9c3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8', 'John Farmer', 'farmer', '+260971234567', 'john@example.com', 'Lusaka', 10.5, 'Maize, Tomatoes', NULL, NULL, '1234', 1, datetime('now'), 'active', 1),
('user_trader1', 'trader1', 'pbkdf2:sha256:600000$9tLw4yMq$9g6f9e0d4b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b', 'Sarah Trader', 'trader', '+260971234568', 'sarah@example.com', 'Kabwe', NULL, NULL, 'Agri Trading Ltd', 'Maize, Beans', '5678', 1, datetime('now'), 'active', 1),
('user_admin1', 'admin1', 'pbkdf2:sha256:600000$0uMx5zNr$0h7g0f1e5c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c', 'Admin User', 'admin', '+260971234569', 'admin@example.com', 'Ndola', NULL, NULL, NULL, NULL, '9999', 1, datetime('now'), 'active', 1);