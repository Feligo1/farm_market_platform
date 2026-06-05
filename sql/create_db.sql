-- ===========================================================
-- Project: Cloud-Based Market Information Platform for Farmers
-- Database: farm_market_platform
-- Author: Tech Guy (Mulungushi University)
-- Purpose: Create schema and load initial sample data
-- ===========================================================

-- 1. Create the database (if not already existing)
CREATE DATABASE IF NOT EXISTS farm_market_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

-- 2. Select the database
USE farm_market_platform;

-- 3. Create the 'prices' table
CREATE TABLE IF NOT EXISTS prices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  market VARCHAR(100) NOT NULL,
  commodity VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  volume INT DEFAULT 0,
  recorded_at DATE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Insert sample data (15 days across Maize and Tomatoes)
INSERT INTO prices (market, commodity, price, volume, recorded_at) VALUES
('Lusaka Central', 'Maize', 1500.00, 500, '2025-10-18'),
('Lusaka Central', 'Maize', 1520.00, 480, '2025-10-19'),
('Lusaka Central', 'Maize', 1510.00, 510, '2025-10-20'),
('Lusaka Central', 'Maize', 1535.00, 470, '2025-10-21'),
('Lusaka Central', 'Maize', 1540.00, 460, '2025-10-22'),
('Kabwe Main', 'Maize', 1480.00, 600, '2025-10-18'),
('Kabwe Main', 'Maize', 1495.00, 620, '2025-10-19'),
('Kabwe Main', 'Maize', 1500.00, 580, '2025-10-20'),
('Kabwe Main', 'Maize', 1510.00, 550, '2025-10-21'),
('Kabwe Main', 'Maize', 1515.00, 540, '2025-10-22'),
('Lusaka Central', 'Tomatoes', 5000.00, 200, '2025-10-18'),
('Lusaka Central', 'Tomatoes', 4900.00, 210, '2025-10-19'),
('Kabwe Main', 'Tomatoes', 4800.00, 300, '2025-10-18'),
('Kabwe Main', 'Tomatoes', 4750.00, 290, '2025-10-19'),
('Lusaka Central', 'Maize', 1550.00, 450, '2025-10-23');

-- 5. Verify data
SELECT COUNT(*) AS total_records FROM prices;

-- 6. Optional: show sample output
SELECT * FROM prices LIMIT 10;
