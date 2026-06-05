"""
zambian_data.py
FarmConnect Zambia — Real Market Data Module
Loads the 2014-2024 dataset and serves it to app.py

Place this file in the same folder as app.py
Place zambia_market_prices_2014_2024.csv in the same folder (or set DATA_PATH)

Student: Daka Felix (202206453) | Mulungushi University ICT 431
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ── Path to your CSV dataset ──────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "zambia_market_prices_2014_2024.csv")

DATABASE = "farm_market.db"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ZambianMarketData:
    """
    Loads the real Zambian market price dataset and exposes helper methods
    used by app.py for API responses, forecasting, and the USSD service.
    """

    def __init__(self, csv_path: str = DATA_PATH):
        self.csv_path = csv_path
        self.df = None
        self._load()

    # ── Load & cache ──────────────────────────────────────────────────────────

    def _load(self):
        """Load CSV into memory once."""
        if not os.path.exists(self.csv_path):
            logger.warning(f"⚠️  Dataset not found at {self.csv_path}")
            self.df = pd.DataFrame()
            return

        self.df = pd.read_csv(self.csv_path, parse_dates=["date"])
        logger.info(f"✅ Loaded {len(self.df):,} rows from {self.csv_path}")

    # ── Seed SQLite DB ────────────────────────────────────────────────────────

    def seed_database(self, db_path: str = DATABASE, limit: int = None):
        """
        Insert dataset rows into the market_prices table that app.py already
        creates.  Safe to call multiple times – skips if data already exists.

        Args:
            db_path:  path to farm_market.db
            limit:    optional row cap (e.g. 500 for quick testing)
        """
        if self.df is None or self.df.empty:
            logger.warning("No data to seed.")
            return 0

        conn = sqlite3.connect(db_path)
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM market_prices")
        existing = cur.fetchone()[0]
        if existing > 100:
            logger.info(f"DB already has {existing} price rows – skipping seed.")
            conn.close()
            return existing

        data = self.df.copy()
        if limit:
            data = data.head(limit)

        saved = 0
        for _, row in data.iterrows():
            try:
                cur.execute("""
                    INSERT INTO market_prices
                        (market, commodity, price, unit, volume, quality,
                         source, verified, recorded_at, region,
                         market_lat, market_lon, price_trend)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    row["market"],
                    row["commodity"],
                    round(float(row["price_zmw_kg"]), 2),
                    "ZMW/kg",
                    int(row["volume_kg"]),
                    row["quality"],
                    row["source"],
                    int(row["verified"]),
                    row["date"].strftime("%Y-%m-%d"),
                    row["region"],
                    float(row["lat"]),
                    float(row["lon"]),
                    row["price_trend"],
                ))
                saved += 1
            except Exception as e:
                logger.debug(f"Row insert error: {e}")

        conn.commit()
        conn.close()
        logger.info(f"✅ Seeded {saved:,} rows into market_prices.")
        return saved

    # ── Public helpers used by app.py ─────────────────────────────────────────

    def fetch_all_sources(self) -> list:
        """
        Called by the scheduled task in app.py.
        Returns the most recent month's data as a list of dicts.
        """
        if self.df is None or self.df.empty:
            return []

        latest_date = self.df["date"].max()
        recent = self.df[self.df["date"] == latest_date]

        records = []
        for _, row in recent.iterrows():
            records.append({
                "market":      row["market"],
                "commodity":   row["commodity"],
                "price":       round(float(row["price_zmw_kg"]), 2),
                "unit":        "ZMW/kg",
                "volume":      int(row["volume_kg"]),
                "quality":     row["quality"],
                "source":      row["source"],
                "verified":    bool(row["verified"]),
                "recorded_at": row["date"].strftime("%Y-%m-%d"),
                "region":      row["region"],
                "price_trend": row["price_trend"],
            })
        return records

    def get_current_prices(self, commodity: str = None,
                           market: str = None) -> list:
        """Latest available price for every commodity/market combination."""
        if self.df is None or self.df.empty:
            return []

        latest_date = self.df["date"].max()
        data = self.df[self.df["date"] == latest_date].copy()

        if commodity and commodity.lower() != "all":
            data = data[data["commodity"].str.lower() == commodity.lower()]
        if market and market.lower() != "all":
            data = data[data["market"].str.lower() == market.lower()]

        return data.to_dict("records")

    def get_price_history(self, commodity: str, market: str,
                          months: int = 24) -> pd.DataFrame:
        """
        Time-series of monthly prices for a commodity/market pair.
        Used by the forecasting module.
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        mask = (
            (self.df["commodity"].str.lower() == commodity.lower()) &
            (self.df["market"].str.lower() == market.lower())
        )
        data = (self.df[mask]
                .sort_values("date")
                .tail(months)
                [["date", "price_zmw_kg", "volume_kg", "rainfall_index",
                  "inflation_index", "fra_active", "season",
                  "price_lag1", "price_lag2", "price_lag3", "rolling_avg_3m"]])
        data = data.rename(columns={"price_zmw_kg": "price"})
        return data

    def get_markets(self) -> list:
        """List of unique markets with coordinates."""
        if self.df is None or self.df.empty:
            return []
        return (self.df[["market", "region", "market_type", "lat", "lon"]]
                .drop_duplicates()
                .to_dict("records"))

    def get_commodities(self) -> list:
        """List of commodity names in the dataset."""
        if self.df is None or self.df.empty:
            return []
        return sorted(self.df["commodity"].unique().tolist())

    def get_seasonal_pattern(self, commodity: str) -> dict:
        """
        Average price index by month (1-12) for a commodity.
        Returns dict like {1: 1.18, 2: 1.22, ...}
        """
        if self.df is None or self.df.empty:
            return {}

        data = self.df[self.df["commodity"].str.lower() == commodity.lower()]
        if data.empty:
            return {}

        monthly = data.groupby("month")["price_zmw_kg"].mean()
        overall = data["price_zmw_kg"].mean()
        return {int(m): round(float(p / overall), 3)
                for m, p in monthly.items()}

    def get_shock_events(self) -> list:
        """Return rows that have a documented shock event."""
        if self.df is None or self.df.empty:
            return []
        shocks = self.df[self.df["shock_event"] != "none"]
        return (shocks[["date", "commodity", "market",
                         "price_zmw_kg", "shock_event"]]
                .drop_duplicates(subset=["date", "commodity", "shock_event"])
                .to_dict("records"))

    def get_summary_stats(self) -> dict:
        """Dashboard statistics for the /api/status endpoint."""
        if self.df is None or self.df.empty:
            return {}
        return {
            "total_records":    len(self.df),
            "date_range":       f"{self.df['date'].min().date()} to {self.df['date'].max().date()}",
            "commodities":      self.get_commodities(),
            "markets":          sorted(self.df["market"].unique().tolist()),
            "latest_date":      str(self.df["date"].max().date()),
            "avg_price_latest": round(
                float(self.df[self.df["date"] == self.df["date"].max()]
                      ["price_zmw_kg"].mean()), 2
            ),
        }