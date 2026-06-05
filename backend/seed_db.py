"""
seed_db.py
Run this ONCE to load the CSV dataset into your SQLite database.

Usage:
    python seed_db.py

FarmConnect Zambia | ICT 431 | Daka Felix 202206453
"""

import os
import sys
import sqlite3
from datetime import datetime

print("=" * 60)
print("FarmConnect — Database Seeder")
print("=" * 60)

# ── Check files exist ─────────────────────────────────────────
CSV_FILE = "zambia_market_prices_2014_2024.csv"
DB_FILE  = "farm_market.db"

if not os.path.exists(CSV_FILE):
    print(f"\n❌  ERROR: '{CSV_FILE}' not found.")
    print("    Make sure the CSV is in the same folder as this script.")
    sys.exit(1)

if not os.path.exists(DB_FILE):
    print(f"\n⚠️   '{DB_FILE}' not found — run app.py first so it creates the DB,")
    print("    then re-run this script.")
    sys.exit(1)

# ── Import and seed ───────────────────────────────────────────
from zambian_data import ZambianMarketData

print(f"\n📂  Loading CSV: {CSV_FILE}")
zmd = ZambianMarketData(CSV_FILE)

if zmd.df is None or zmd.df.empty:
    print("❌  Failed to load CSV.")
    sys.exit(1)

print(f"✅  Loaded {len(zmd.df):,} rows")
print(f"    Commodities : {', '.join(zmd.get_commodities())}")
print(f"    Markets     : {', '.join(m['market'] for m in zmd.get_markets())}")
print(f"    Date range  : {zmd.df['date'].min().date()} → {zmd.df['date'].max().date()}")

print(f"\n📥  Seeding into {DB_FILE} ...")
saved = zmd.seed_database(DB_FILE)

print(f"\n✅  Done!  {saved:,} rows inserted into market_prices table.")
print("    You can now start app.py — the API will serve real data.")
print("=" * 60)