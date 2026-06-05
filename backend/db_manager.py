#!/usr/bin/env python3
"""
Database Manager for FarmConnect
Handles connections, migrations, backups, and data operations
"""

import sqlite3
import os
import json
import csv
import hashlib
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Main database manager for FarmConnect"""
    
    def __init__(self, db_path: str = "farm_market.db"):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database with schema"""
        schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                logger.info("Database schema initialized")
        else:
            logger.warning("Schema file not found, using embedded schema")
            self._create_embedded_schema()
    
    def _create_embedded_schema(self):
        """Create schema if SQL file not available"""
        with self.get_connection() as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
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
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Market prices table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market TEXT NOT NULL,
                    commodity TEXT NOT NULL,
                    price REAL NOT NULL,
                    unit TEXT DEFAULT 'ZMW/kg',
                    volume REAL,
                    quality TEXT,
                    source TEXT,
                    verified INTEGER DEFAULT 0,
                    recorded_at TEXT NOT NULL,
                    collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    region TEXT,
                    price_trend TEXT
                )
            """)
            
            # Buyers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS buyers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    commodity TEXT NOT NULL,
                    location TEXT NOT NULL,
                    max_price REAL NOT NULL,
                    min_volume REAL,
                    notes TEXT,
                    verified INTEGER DEFAULT 0,
                    rating REAL DEFAULT 4.0,
                    added_by TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # SMS tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sms_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'notification',
                    status TEXT DEFAULT 'pending',
                    provider TEXT,
                    message_id TEXT,
                    cost REAL DEFAULT 0.0,
                    sent_at TEXT,
                    queued_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sms_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    commodity TEXT NOT NULL,
                    alert_type TEXT DEFAULT 'price_change',
                    threshold REAL DEFAULT 5.0,
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Embedded database schema created")
    
    # =========================================================
    # USER MANAGEMENT
    # =========================================================
    
    def create_user(self, user_data: Dict) -> str:
        """Create a new user"""
        user_id = user_data.get('user_id') or self._generate_id('user')
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (
                    user_id, username, password_hash, name, role, phone, email,
                    location, farm_size, main_crops, business_name, license_number,
                    trading_commodities, ussd_pin, sms_alerts, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                user_data['username'],
                user_data['password_hash'],
                user_data['name'],
                user_data['role'],
                user_data.get('phone'),
                user_data.get('email'),
                user_data.get('location'),
                user_data.get('farm_size'),
                user_data.get('main_crops'),
                user_data.get('business_name'),
                user_data.get('license_number'),
                user_data.get('trading_commodities'),
                user_data.get('ussd_pin'),
                user_data.get('sms_alerts', 1),
                datetime.now().isoformat(),
                'active'
            ))
        
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND status = 'active'",
                (username,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict]:
        """Get user by phone number"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE phone = ? AND status = 'active'",
                (phone,)
            ).fetchone()
            return dict(row) if row else None
    
    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user information"""
        allowed_fields = ['name', 'phone', 'email', 'location', 'farm_size', 
                         'main_crops', 'business_name', 'trading_commodities', 
                         'sms_alerts', 'ussd_pin']
        
        set_clause = ", ".join([f"{k}=?" for k in updates if k in allowed_fields])
        if not set_clause:
            return False
        
        values = [updates[k] for k in updates if k in allowed_fields] + [user_id]
        
        with self.get_connection() as conn:
            conn.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
            return conn.total_changes > 0
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
    
    # =========================================================
    # PRICE MANAGEMENT
    # =========================================================
    
    def add_price(self, price_data: Dict) -> int:
        """Add a new market price"""
        # Calculate price trend
        trend = self._calculate_price_trend(
            price_data['commodity'],
            price_data['market'],
            price_data['price']
        )
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO market_prices (
                    market, commodity, price, unit, volume, quality,
                    source, verified, recorded_at, region, price_trend
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                price_data['market'],
                price_data['commodity'],
                price_data['price'],
                price_data.get('unit', 'ZMW/kg'),
                price_data.get('volume'),
                price_data.get('quality', 'standard'),
                price_data.get('source', 'user'),
                price_data.get('verified', 0),
                price_data.get('recorded_at', datetime.now().isoformat()),
                price_data.get('region'),
                trend
            ))
            return cursor.lastrowid
    
    def get_latest_prices(self, commodity: str = None, market: str = None, limit: int = 100) -> List[Dict]:
        """Get latest market prices"""
        query = "SELECT * FROM market_prices WHERE verified = 1"
        params = []
        
        if commodity:
            query += " AND commodity = ?"
            params.append(commodity)
        if market:
            query += " AND market LIKE ?"
            params.append(f"%{market}%")
        
        query += " ORDER BY recorded_at DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_price_history(self, commodity: str, market: str, days: int = 30) -> List[Dict]:
        """Get price history for a commodity and market"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT date(recorded_at) as date, 
                       AVG(price) as avg_price,
                       MIN(price) as min_price,
                       MAX(price) as max_price,
                       COUNT(*) as count
                FROM market_prices
                WHERE commodity = ? AND market LIKE ? AND verified = 1
                  AND recorded_at >= date('now', ?)
                GROUP BY date(recorded_at)
                ORDER BY date ASC
            """, (commodity, f"%{market}%", f'-{days} days')).fetchall()
            return [dict(row) for row in rows]
    
    def _calculate_price_trend(self, commodity: str, market: str, new_price: float) -> str:
        """Calculate price trend based on previous price"""
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT price FROM market_prices
                WHERE commodity = ? AND market LIKE ? AND verified = 1
                ORDER BY recorded_at DESC LIMIT 1
            """, (commodity, f"%{market}%")).fetchone()
            
            if not row:
                return "stable"
            
            diff = new_price - row['price']
            if diff > 0.5:
                return "up"
            elif diff < -0.5:
                return "down"
            else:
                return "stable"
    
    # =========================================================
    # BUYER MANAGEMENT
    # =========================================================
    
    def add_buyer(self, buyer_data: Dict) -> int:
        """Add a new buyer"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO buyers (
                    name, phone, commodity, location, max_price, min_volume,
                    notes, verified, rating, added_by, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                buyer_data['name'],
                buyer_data['phone'],
                buyer_data['commodity'],
                buyer_data['location'],
                buyer_data['max_price'],
                buyer_data.get('min_volume'),
                buyer_data.get('notes'),
                buyer_data.get('verified', 0),
                buyer_data.get('rating', 4.0),
                buyer_data.get('added_by'),
                datetime.now().isoformat(),
                'active'
            ))
            return cursor.lastrowid
    
    def get_buyers(self, commodity: str = None, verified_only: bool = True, limit: int = 50) -> List[Dict]:
        """Get buyers matching criteria"""
        query = "SELECT * FROM buyers WHERE status = 'active'"
        params = []
        
        if verified_only:
            query += " AND verified = 1"
        if commodity:
            query += " AND commodity = ?"
            params.append(commodity)
        
        query += " ORDER BY rating DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    # =========================================================
    # SMS MANAGEMENT
    # =========================================================
    
    def log_sms(self, phone: str, message: str, msg_type: str, status: str, 
                message_id: str = None, error: str = None) -> int:
        """Log an SMS message"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO sms_history (
                    phone, message, type, status, message_id, 
                    error_message, sent_at, queued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                phone, message[:500], msg_type, status, message_id,
                error, datetime.now().isoformat() if status in ('sent', 'delivered') else None,
                datetime.now().isoformat()
            ))
            return cursor.lastrowid
    
    def add_subscription(self, user_id: str, commodity: str, alert_type: str = 'price_change', 
                         threshold: float = 5.0) -> bool:
        """Add SMS subscription for a user"""
        with self.get_connection() as conn:
            # Check if already subscribed
            existing = conn.execute("""
                SELECT id FROM sms_subscriptions 
                WHERE user_id = ? AND commodity = ? AND alert_type = ? AND active = 1
            """, (user_id, commodity, alert_type)).fetchone()
            
            if existing:
                return False
            
            conn.execute("""
                INSERT INTO sms_subscriptions (user_id, commodity, alert_type, threshold)
                VALUES (?, ?, ?, ?)
            """, (user_id, commodity, alert_type, threshold))
            return True
    
    def get_subscribers_for_alert(self, commodity: str, price_change_pct: float) -> List[Dict]:
        """Get subscribers who should receive an alert based on price change"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT s.user_id, s.threshold, u.phone, u.name, u.sms_alerts
                FROM sms_subscriptions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.commodity = ? 
                  AND s.active = 1 
                  AND u.status = 'active'
                  AND u.sms_alerts = 1
                  AND u.phone IS NOT NULL
                  AND s.threshold <= ?
            """, (commodity, price_change_pct)).fetchall()
            return [dict(row) for row in rows]
    
    # =========================================================
    # USSD MANAGEMENT
    # =========================================================
    
    def save_ussd_session(self, session_id: str, phone_number: str, current_menu: str, 
                          menu_data: Dict = None) -> bool:
        """Save or update USSD session"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ussd_sessions 
                (session_id, phone_number, current_menu, menu_data, last_activity, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id, phone_number, current_menu,
                json.dumps(menu_data) if menu_data else None,
                datetime.now().isoformat(), 'active'
            ))
            return True
    
    def get_ussd_session(self, session_id: str) -> Optional[Dict]:
        """Get USSD session by ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM ussd_sessions WHERE session_id = ? AND status = 'active'",
                (session_id,)
            ).fetchone()
            
            if row:
                result = dict(row)
                if result.get('menu_data'):
                    result['menu_data'] = json.loads(result['menu_data'])
                return result
            return None
    
    def log_ussd_interaction(self, session_id: str, phone_number: str, 
                             input_text: str, response_text: str, menu_name: str = None):
        """Log USSD interaction"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO ussd_logs (session_id, phone_number, input_text, response_text, menu_name)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, phone_number, input_text, response_text[:500], menu_name))
    
    # =========================================================
    # FORECAST MANAGEMENT
    # =========================================================
    
    def cache_forecast(self, commodity: str, market: str, days: int, 
                       forecast_data: List[Dict], recommendations: Dict = None,
                       model_used: str = None, accuracy: float = None) -> bool:
        """Cache forecast results"""
        expires_at = datetime.now() + timedelta(hours=24)
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO forecast_cache 
                (commodity, market, forecast_days, forecast_data, recommendations,
                 generated_at, expires_at, model_used, accuracy_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                commodity, market, days,
                json.dumps(forecast_data),
                json.dumps(recommendations) if recommendations else None,
                datetime.now().isoformat(),
                expires_at.isoformat(),
                model_used,
                accuracy
            ))
            return True
    
    def get_cached_forecast(self, commodity: str, market: str, days: int) -> Optional[Dict]:
        """Get cached forecast if still valid"""
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM forecast_cache
                WHERE commodity = ? AND market = ? AND forecast_days = ?
                  AND expires_at > datetime('now')
                ORDER BY generated_at DESC LIMIT 1
            """, (commodity, market, days)).fetchone()
            
            if row:
                result = dict(row)
                result['forecast_data'] = json.loads(result['forecast_data'])
                if result.get('recommendations'):
                    result['recommendations'] = json.loads(result['recommendations'])
                return result
            return None
    
    # =========================================================
    # ANALYTICS & STATISTICS
    # =========================================================
    
    def log_activity(self, user: str, action: str, details: str = None, ip_address: str = None):
        """Log user activity"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO activity_logs (user, action, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user, action, details, ip_address, datetime.now().isoformat()))
    
    def log_api_usage(self, endpoint: str, user_id: str, method: str, 
                      status_code: int, response_time_ms: int):
        """Log API usage for analytics"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO api_usage (endpoint, user_id, method, status_code, response_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, (endpoint, user_id, method, status_code, response_time_ms))
    
    def get_dashboard_stats(self) -> Dict:
        """Get statistics for admin dashboard"""
        stats = {}
        
        with self.get_connection() as conn:
            # User stats
            stats['users'] = dict(conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN role = 'farmer' THEN 1 ELSE 0 END) as farmers,
                    SUM(CASE WHEN role = 'trader' THEN 1 ELSE 0 END) as traders,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
                FROM users
            """).fetchone())
            
            # Price stats
            stats['prices'] = dict(conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified,
                    COUNT(DISTINCT commodity) as commodities,
                    COUNT(DISTINCT market) as markets
                FROM market_prices
            """).fetchone())
            
            # Today's prices
            stats['prices_today'] = conn.execute("""
                SELECT COUNT(*) as count
                FROM market_prices
                WHERE date(recorded_at) = date('now')
            """).fetchone()[0]
            
            # Buyer stats
            stats['buyers'] = conn.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified
                FROM buyers WHERE status = 'active'
            """).fetchone()[0]
            
            # SMS stats
            stats['sms'] = dict(conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM sms_history
            """).fetchone())
            
            # Subscriptions
            stats['subscriptions'] = conn.execute("""
                SELECT COUNT(*) as count FROM sms_subscriptions WHERE active = 1
            """).fetchone()[0]
        
        return stats
    
    # =========================================================
    # UTILITIES
    # =========================================================
    
    def _generate_id(self, prefix: str = 'user') -> str:
        """Generate a unique ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
    
    def backup_database(self, backup_dir: str = "backups") -> str:
        """Create a database backup"""
        import shutil
        
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"farmconnect_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        
        return backup_path
    
    def export_to_csv(self, table_name: str, output_path: str = None) -> str:
        """Export a table to CSV"""
        if not output_path:
            output_path = f"export_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                raise ValueError(f"No data in table {table_name}")
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([description[0] for description in cursor.description])
                writer.writerows(rows)
        
        logger.info(f"Exported {table_name} to {output_path}")
        return output_path
    
    def cleanup_expired_sessions(self):
        """Clean up expired USSD sessions"""
        with self.get_connection() as conn:
            # Sessions older than 1 hour
            conn.execute("""
                UPDATE ussd_sessions SET status = 'expired'
                WHERE status = 'active' 
                  AND last_activity < datetime('now', '-1 hour')
            """)
            
            # Clean up old forecast cache (older than 7 days)
            conn.execute("""
                DELETE FROM forecast_cache
                WHERE expires_at < datetime('now', '-7 days')
            """)
            
            logger.info("Cleaned up expired sessions and cache")


# Singleton instance
_db_manager = None

def get_db_manager(db_path: str = "farm_market.db") -> DatabaseManager:
    """Get the database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager