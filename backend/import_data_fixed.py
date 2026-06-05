import sqlite3
import os
import random
from datetime import datetime, timedelta

# Connect to your database
conn = sqlite3.connect('farm_market.db')
cursor = conn.cursor()

print("🚀 Starting data import...")

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# =========================================================
# STEP 1: Insert missing markets (INSERT OR IGNORE)
# =========================================================
print("\n📊 Adding markets...")

markets = [
    # Lusaka Province
    ('Kalingalinga Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.3985, 28.3456, 'Daily', '06:00-19:00', '+260211345678', 1, datetime.now().isoformat()),
    ('Chawama Market', 'Lusaka', 'Lusaka', 'Lusaka', -15.4356, 28.2789, 'Daily', '06:00-19:00', '+260211456789', 1, datetime.now().isoformat()),
    # Copperbelt Province
    ('Chingola Market', 'Copperbelt', 'Chingola', 'Copperbelt', -12.5387, 27.8823, 'Mon-Sat', '07:00-17:00', '+260212345678', 1, datetime.now().isoformat()),
    ('Mufulira Market', 'Copperbelt', 'Mufulira', 'Copperbelt', -12.5514, 28.2412, 'Mon-Sat', '07:00-17:00', '+260212456789', 1, datetime.now().isoformat()),
    ('Luanshya Market', 'Copperbelt', 'Luanshya', 'Copperbelt', -13.1377, 28.4164, 'Mon-Sat', '07:00-17:00', '+260212567890', 1, datetime.now().isoformat()),
    # Central Province
    ('Kapiri Mposhi Market', 'Central', 'Kapiri Mposhi', 'Central', -13.9719, 28.6848, 'Mon-Sat', '07:00-17:00', '+260215234567', 1, datetime.now().isoformat()),
    ('Serenje Market', 'Central', 'Serenje', 'Central', -13.2315, 30.2367, 'Mon-Fri', '08:00-17:00', '+260215345678', 1, datetime.now().isoformat()),
    # Southern Province
    ('Monze Market', 'Southern', 'Monze', 'Southern', -16.2816, 27.4814, 'Mon-Sat', '07:00-17:00', '+260213345678', 1, datetime.now().isoformat()),
    # Eastern Province
    ('Petauke Market', 'Eastern', 'Petauke', 'Eastern', -14.2489, 31.3256, 'Mon-Sat', '07:00-17:00', '+260216234567', 1, datetime.now().isoformat()),
    ('Lundazi Market', 'Eastern', 'Lundazi', 'Eastern', -12.2903, 33.1797, 'Mon-Fri', '08:00-17:00', '+260216345678', 1, datetime.now().isoformat()),
    # Western Province
    ('Kaoma Market', 'Western', 'Kaoma', 'Western', -14.7904, 24.8087, 'Mon-Fri', '08:00-17:00', '+260217234567', 1, datetime.now().isoformat()),
    # North-Western Province
    ('Kasempa Market', 'North-Western', 'Kasempa', 'North-Western', -13.4571, 25.8315, 'Mon-Fri', '08:00-17:00', '+260218234567', 1, datetime.now().isoformat()),
    # Luapula Province
    ('Kawambwa Market', 'Luapula', 'Kawambwa', 'Luapula', -9.7946, 29.0797, 'Mon-Fri', '08:00-17:00', '+260214234567', 1, datetime.now().isoformat()),
    # Muchinga Province
    ('Chinsali Market', 'Muchinga', 'Chinsali', 'Muchinga', -10.5548, 32.0604, 'Mon-Sat', '07:00-17:00', '+260211987654', 1, datetime.now().isoformat()),
    ('Mpika Market', 'Muchinga', 'Mpika', 'Muchinga', -11.8344, 31.4538, 'Mon-Fri', '08:00-17:00', '+260211876543', 1, datetime.now().isoformat()),
]

for market in markets:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO markets 
            (name, region, district, province, gps_lat, gps_lon, market_days, operating_hours, contact_phone, active, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, market)
    except Exception as e:
        print(f"  ⚠️ Error adding market {market[0]}: {e}")

# =========================================================
# STEP 2: Insert missing commodities
# =========================================================
print("\n🌾 Adding commodities...")

commodities = [
    ('Cowpeas', 'Legumes', 'kg', 8, 15, 'May-July', 1),
    ('Pigeon Peas', 'Legumes', 'kg', 7, 14, 'June-August', 1),
    ('Okra', 'Vegetables', 'kg', 6, 15, 'December-March', 1),
    ('Eggplant', 'Vegetables', 'kg', 5, 12, 'Year-round', 1),
    ('Green Pepper', 'Vegetables', 'kg', 8, 20, 'Year-round', 1),
    ('Irish Potatoes', 'Tubers', 'kg', 8, 18, 'April-August', 1),
    ('Avocado', 'Fruits', 'each', 2, 5, 'January-March', 1),
    ('Pineapples', 'Fruits', 'each', 8, 18, 'October-December', 1),
    ('Watermelon', 'Fruits', 'kg', 3, 8, 'September-November', 1),
    ('Sunflower', 'Cash Crops', 'kg', 8, 16, 'April-June', 1),
    ('Goat Meat', 'Livestock', 'kg', 35, 55, 'Year-round', 1),
    ('Honey', 'Other', 'kg', 40, 80, 'September-November', 1),
    ('Coffee', 'Other', 'kg', 25, 50, 'May-August', 1),
]

for commodity in commodities:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO commodities 
            (name, category, unit, min_price, max_price, season_start, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, commodity)
    except Exception as e:
        print(f"  ⚠️ Error adding commodity {commodity[0]}: {e}")

# =========================================================
# STEP 3: Generate market prices
# =========================================================
print("\n💰 Adding market prices...")

# Get all markets and commodities
cursor.execute("SELECT name FROM markets WHERE active = 1")
markets_list = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT name FROM commodities WHERE active = 1")
commodities_list = [row[0] for row in cursor.fetchall()]

# Price multipliers by market type
market_price_factors = {
    'Lusaka': 1.15,      # Capital city premium
    'Copperbelt': 1.10,  # Mining region premium
    'Central': 1.00,     # Baseline
    'Southern': 1.00,    # Baseline
    'Eastern': 0.90,     # Agricultural hub - lower prices
    'Western': 0.85,     # Remote - lower prices
    'North-Western': 1.08, # Mining region
    'Luapula': 0.82,     # Remote - lowest prices
    'Muchinga': 0.88,    # Remote
}

# Base prices for commodities (ZMW/kg)
base_prices = {
    # Grains
    'Maize': 6.50, 'Rice': 13.00, 'Sorghum': 5.50, 'Millet': 6.00, 'Wheat': 7.00,
    # Legumes
    'Beans': 16.00, 'Groundnuts': 21.00, 'Soybeans': 13.00, 'Cowpeas': 11.00, 'Pigeon Peas': 10.00,
    # Vegetables
    'Tomatoes': 8.50, 'Onions': 9.00, 'Cabbage': 6.50, 'Rape': 3.50, 'Okra': 10.00,
    'Eggplant': 7.50, 'Green Pepper': 14.00,
    # Tubers
    'Cassava': 5.00, 'Sweet Potatoes': 6.50, 'Irish Potatoes': 12.00,
    # Fruits
    'Bananas': 14.00, 'Oranges': 8.00, 'Mangoes': 7.00, 'Avocado': 3.50,
    'Pineapples': 12.00, 'Watermelon': 5.00,
    # Cash Crops
    'Cotton': 8.00, 'Sunflower': 12.00,
    # Livestock
    'Beef': 48.00, 'Chicken': 35.00, 'Goat Meat': 42.00, 'Eggs': 25.00, 'Milk': 14.00,
    # Other
    'Honey': 60.00, 'Coffee': 40.00,
}

price_count = 0
for market in markets_list:
    # Determine which province this market is in
    cursor.execute("SELECT province FROM markets WHERE name = ?", (market,))
    result = cursor.fetchone()
    province = result[0] if result else 'Central'
    factor = market_price_factors.get(province, 1.00)
    
    for commodity in commodities_list[:15]:  # Add for top commodities first
        base = base_prices.get(commodity, 10.00)
        price = round(base * factor + random.uniform(-0.30, 0.50), 2)
        price = max(2.00, price)  # Ensure minimum price
        
        volume = random.randint(500, 5000) if commodity in ['Maize', 'Beans', 'Groundnuts'] else random.randint(100, 1500)
        trend = random.choice(['up', 'down', 'stable'])
        
        try:
            cursor.execute("""
                INSERT INTO market_prices 
                (market, commodity, price, unit, volume, quality, source, verified, recorded_at, region, price_trend, notes)
                VALUES (?, ?, ?, 'ZMW/kg', ?, 'Grade A', 'Market Survey', 1, ?, ?, ?, ?)
            """, (market, commodity, price, volume, datetime.now().isoformat(), province, trend, f'Price for {commodity} at {market}'))
            price_count += 1
        except Exception as e:
            pass  # Skip duplicates

print(f"  ✅ Added {price_count} market prices")

# =========================================================
# STEP 4: Add more buyers
# =========================================================
print("\n🏪 Adding buyers...")

buyers = [
    ('Beans Exporters Inc', '+260976666666', 'beans@export.zm', 'Beans', 'Lusaka', 19.00, 3000, 25000, '30% deposit', 'Premium grade', 1, 4.6, 'active', datetime.now().isoformat()),
    ('Local Food Processors', '+260977777777', 'procurement@foodproc.zm', 'Beans', 'Kabwe', 17.50, 2000, 20000, 'Net 30 days', 'Clean, no stones', 1, 4.1, 'active', datetime.now().isoformat()),
    ('Groundnut Oil Mills', '+260978888888', 'oil@groundnuts.zm', 'Groundnuts', 'Lusaka', 25.00, 2000, 20000, 'Bank transfer', 'High oil content >45%', 1, 4.4, 'active', datetime.now().isoformat()),
    ('Snack Foods Ltd', '+260979999999', 'snacks@foods.zm', 'Groundnuts', 'Ndola', 24.00, 1000, 10000, 'Net 15 days', 'Roasting grade', 1, 4.0, 'active', datetime.now().isoformat()),
    ('Soybean Processors', '+260980000000', 'soy@processors.zm', 'Soybeans', 'Lusaka', 16.00, 5000, 50000, 'Letter of Credit', 'Non-GMO', 1, 4.7, 'active', datetime.now().isoformat()),
    ('Animal Feed Ltd', '+260981111111', 'feed@animals.zm', 'Soybeans', 'Kitwe', 15.00, 3000, 30000, 'Net 30 days', 'For animal feed', 1, 4.2, 'active', datetime.now().isoformat()),
    ('Cassava Processing', '+260982222222', 'cassava@process.zm', 'Cassava', 'Mansa', 7.00, 5000, 40000, 'Cash on delivery', 'Fresh, high starch', 1, 4.3, 'active', datetime.now().isoformat()),
    ('Fresh Produce Export', '+260983333333', 'export@fresh.zm', 'Sweet Potatoes', 'Lusaka', 9.00, 1000, 8000, 'Net 14 days', 'Orange-fleshed', 1, 4.1, 'active', datetime.now().isoformat()),
    ('Butchery Chain', '+260984444444', 'meat@butchery.zm', 'Beef', 'Lusaka', 60.00, 500, 5000, 'Weekly payment', 'Grade A beef', 1, 4.5, 'active', datetime.now().isoformat()),
    ('Hotel Suppliers Ltd', '+260985555555', 'supply@hotels.zm', 'Beef', 'Livingstone', 58.00, 300, 3000, 'Net 7 days', 'Premium cuts', 1, 4.4, 'active', datetime.now().isoformat()),
    ('Poultry Processors', '+260986666666', 'poultry@process.zm', 'Chicken', 'Lusaka', 42.00, 500, 5000, 'Cash on delivery', 'Broilers 1.5-2kg', 1, 4.6, 'active', datetime.now().isoformat()),
    ('Fast Food Chain', '+260987777777', 'procurement@fastfood.zm', 'Chicken', 'Ndola', 40.00, 300, 3000, 'Net 15 days', 'Fresh, not frozen', 1, 4.2, 'active', datetime.now().isoformat()),
    ('Bakery Chain', '+260988888888', 'eggs@bakery.zm', 'Eggs', 'Lusaka', 30.00, 1000, 10000, 'Weekly payment', 'Large eggs, Grade A', 1, 4.7, 'active', datetime.now().isoformat()),
    ('Hotel Group', '+260989999999', 'hotel@group.zm', 'Eggs', 'Livingstone', 29.00, 500, 5000, 'Net 14 days', 'Fresh eggs', 1, 4.3, 'active', datetime.now().isoformat()),
    ('Dairy Processors', '+260990000000', 'dairy@process.zm', 'Milk', 'Lusaka', 17.00, 2000, 20000, 'Bank transfer weekly', 'Raw milk, 3.5% fat', 1, 4.8, 'active', datetime.now().isoformat()),
    ('Cheese Factory', '+260991111111', 'cheese@factory.zm', 'Milk', 'Kabwe', 16.50, 1000, 10000, 'Net 30 days', 'High quality', 1, 4.4, 'active', datetime.now().isoformat()),
]

buyer_count = 0
for buyer in buyers:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO buyers 
            (name, phone, email, commodity, location, max_price, min_volume, max_volume, 
             payment_terms, delivery_requirements, verified, rating, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, buyer)
        buyer_count += 1
    except Exception as e:
        print(f"  ⚠️ Error adding buyer {buyer[0]}: {e}")

print(f"  ✅ Added {buyer_count} buyers")

# =========================================================
# STEP 5: Verify and commit
# =========================================================
conn.commit()

# Display summary
print("\n" + "="*50)
print("📊 IMPORT SUMMARY")
print("="*50)

cursor.execute("SELECT COUNT(*) FROM markets")
print(f"  Markets: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM commodities")
print(f"  Commodities: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM market_prices")
print(f"  Market Prices: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM buyers")
print(f"  Buyers: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM users")
print(f"  Users: {cursor.fetchone()[0]}")

print("="*50)
print("✅ Database import completed successfully!")
print("="*50)

conn.close()