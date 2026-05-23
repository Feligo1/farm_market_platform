#!/usr/bin/env python3
"""
FarmConnect - Backend API

Flask backend for live market prices, forecasts, buyers, sellers, news,
profiles, SMS subscriptions, admin tools, and the static web frontend.
"""

import os
import sys
import uuid
import time
import random
import logging
import threading
import webbrowser
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps

import jwt
import numpy as np
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_caching import Cache
from flask_cors import CORS
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from sklearn.linear_model import LinearRegression
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

try:
    import africastalking
except ImportError:
    africastalking = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "news"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "profiles"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "farmconnect.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="frontend", static_url_path="")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config["JWT_SECRET"] = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp", "csv", "xlsx", "xls"}

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

try:
    cache = Cache(
        app,
        config={
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "CACHE_DEFAULT_TIMEOUT": 60,
        },
    )
    with app.app_context():
        cache.set("healthcheck", "ok", timeout=5)
    print("[OK] Redis cache enabled")
except Exception:
    print("[WARNING] Redis not available - using in-memory cache")
    cache = Cache(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 60})
cache.init_app(app)

try:
    from flask_socketio import SocketIO

    socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60)
    logger.info("WebSocket initialized")
except ImportError:
    socketio = None


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "ep-bitter-cell-alftjnnc-pooler.c-3.eu-central-1.aws.neon.tech"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "neondb"),
    "user": os.getenv("DB_USER", "neondb_owner"),
    "password": os.getenv("DB_PASSWORD", ""),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
    "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "15")),
}

db_pool = None


def init_db_pool():
    global db_pool
    try:
        db_pool = SimpleConnectionPool(1, 20, **DB_CONFIG)
        print("[OK] PostgreSQL connection pool created")
        return True
    except Exception as exc:
        print(f"[ERROR] PostgreSQL connection failed: {exc}")
        return False


@contextmanager
def get_db_cursor(commit=True):
    conn = None
    try:
        conn = db_pool.getconn() if db_pool else psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SET statement_timeout = %s", (int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "30000")),))
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    finally:
        if conn and db_pool:
            db_pool.putconn(conn)
        elif conn:
            conn.close()


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def clean_row(row):
    return {key: clean_value(value) for key, value in dict(row).items()}


def clean_rows(rows):
    return [clean_row(row) for row in rows]


def table_columns(table_name):
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
        """, (table_name,))
        return {row["column_name"] for row in cursor.fetchall()}


def find_commodity_id(name):
    if not name:
        return None
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT id FROM commodities WHERE name = %s LIMIT 1", (name,))
        row = cursor.fetchone()
        return row["id"] if row else None


def get_json():
    return request.get_json(silent=True) or {}


def coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def save_uploaded_file(file, subfolder="news"):
    if not file or not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    filepath = os.path.join(upload_path, unique_name)
    file.save(filepath)
    return f"/static/uploads/{subfolder}/{unique_name}"


def generate_token(user):
    payload = {
        "user_id": str(user["id"]),
        "username": user["username"],
        "name": f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip(),
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, app.config["JWT_SECRET"], algorithm="HS256")


def verify_token(token):
    try:
        return jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
    except Exception:
        return None


def current_user_payload(optional=False):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return None if optional else False
    return verify_token(token)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = current_user_payload()
        if payload is False:
            return jsonify({"error": "Token required"}), 401
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.user = payload
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = current_user_payload()
        if payload is False:
            return jsonify({"error": "Token required"}), 401
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        if payload.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        request.user = payload
        return f(*args, **kwargs)

    return decorated


def create_schema():
    with get_db_cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        cursor.execute("DO $$ BEGIN CREATE TYPE user_role AS ENUM ('admin', 'farmer', 'buyer', 'trader'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE,
                password_hash TEXT NOT NULL,
                phone VARCHAR(20) UNIQUE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                profile_picture_url TEXT,
                role user_role DEFAULT 'farmer',
                is_active BOOLEAN DEFAULT true,
                is_email_verified BOOLEAN DEFAULT false,
                is_phone_verified BOOLEAN DEFAULT false,
                location TEXT,
                province VARCHAR(100),
                district VARCHAR(100),
                latitude DECIMAL(10,8),
                longitude DECIMAL(11,8),
                farm_size_hectares DECIMAL(10,2),
                main_crops TEXT[],
                years_farming INTEGER,
                business_name VARCHAR(200),
                business_registration_number VARCHAR(100),
                tax_id VARCHAR(100),
                preferred_language VARCHAR(10) DEFAULT 'en',
                sms_alerts_enabled BOOLEAN DEFAULT true,
                email_alerts_enabled BOOLEAN DEFAULT true,
                notification_frequency VARCHAR(20) DEFAULT 'daily',
                ussd_pin_hash VARCHAR(255),
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commodities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(50),
                sub_category VARCHAR(50),
                unit_of_measure VARCHAR(20) DEFAULT 'kg',
                icon_emoji VARCHAR(10),
                icon_url TEXT,
                color_code VARCHAR(7),
                typical_min_price DECIMAL(10,2),
                typical_max_price DECIMAL(10,2),
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS markets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                market_code VARCHAR(20) UNIQUE,
                province VARCHAR(100) NOT NULL,
                district VARCHAR(100) NOT NULL,
                town VARCHAR(100),
                latitude DECIMAL(10,8),
                longitude DECIMAL(11,8),
                address TEXT,
                market_days VARCHAR(100),
                operating_hours VARCHAR(100),
                contact_phone VARCHAR(20),
                has_weighbridge BOOLEAN DEFAULT false,
                has_storage BOOLEAN DEFAULT false,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id BIGSERIAL PRIMARY KEY,
                commodity_id INTEGER REFERENCES commodities(id),
                market_id INTEGER REFERENCES markets(id),
                user_id UUID REFERENCES users(id),
                price DECIMAL(12,2) NOT NULL,
                unit VARCHAR(20) DEFAULT 'kg',
                volume DECIMAL(12,2),
                quality VARCHAR(50),
                source_type VARCHAR(50),
                is_verified BOOLEAN DEFAULT false,
                trend VARCHAR(20),
                price_date DATE NOT NULL DEFAULT CURRENT_DATE,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_prices (
                id SERIAL PRIMARY KEY,
                commodity_id INTEGER REFERENCES commodities(id),
                market_id INTEGER REFERENCES markets(id),
                current_price DECIMAL(12,2) NOT NULL,
                price_7d DECIMAL(12,2),
                price_14d DECIMAL(12,2),
                price_30d DECIMAL(12,2),
                trend VARCHAR(20),
                recommendation VARCHAR(50),
                confidence DECIMAL(5,2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(commodity_id, market_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buyers (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                business_name VARCHAR(200),
                contact_person VARCHAR(200),
                contact_phone VARCHAR(20),
                contact_email VARCHAR(255),
                commodity VARCHAR(100),
                location TEXT,
                max_price DECIMAL(12,2),
                min_volume DECIMAL(12,2),
                notes TEXT,
                is_verified BOOLEAN DEFAULT false,
                rating DECIMAL(3,2) DEFAULT 0,
                added_by VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                farm_name VARCHAR(200),
                contact_person VARCHAR(200),
                contact_phone VARCHAR(20),
                contact_email VARCHAR(255),
                commodity VARCHAR(100),
                available_volume DECIMAL(12,2),
                price_per_kg DECIMAL(12,2),
                location TEXT,
                is_verified BOOLEAN DEFAULT false,
                rating DECIMAL(3,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                from_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                subject VARCHAR(200),
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                summary VARCHAR(500),
                image_url TEXT,
                category VARCHAR(50),
                author_id UUID REFERENCES users(id) ON DELETE SET NULL,
                author_name VARCHAR(200),
                status VARCHAR(20) DEFAULT 'published',
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_likes (
                id SERIAL PRIMARY KEY,
                news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(news_id, user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_comments (
                id SERIAL PRIMARY KEY,
                news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                commodity VARCHAR(100) NOT NULL,
                market VARCHAR(200),
                alert_type VARCHAR(30) DEFAULT 'price_change',
                threshold DECIMAL(8,2) DEFAULT 5.0,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms_history (
                id SERIAL PRIMARY KEY,
                phone VARCHAR(20),
                message TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'notification',
                status VARCHAR(30) DEFAULT 'pending',
                provider VARCHAR(50),
                sent_at TIMESTAMP,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        """)



def seed_defaults():
    commodities = [
        ("Maize", "Cereal", "kg", "MZ", "#f4c542", 5.0, 9.0),
        ("Tomatoes", "Vegetable", "kg", "TM", "#e84d4d", 6.0, 15.0),
        ("Beans", "Legume", "kg", "BN", "#8b5e3c", 10.0, 20.0),
        ("Groundnuts", "Legume", "kg", "GN", "#c69249", 15.0, 28.0),
        ("Rice", "Cereal", "kg", "RC", "#d9d2bd", 8.0, 15.0),
        ("Soybeans", "Legume", "kg", "SB", "#9bbf5a", 10.0, 20.0),
        ("Sweet Potatoes", "Root Crop", "kg", "SP", "#d8793f", 3.0, 8.0),
        ("Cassava", "Root Crop", "kg", "CS", "#b99b62", 3.0, 7.0),
        ("Onions", "Vegetable", "kg", "ON", "#b25aa3", 8.0, 18.0),
        ("Cabbage", "Vegetable", "kg", "CB", "#61a85f", 3.0, 8.0),
    ]
    markets = [
        ("Lusaka", "LUS", "Lusaka", "Lusaka", "Lusaka"),
        ("Kitwe", "KIT", "Copperbelt", "Kitwe", "Kitwe"),
        ("Ndola", "NDO", "Copperbelt", "Ndola", "Ndola"),
        ("Livingstone", "LIV", "Southern", "Livingstone", "Livingstone"),
        ("Chipata", "CHI", "Eastern", "Chipata", "Chipata"),
        ("Kabwe", "KAB", "Central", "Kabwe", "Kabwe"),
        ("Solwezi", "SOL", "North-Western", "Solwezi", "Solwezi"),
        ("Mongu", "MON", "Western", "Mongu", "Mongu"),
    ]

    with get_db_cursor() as cursor:
        admin_password = generate_password_hash(os.getenv("DEFAULT_ADMIN_PASSWORD", "5645"))
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, phone, first_name, last_name, role, is_active, is_email_verified, is_phone_verified)
            VALUES (%s, %s, %s, %s, %s, %s, 'admin', true, true, true)
            ON CONFLICT (username) DO NOTHING
        """, (os.getenv("DEFAULT_ADMIN_USERNAME", "Felix"), "felix@farmconnect.zm", admin_password, "+260971234560", "Felix", "Admin"))

        for name, category, unit, icon, color, min_price, max_price in commodities:
            cursor.execute("""
                INSERT INTO commodities (name, category, unit_of_measure, icon_emoji, color_code, typical_min_price, typical_max_price, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                ON CONFLICT (name) DO NOTHING
            """, (name, category, unit, icon, color, min_price, max_price))

        for name, code, province, district, town in markets:
            cursor.execute("""
                INSERT INTO markets (name, market_code, province, district, town, is_active)
                VALUES (%s, %s, %s, %s, %s, true)
                ON CONFLICT (market_code) DO NOTHING
            """, (name, code, province, district, town))


def ensure_live_prices():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM live_prices")
        if cursor.fetchone()["count"] > 0:
            return
        cursor.execute("""
            INSERT INTO live_prices (
                commodity_id, market_id, current_price, price_7d, price_14d, price_30d,
                trend, recommendation, confidence, updated_at
            )
            SELECT
                c.id,
                m.id,
                ROUND(((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2)::numeric, 2),
                ROUND((((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2) * 1.01)::numeric, 2),
                ROUND((((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2) * 1.02)::numeric, 2),
                ROUND((((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2) * 1.03)::numeric, 2),
                'stable',
                'Monitor',
                60,
                CURRENT_TIMESTAMP
            FROM commodities c
            CROSS JOIN markets m
            WHERE c.is_active = true AND m.is_active = true
            ON CONFLICT (commodity_id, market_id) DO NOTHING
        """)


def init_database():
    create_schema()
    seed_defaults()
    print("[OK] Database schema ready")


def compute_advanced_trend(historical_prices):
    if len(historical_prices) < 5:
        return 0.0005
    x_values = np.arange(len(historical_prices)).reshape(-1, 1)
    y_values = np.array(historical_prices)
    model = LinearRegression().fit(x_values, y_values)
    avg_price = np.mean(historical_prices)
    return 0.0 if avg_price == 0 else float(model.coef_[0] / avg_price)


def generate_forecast_for_commodity_market(commodity_id, market_id, days=30):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT price FROM price_history
            WHERE commodity_id = %s AND market_id = %s AND is_verified = true
            ORDER BY price_date ASC, recorded_at ASC
        """, (commodity_id, market_id))
        rows = cursor.fetchall()

        if rows:
            historical = [float(row["price"]) for row in rows]
            current_price = historical[-1]
            daily_trend = compute_advanced_trend(historical)
        else:
            cursor.execute("SELECT typical_min_price, typical_max_price FROM commodities WHERE id = %s", (commodity_id,))
            commodity = cursor.fetchone()
            min_price = float(commodity["typical_min_price"] or 5.0) if commodity else 5.0
            max_price = float(commodity["typical_max_price"] or 10.0) if commodity else 10.0
            current_price = round((min_price + max_price) / 2, 2)
            daily_trend = 0.0005
            historical = [current_price]

        seasonal_map = {1: 0.98, 2: 1.00, 3: 1.02, 4: 1.04, 5: 1.05, 6: 1.10, 7: 1.12, 8: 1.08, 9: 1.03, 10: 1.00, 11: 0.97, 12: 0.95}
        seasonal_effect = (seasonal_map.get(datetime.now().month, 1.0) - 1.0) * 0.25

        forecast_prices = []
        predicted = current_price
        for day_num in range(1, min(days, 30) + 1):
            change = daily_trend + seasonal_effect / 30 + random.uniform(-0.003, 0.003)
            predicted = max(1.0, predicted * (1 + change))
            forecast_prices.append(predicted)

        price_7d = forecast_prices[6] if len(forecast_prices) >= 7 else None
        price_14d = forecast_prices[13] if len(forecast_prices) >= 14 else None
        price_30d = forecast_prices[29] if len(forecast_prices) >= 30 else None

        if daily_trend > 0.001:
            trend = "up"
            recommendation = "Hold"
        elif daily_trend < -0.001:
            trend = "down"
            recommendation = "Sell"
        else:
            trend = "stable"
            recommendation = "Monitor"

        confidence = min(95, max(55, 60 + len(historical) * 2))
        return {
            "current_price": round(current_price, 2),
            "price_7d": round(price_7d, 2) if price_7d else None,
            "price_14d": round(price_14d, 2) if price_14d else None,
            "price_30d": round(price_30d, 2) if price_30d else None,
            "trend": trend,
            "recommendation": recommendation,
            "confidence": confidence,
        }


def retrain_forecast_model():
    logger.info("Retraining forecast model")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id FROM commodities WHERE is_active = true")
        commodities = cursor.fetchall()
        cursor.execute("SELECT id FROM markets WHERE is_active = true")
        markets = cursor.fetchall()

    total = 0
    with get_db_cursor() as cursor:
        for commodity in commodities:
            for market in markets:
                forecast = generate_forecast_for_commodity_market(commodity["id"], market["id"])
                cursor.execute("""
                    INSERT INTO live_prices (commodity_id, market_id, current_price, price_7d, price_14d, price_30d, trend, recommendation, confidence, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (commodity_id, market_id) DO UPDATE SET
                        current_price = EXCLUDED.current_price,
                        price_7d = EXCLUDED.price_7d,
                        price_14d = EXCLUDED.price_14d,
                        price_30d = EXCLUDED.price_30d,
                        trend = EXCLUDED.trend,
                        recommendation = EXCLUDED.recommendation,
                        confidence = EXCLUDED.confidence,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    commodity["id"], market["id"], forecast["current_price"], forecast["price_7d"],
                    forecast["price_14d"], forecast["price_30d"], forecast["trend"],
                    forecast["recommendation"], forecast["confidence"],
                ))
                total += 1
    cache.clear()
    logger.info("Retrained model and updated %s live price records", total)


def update_live_prices():
    retrain_forecast_model()


@app.route("/api/register", methods=["POST"])
def register():
    data = get_json()
    for field in ["username", "password", "name", "phone"]:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    full_name = data["name"].strip()
    first_name, _, last_name = full_name.partition(" ")
    role = data.get("role", "farmer")
    if role not in ["farmer", "buyer", "trader"]:
        role = "farmer"

    try:
        with get_db_cursor() as cursor:
            main_crops = data.get("main_crops")
            if isinstance(main_crops, str):
                main_crops = [crop.strip() for crop in main_crops.split(",") if crop.strip()]
            cursor.execute("""
                INSERT INTO users (
                    username, email, password_hash, phone, first_name, last_name, role,
                    location, farm_size_hectares, main_crops, business_name, is_active, ussd_pin_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, %s)
                RETURNING id, username, email, first_name, last_name, role, phone, profile_picture_url
            """, (
                data["username"], data.get("email") or None, generate_password_hash(data["password"]),
                data["phone"], first_name, last_name, role, data.get("location") or None,
                data.get("farm_size_hectares") or data.get("farm_size") or None,
                main_crops, data.get("business_name") or None, str(random.randint(1000, 9999)),
            ))
            user = cursor.fetchone()
        return jsonify({"success": True, "message": "Registration successful", "token": generate_token(user), "user": user_response(user)}), 201
    except psycopg2.IntegrityError as exc:
        message = str(exc).lower()
        if "username" in message:
            return jsonify({"error": "Username already exists"}), 400
        if "phone" in message:
            return jsonify({"error": "Phone number already registered"}), 400
        if "email" in message:
            return jsonify({"error": "Email already registered"}), 400
        return jsonify({"error": "Registration failed"}), 400
    except Exception as exc:
        logger.exception("Registration error")
        return jsonify({"error": str(exc)}), 500


def user_response(user):
    return {
        "id": str(user["id"]),
        "username": user["username"],
        "name": f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip(),
        "role": user["role"],
        "phone": user.get("phone") or "",
        "email": user.get("email") or "",
        "profile_picture": user.get("profile_picture_url") or "",
    }


@app.route("/api/login", methods=["POST"])
def login():
    data = get_json()
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, first_name, last_name, role, phone, profile_picture_url, password_hash, is_active
                FROM users WHERE username = %s
            """, (data["username"],))
            user = cursor.fetchone()
            if not user or not user["is_active"] or not check_password_hash(user["password_hash"], data["password"]):
                return jsonify({"error": "Invalid credentials"}), 401
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user["id"],))

        return jsonify({"success": True, "message": "Login successful", "token": generate_token(user), "user": user_response(user)})
    except Exception:
        logger.exception("Login error")
        return jsonify({"error": "Login failed"}), 500


@app.route("/api/prices", methods=["GET"])
@cache.cached(timeout=30, query_string=True)
def get_prices():
    commodity = request.args.get("commodity")
    market = request.args.get("market")
    limit = min(int(request.args.get("limit", 200)), 1000)
    try:
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT lp.id, c.name AS commodity_name, c.name AS commodity, c.icon_emoji,
                       m.name AS market_name, m.name AS market, m.province,
                       lp.current_price AS price, 'ZMW/kg' AS unit, lp.trend,
                       lp.updated_at AS last_updated, lp.confidence, lp.recommendation
                FROM live_prices lp
                JOIN commodities c ON lp.commodity_id = c.id
                JOIN markets m ON lp.market_id = m.id
                WHERE lp.current_price IS NOT NULL
            """
            params = []
            if commodity:
                query += " AND c.name = %s"
                params.append(commodity)
            if market:
                query += " AND m.name = %s"
                params.append(market)
            query += " ORDER BY c.name, m.name LIMIT %s"
            params.append(limit)
            cursor.execute(query, params)
            prices = clean_rows(cursor.fetchall())
            if not prices:
                fallback_query = """
                    SELECT c.id, c.name AS commodity_name, c.name AS commodity, c.icon_emoji,
                           m.name AS market_name, m.name AS market, m.province,
                           ROUND(((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2)::numeric, 2) AS price,
                           'ZMW/kg' AS unit, 'stable' AS trend, CURRENT_TIMESTAMP AS last_updated,
                           60 AS confidence, 'Monitor' AS recommendation
                    FROM commodities c
                    CROSS JOIN markets m
                    WHERE c.is_active = true AND m.is_active = true
                """
                fallback_params = []
                if commodity:
                    fallback_query += " AND c.name = %s"
                    fallback_params.append(commodity)
                if market:
                    fallback_query += " AND m.name = %s"
                    fallback_params.append(market)
                fallback_query += " ORDER BY c.name, m.name LIMIT %s"
                fallback_params.append(limit)
                cursor.execute(fallback_query, fallback_params)
                prices = clean_rows(cursor.fetchall())
        return jsonify({"success": True, "prices": prices, "count": len(prices)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "prices": []}), 500


@app.route("/api/prices/real", methods=["GET"])
def get_real_prices():
    limit = min(int(request.args.get("limit", 100)), 1000)
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT ph.id, c.name AS commodity, m.name AS market, ph.price, ph.unit, ph.volume,
                       ph.quality, ph.is_verified, ph.trend, ph.price_date, ph.recorded_at, ph.notes
                FROM price_history ph
                JOIN commodities c ON ph.commodity_id = c.id
                JOIN markets m ON ph.market_id = m.id
                ORDER BY ph.recorded_at DESC LIMIT %s
            """, (limit,))
            prices = clean_rows(cursor.fetchall())
        return jsonify({"success": True, "prices": prices, "count": len(prices)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "prices": []}), 500


@app.route("/api/prices/history", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def get_price_history():
    commodity = request.args.get("commodity")
    market = request.args.get("market")
    days = min(int(request.args.get("days", 30)), 365)
    if not commodity:
        return jsonify({"error": "commodity parameter required"}), 400
    try:
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT ph.price, ph.price_date, ph.trend, m.name AS market_name, m.name AS market
                FROM price_history ph
                JOIN commodities c ON ph.commodity_id = c.id
                JOIN markets m ON ph.market_id = m.id
                WHERE c.name = %s AND ph.is_verified = true
                  AND ph.price_date >= CURRENT_DATE - (%s * INTERVAL '1 day')
            """
            params = [commodity, days]
            if market:
                query += " AND m.name = %s"
                params.append(market)
            query += " ORDER BY ph.price_date ASC"
            cursor.execute(query, params)
            history = clean_rows(cursor.fetchall())
        return jsonify({"success": True, "history": history, "count": len(history)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "history": []}), 500


@app.route("/api/prices", methods=["POST"])
@token_required
def add_price():
    data = get_json()
    for field in ["commodity", "market", "price"]:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400
    try:
        price = float(data["price"])
        if price <= 0:
            return jsonify({"error": "Price must be greater than zero"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Price must be a number"}), 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM commodities WHERE name = %s", (data["commodity"],))
            commodity = cursor.fetchone()
            cursor.execute("SELECT id FROM markets WHERE name = %s", (data["market"],))
            market = cursor.fetchone()
            if not commodity:
                return jsonify({"error": f"Commodity \"{data['commodity']}\" not found"}), 404
            if not market:
                return jsonify({"error": f"Market \"{data['market']}\" not found"}), 404

            is_verified = request.user.get("role") == "admin"
            cursor.execute("""
                INSERT INTO price_history (commodity_id, market_id, user_id, price, unit, volume, quality, source_type, is_verified, trend, price_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'user_submitted', %s, 'stable', CURRENT_DATE, %s)
                RETURNING id
            """, (
                commodity["id"], market["id"], request.user["user_id"], price, data.get("unit", "kg"),
                data.get("volume"), data.get("quality", "Standard"), is_verified, data.get("notes"),
            ))
            price_id = cursor.fetchone()["id"]

        cache.clear()
        threading.Thread(target=retrain_forecast_model, daemon=True).start()
        return jsonify({"success": True, "message": "Price submitted", "id": price_id, "verified": is_verified}), 201
    except Exception as exc:
        logger.exception("Add price error")
        return jsonify({"error": str(exc)}), 500


def build_forecast_response():
    commodity = request.args.get("commodity")
    market = request.args.get("market")
    days = min(int(request.args.get("days", 14)), 60)
    if not commodity:
        return jsonify({"error": "commodity parameter required"}), 400

    try:
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT c.name AS commodity, m.name AS market, lp.current_price, lp.price_7d,
                       lp.price_14d, lp.price_30d, lp.trend, lp.recommendation, lp.confidence
                FROM live_prices lp
                JOIN commodities c ON lp.commodity_id = c.id
                JOIN markets m ON lp.market_id = m.id
                WHERE c.name = %s
            """
            params = [commodity]
            if market:
                query += " AND m.name = %s"
                params.append(market)
            query += " ORDER BY m.name LIMIT 1"
            cursor.execute(query, params)
            live_price = cursor.fetchone()

        if not live_price:
            with get_db_cursor(commit=False) as cursor:
                query = """
                    SELECT c.name AS commodity, m.name AS market,
                           ROUND(((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2)::numeric, 2) AS current_price,
                           ROUND((((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2) * 1.01)::numeric, 2) AS price_7d,
                           ROUND((((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2) * 1.02)::numeric, 2) AS price_14d,
                           ROUND((((COALESCE(c.typical_min_price, 5) + COALESCE(c.typical_max_price, 10)) / 2) * 1.03)::numeric, 2) AS price_30d,
                           'stable' AS trend, 'Monitor' AS recommendation, 60 AS confidence
                    FROM commodities c
                    CROSS JOIN markets m
                    WHERE c.is_active = true AND m.is_active = true AND c.name = %s
                """
                params = [commodity]
                if market:
                    query += " AND m.name = %s"
                    params.append(market)
                query += " ORDER BY m.name LIMIT 1"
                cursor.execute(query, params)
                live_price = cursor.fetchone()
        if not live_price:
            return jsonify({"error": "No forecast available for this commodity"}), 404

        current = float(live_price["current_price"])
        price_7d = float(live_price["price_7d"] or current)
        price_14d = float(live_price["price_14d"] or price_7d)
        price_30d = float(live_price["price_30d"] or price_14d)
        forecast = []
        for day_num in range(1, days + 1):
            if day_num <= 7:
                predicted = current + ((price_7d - current) / 7) * day_num
            elif day_num <= 14:
                predicted = price_7d + ((price_14d - price_7d) / 7) * (day_num - 7)
            else:
                predicted = price_14d + ((price_30d - price_14d) / 16) * (day_num - 14)
            forecast.append({
                "day": day_num,
                "date": (datetime.now() + timedelta(days=day_num)).strftime("%Y-%m-%d"),
                "predicted_price": round(predicted, 2),
                "change_percent": round(((predicted - current) / current) * 100, 2) if current else 0,
                "confidence": "High" if day_num <= 14 else "Medium",
            })

        return jsonify({
            "success": True,
            "commodity": live_price["commodity"],
            "market": live_price["market"],
            "current_price": current,
            "forecast": forecast,
            "trend": live_price["trend"],
            "recommendation": live_price["recommendation"],
            "confidence": clean_value(live_price["confidence"]),
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/forecast", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def get_forecast():
    return build_forecast_response()


@app.route("/api/forecast/realtime", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def get_realtime_forecast():
    return build_forecast_response()


@app.route("/api/admin/retrain-forecast", methods=["POST"])
@admin_required
def retrain_forecast():
    try:
        retrain_forecast_model()
        return jsonify({"success": True, "message": "Forecast model retrained successfully"})
    except Exception as exc:
        logger.exception("Retrain error")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/commodities", methods=["GET"])
@cache.cached(timeout=3600)
def get_commodities():
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, name, category, sub_category, unit_of_measure, icon_emoji,
                       color_code, description, is_active
                FROM commodities WHERE is_active = true ORDER BY display_order, category, name
            """)
            commodities = clean_rows(cursor.fetchall())
        return jsonify({"success": True, "commodities": commodities, "count": len(commodities)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "commodities": []}), 500


@app.route("/api/markets", methods=["GET"])
@cache.cached(timeout=3600)
def get_markets():
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, name, market_code, province, district, town, latitude, longitude,
                       market_days, operating_hours, has_weighbridge, has_storage, is_active
                FROM markets WHERE is_active = true ORDER BY province, name
            """)
            markets = clean_rows(cursor.fetchall())
        return jsonify({"success": True, "markets": markets, "count": len(markets)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "markets": []}), 500


def list_party(table_name):
    commodity = request.args.get("commodity")
    limit = min(int(request.args.get("limit", 200)), 1000)
    cols = table_columns(table_name)
    try:
        with get_db_cursor(commit=False) as cursor:
            if table_name == "buyers" and "commodities_of_interest" in cols:
                query = """
                    SELECT b.id, b.user_id, b.business_name AS name, b.business_name,
                           b.contact_person, b.contact_phone AS phone, b.contact_phone,
                           b.contact_email AS email, b.contact_email,
                           COALESCE(c.name, b.commodities_of_interest::text, '') AS commodity,
                           b.location, COALESCE(b.max_price, b.max_price_per_kg) AS price,
                           COALESCE(b.max_price, b.max_price_per_kg) AS max_price,
                           b.min_volume_required AS volume, b.min_volume_required AS min_volume,
                           b.notes, b.is_verified, b.average_rating AS rating, b.status, b.created_at
                    FROM buyers b
                    LEFT JOIN commodities c ON b.commodity_id = c.id
                    WHERE b.status = 'active'
                """
            elif table_name == "sellers" and "commodities_sold" in cols:
                query = """
                    SELECT s.id, s.user_id, COALESCE(s.farm_name, s.business_name) AS name,
                           s.farm_name, s.business_name, s.contact_person,
                           s.contact_phone AS phone, s.contact_phone,
                           s.contact_email AS email, s.contact_email,
                           COALESCE(c.name, s.commodities_sold::text, '') AS commodity,
                           s.location, s.price_per_kg AS price, s.price_per_kg,
                           s.available_volume_kg AS volume, s.available_volume_kg AS available_volume,
                           s.notes, s.is_verified, s.average_rating AS rating, s.status, s.created_at
                    FROM sellers s
                    LEFT JOIN commodities c ON s.commodity_id = c.id
                    WHERE s.status = 'active'
                """
            else:
                name_col = "business_name" if table_name == "buyers" else "farm_name"
                price_col = "max_price" if table_name == "buyers" else "price_per_kg"
                volume_col = "min_volume" if table_name == "buyers" else "available_volume"
                alias = "b" if table_name == "buyers" else "s"
                query = f"""
                    SELECT {alias}.id, {alias}.user_id, {alias}.{name_col} AS name, {alias}.{name_col},
                           {alias}.contact_person, {alias}.contact_phone AS phone, {alias}.contact_phone,
                           {alias}.contact_email AS email, {alias}.contact_email,
                           {alias}.commodity, {alias}.location, {alias}.{price_col} AS price,
                           {alias}.{price_col}, {alias}.{volume_col} AS volume, {alias}.{volume_col},
                           {alias}.notes, {alias}.is_verified, {alias}.rating, {alias}.status, {alias}.created_at
                    FROM {table_name} {alias}
                    WHERE {alias}.status = 'active'
                """
            params = []
            if commodity:
                query += " AND COALESCE(c.name, commodity) = %s" if "commodity" in cols and "commodity_id" in cols else " AND c.name = %s" if "commodity_id" in cols else " AND commodity = %s"
                params.append(commodity)
            query += " ORDER BY is_verified DESC, rating DESC, created_at DESC LIMIT %s"
            params.append(limit)
            cursor.execute(query, params)
            rows = clean_rows(cursor.fetchall())
        return jsonify({"success": True, table_name: rows, "count": len(rows)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), table_name: []}), 500


@app.route("/api/buyers", methods=["GET"])
def get_buyers():
    return list_party("buyers")


@app.route("/api/sellers", methods=["GET"])
def get_sellers():
    return list_party("sellers")


@app.route("/api/buyers", methods=["POST"])
@token_required
def create_buyer():
    data = get_json()
    try:
        cols = table_columns("buyers")
        commodity_id = find_commodity_id(data.get("commodity"))
        is_admin = request.user.get("role") == "admin"
        with get_db_cursor() as cursor:
            fields = {
                "user_id": request.user["user_id"],
                "business_name": data.get("business_name") or data.get("name"),
                "contact_person": data.get("contact_person") or data.get("name"),
                "contact_phone": data.get("contact_phone") or data.get("phone"),
                "contact_email": data.get("contact_email") or data.get("email"),
                "location": data.get("location"),
                "notes": data.get("notes"),
                "is_verified": coerce_bool(data.get("is_verified")) if is_admin else False,
                "status": "active",
            }
            if "commodity" in cols:
                fields["commodity"] = data.get("commodity")
            if "commodity_id" in cols:
                fields["commodity_id"] = commodity_id
            if "max_price" in cols:
                fields["max_price"] = data.get("max_price") or data.get("price")
            if "max_price_per_kg" in cols:
                fields["max_price_per_kg"] = data.get("max_price") or data.get("price")
            if "min_volume" in cols:
                fields["min_volume"] = data.get("min_volume") or data.get("volume")
            if "min_volume_required" in cols:
                fields["min_volume_required"] = data.get("min_volume") or data.get("volume")
            if "added_by" in cols:
                fields["added_by"] = request.user.get("username")
            if "rating" in cols:
                fields["rating"] = data.get("rating") if is_admin and data.get("rating") is not None else 4.0
            if "average_rating" in cols:
                fields["average_rating"] = data.get("rating") if is_admin and data.get("rating") is not None else 4.0
            fields = {key: value for key, value in fields.items() if key in cols}
            columns = ", ".join(fields.keys())
            placeholders = ", ".join(["%s"] * len(fields))
            cursor.execute(f"INSERT INTO buyers ({columns}) VALUES ({placeholders}) RETURNING id", list(fields.values()))
            item_id = cursor.fetchone()["id"]
        cache.clear()
        return jsonify({"success": True, "message": "Buyer saved", "id": item_id}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/sellers", methods=["POST"])
@token_required
def create_seller():
    data = get_json()
    try:
        cols = table_columns("sellers")
        commodity_id = find_commodity_id(data.get("commodity"))
        is_admin = request.user.get("role") == "admin"
        with get_db_cursor() as cursor:
            existing_seller_id = None
            if not is_admin and "user_id" in cols:
                cursor.execute("SELECT id FROM sellers WHERE user_id = %s LIMIT 1", (request.user["user_id"],))
                existing = cursor.fetchone()
                existing_seller_id = existing["id"] if existing else None
            fields = {
                "user_id": request.user["user_id"],
                "farm_name": data.get("farm_name") or data.get("name"),
                "business_name": data.get("business_name") or data.get("name"),
                "contact_person": data.get("contact_person") or data.get("name"),
                "contact_phone": data.get("contact_phone") or data.get("phone"),
                "contact_email": data.get("contact_email") or data.get("email"),
                "location": data.get("location"),
                "notes": data.get("notes"),
                "is_verified": coerce_bool(data.get("is_verified")) if is_admin else False,
                "status": "active",
            }
            if "commodity" in cols:
                fields["commodity"] = data.get("commodity")
            if "commodity_id" in cols:
                fields["commodity_id"] = commodity_id
            if "available_volume" in cols:
                fields["available_volume"] = data.get("available_volume") or data.get("volume")
            if "available_volume_kg" in cols:
                fields["available_volume_kg"] = data.get("available_volume") or data.get("volume")
            if "price_per_kg" in cols:
                fields["price_per_kg"] = data.get("price_per_kg") or data.get("price")
            if "rating" in cols:
                fields["rating"] = data.get("rating") if is_admin and data.get("rating") is not None else 4.0
            if "average_rating" in cols:
                fields["average_rating"] = data.get("rating") if is_admin and data.get("rating") is not None else 4.0
            fields = {key: value for key, value in fields.items() if key in cols}
            if existing_seller_id:
                fields.pop("user_id", None)
                set_clause = ", ".join([f"{field} = %s" for field in fields])
                cursor.execute(f"UPDATE sellers SET {set_clause} WHERE id = %s RETURNING id", list(fields.values()) + [existing_seller_id])
            else:
                columns = ", ".join(fields.keys())
                placeholders = ", ".join(["%s"] * len(fields))
                cursor.execute(f"INSERT INTO sellers ({columns}) VALUES ({placeholders}) RETURNING id", list(fields.values()))
            item_id = cursor.fetchone()["id"]
        cache.clear()
        return jsonify({"success": True, "message": "Seller saved", "id": item_id}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def update_party(table_name, item_id):
    data = get_json()
    cols = table_columns(table_name)
    fields = {
        "buyers": [
            "business_name", "contact_person", "contact_phone", "contact_email",
            "commodity", "location", "max_price", "max_price_per_kg",
            "min_volume", "min_volume_required", "notes", "status",
        ],
        "sellers": [
            "farm_name", "business_name", "contact_person", "contact_phone",
            "contact_email", "commodity", "location", "price_per_kg",
            "available_volume", "available_volume_kg", "notes", "status",
        ],
    }[table_name]
    updates = {field: data[field] for field in fields if field in data and field in cols}
    if "name" in data:
        name_field = "business_name" if table_name == "buyers" else "farm_name"
        if name_field in cols:
            updates[name_field] = data["name"]
    if "phone" in data and "contact_phone" in cols:
        updates["contact_phone"] = data["phone"]
    if "email" in data and "contact_email" in cols:
        updates["contact_email"] = data["email"]
    if request.user.get("role") == "admin":
        if "is_verified" in data and "is_verified" in cols:
            updates["is_verified"] = coerce_bool(data["is_verified"])
        if "rating" in data:
            if "rating" in cols:
                updates["rating"] = data["rating"]
            if "average_rating" in cols:
                updates["average_rating"] = data["rating"]
    if table_name == "buyers":
        if "max_price" in data and "max_price_per_kg" in cols:
            updates["max_price_per_kg"] = data["max_price"]
        if "min_volume" in data and "min_volume_required" in cols:
            updates["min_volume_required"] = data["min_volume"]
    else:
        if "available_volume" in data and "available_volume_kg" in cols:
            updates["available_volume_kg"] = data["available_volume"]
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    set_clause = ", ".join([f"{field} = %s" for field in updates])
    params = list(updates.values()) + [item_id]
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = %s RETURNING id", params)
            if not cursor.fetchone():
                return jsonify({"error": "Record not found"}), 404
        cache.clear()
        return jsonify({"success": True, "message": "Record updated"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/buyers/<item_id>", methods=["PUT"])
@token_required
def update_buyer(item_id):
    return update_party("buyers", item_id)


@app.route("/api/sellers/<item_id>", methods=["PUT"])
@token_required
def update_seller(item_id):
    return update_party("sellers", item_id)


@app.route("/api/buyers/<item_id>", methods=["DELETE"])
@token_required
def delete_buyer(item_id):
    return soft_delete_party("buyers", item_id)


@app.route("/api/sellers/<item_id>", methods=["DELETE"])
@token_required
def delete_seller(item_id):
    return soft_delete_party("sellers", item_id)


def soft_delete_party(table_name, item_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"UPDATE {table_name} SET status = 'inactive' WHERE id = %s RETURNING id", (item_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Record not found"}), 404
        cache.clear()
        return jsonify({"success": True, "message": "Record deleted"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/news", methods=["GET"])
def get_news():
    limit = min(int(request.args.get("limit", 50)), 200)
    try:
        cols = table_columns("news")
        image_expr = "image_url" if "image_url" in cols else "NULL AS image_url"
        comment_expr = "comment_count" if "comment_count" in cols else "0 AS comment_count"
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(f"""
                SELECT id, title, content, summary, {image_expr}, category, author_name, status,
                       view_count, like_count, {comment_expr}, published_at, created_at, updated_at
                FROM news WHERE status = 'published'
                ORDER BY published_at DESC, created_at DESC LIMIT %s
            """, (limit,))
            news = clean_rows(cursor.fetchall())
        return jsonify({"success": True, "news": news, "count": len(news)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "news": []}), 500


@app.route("/api/news", methods=["POST"])
@admin_required
def create_news():
    data = request.form.to_dict() if request.form else get_json()
    cols = table_columns("news")
    image_url = data.get("image_url")
    image_file = request.files.get("image") or request.files.get("featured_image")
    if image_file:
        image_url = save_uploaded_file(image_file, "news")
    if not data.get("title") or not data.get("content"):
        return jsonify({"error": "title and content are required"}), 400
    try:
        with get_db_cursor() as cursor:
            fields = {
                "title": data["title"],
                "content": data["content"],
                "summary": data.get("summary"),
                "category": data.get("category"),
                "author_id": request.user["user_id"],
                "author_name": request.user.get("name") or request.user.get("username"),
                "status": "published",
            }
            if "image_url" in cols:
                fields["image_url"] = image_url
            fields = {key: value for key, value in fields.items() if key in cols}
            columns = ", ".join(fields.keys())
            placeholders = ", ".join(["%s"] * len(fields))
            cursor.execute(f"INSERT INTO news ({columns}) VALUES ({placeholders}) RETURNING id", list(fields.values()))
            news_id = cursor.fetchone()["id"]
        return jsonify({"success": True, "message": "News saved", "id": news_id}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/news/<int:news_id>", methods=["PUT"])
@admin_required
def update_news(news_id):
    data = request.form.to_dict() if request.form else get_json()
    cols = table_columns("news")
    image_file = request.files.get("image") or request.files.get("featured_image")
    if image_file and "image_url" in cols:
        data["image_url"] = save_uploaded_file(image_file, "news")
    fields = ["title", "content", "summary", "image_url", "category", "status"]
    updates = {field: data[field] for field in fields if field in data and field in cols}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    updates["updated_at"] = datetime.now()
    set_clause = ", ".join([f"{field} = %s" for field in updates])
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"UPDATE news SET {set_clause} WHERE id = %s RETURNING id", list(updates.values()) + [news_id])
            if not cursor.fetchone():
                return jsonify({"error": "News item not found"}), 404
        return jsonify({"success": True, "message": "News updated"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/news/<int:news_id>", methods=["DELETE"])
@admin_required
def delete_news(news_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE news SET status = 'deleted' WHERE id = %s RETURNING id", (news_id,))
            if not cursor.fetchone():
                return jsonify({"error": "News item not found"}), 404
        return jsonify({"success": True, "message": "News deleted"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/news/<int:news_id>/view", methods=["POST"])
def view_news(news_id):
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE news SET view_count = view_count + 1 WHERE id = %s RETURNING view_count", (news_id,))
        row = cursor.fetchone()
    return jsonify({"success": bool(row), "view_count": row["view_count"] if row else 0})


@app.route("/api/news/<int:news_id>/like", methods=["POST"])
@token_required
def like_news(news_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM news_likes WHERE news_id = %s AND user_id = %s", (news_id, request.user["user_id"]))
            existing = cursor.fetchone()
            liked = not bool(existing)
            if existing:
                cursor.execute("DELETE FROM news_likes WHERE news_id = %s AND user_id = %s", (news_id, request.user["user_id"]))
            else:
                cursor.execute("""
                    INSERT INTO news_likes (news_id, user_id) VALUES (%s, %s)
                    ON CONFLICT (news_id, user_id) DO NOTHING
                """, (news_id, request.user["user_id"]))
            cursor.execute("""
                UPDATE news
                SET like_count = (SELECT COUNT(*) FROM news_likes WHERE news_id = %s)
                WHERE id = %s RETURNING like_count
            """, (news_id, news_id))
            row = cursor.fetchone()
        return jsonify({"success": bool(row), "liked": liked, "like_count": row["like_count"] if row else 0})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/news/<int:news_id>/comments", methods=["GET"])
def get_comments(news_id):
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT nc.id, nc.comment, nc.created_at,
                   COALESCE(u.first_name || ' ' || u.last_name, u.username, 'User') AS author_name
            FROM news_comments nc
            LEFT JOIN users u ON nc.user_id = u.id
            WHERE nc.news_id = %s ORDER BY nc.created_at ASC
        """, (news_id,))
        comments = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "comments": comments, "count": len(comments)})


@app.route("/api/news/<int:news_id>/comments", methods=["POST"])
@token_required
def add_comment(news_id):
    data = get_json()
    if not data.get("comment"):
        return jsonify({"error": "comment is required"}), 400
    has_comment_count = "comment_count" in table_columns("news")
    with get_db_cursor() as cursor:
        cursor.execute("INSERT INTO news_comments (news_id, user_id, comment) VALUES (%s, %s, %s)", (news_id, request.user["user_id"], data["comment"]))
        if has_comment_count:
            cursor.execute("UPDATE news SET comment_count = (SELECT COUNT(*) FROM news_comments WHERE news_id = %s) WHERE id = %s RETURNING comment_count", (news_id, news_id))
            row = cursor.fetchone()
            count = row["comment_count"] if row else 0
        else:
            cursor.execute("SELECT COUNT(*) AS count FROM news_comments WHERE news_id = %s", (news_id,))
            count = cursor.fetchone()["count"]
    return jsonify({"success": True, "comment_count": count})


@app.route("/api/messages", methods=["GET"])
@token_required
def get_messages():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM messages
            WHERE from_user_id = %s OR to_user_id = %s
            ORDER BY created_at DESC
        """, (request.user["user_id"], request.user["user_id"]))
        messages = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "messages": messages, "count": len(messages)})


@app.route("/api/messages", methods=["POST"])
@token_required
def create_message():
    data = get_json()
    if not data.get("message"):
        return jsonify({"error": "message is required"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO messages (from_user_id, to_user_id, subject, message)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (request.user["user_id"], data.get("to_user_id"), data.get("subject"), data["message"]))
        message_id = cursor.fetchone()["id"]
    return jsonify({"success": True, "message": "Message sent", "id": message_id}), 201


@app.route("/api/profile", methods=["GET"])
@token_required
def get_profile():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (request.user["user_id"],))
        user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    profile = clean_row(user)
    profile.pop("password_hash", None)
    return jsonify({"success": True, "profile": profile, "user": profile})


@app.route("/api/profile", methods=["PUT", "POST"])
@token_required
def update_profile():
    data = request.form.to_dict() if request.form else get_json()
    if "profile_picture" in request.files:
        data["profile_picture_url"] = save_uploaded_file(request.files["profile_picture"], "profiles")
    allowed = [
        "first_name", "last_name", "email", "phone", "location", "province", "district",
        "farm_size_hectares", "main_crops", "business_name", "business_registration_number",
        "preferred_language", "sms_alerts_enabled", "email_alerts_enabled", "profile_picture_url"
    ]
    updates = {field: data[field] for field in allowed if field in data}
    if isinstance(updates.get("main_crops"), str):
        updates["main_crops"] = [crop.strip() for crop in updates["main_crops"].split(",") if crop.strip()]
    if "name" in data:
        first, _, last = data["name"].partition(" ")
        updates["first_name"] = first
        updates["last_name"] = last
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    updates["updated_at"] = datetime.now()
    set_clause = ", ".join([f"{field} = %s" for field in updates])
    with get_db_cursor() as cursor:
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id", list(updates.values()) + [request.user["user_id"]])
    return jsonify({"success": True, "message": "Profile updated"})


@app.route("/api/profile/password", methods=["PUT", "POST"])
@app.route("/api/auth/password", methods=["PUT", "POST"])
@token_required
def update_password():
    data = get_json()
    new_password = data.get("new_password") or data.get("password")
    if not new_password:
        return jsonify({"error": "new_password is required"}), 400
    current_password = data.get("current_password")
    with get_db_cursor() as cursor:
        if current_password:
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (request.user["user_id"],))
            user = cursor.fetchone()
            if not user or not check_password_hash(user["password_hash"], current_password):
                return jsonify({"error": "Current password is incorrect"}), 400
        cursor.execute("UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (generate_password_hash(new_password), request.user["user_id"]))
    return jsonify({"success": True, "message": "Password updated"})


@app.route("/api/sms/subscriptions", methods=["GET"])
@token_required
def get_sms_subscriptions():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM sms_subscriptions WHERE user_id = %s ORDER BY created_at DESC", (request.user["user_id"],))
        subscriptions = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "subscriptions": subscriptions, "count": len(subscriptions)})


@app.route("/api/sms/subscribe", methods=["POST"])
@token_required
def sms_subscribe():
    data = get_json()
    if not data.get("commodity"):
        return jsonify({"error": "commodity is required"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO sms_subscriptions (user_id, commodity, market, alert_type, threshold, active)
            VALUES (%s, %s, %s, %s, %s, true) RETURNING id
        """, (request.user["user_id"], data["commodity"], data.get("market"), data.get("alert_type", "price_change"), data.get("threshold", 5)))
        sub_id = cursor.fetchone()["id"]
    return jsonify({"success": True, "message": "Subscription saved", "id": sub_id}), 201


@app.route("/api/sms/unsubscribe", methods=["POST"])
@token_required
def sms_unsubscribe():
    data = get_json()
    sub_id = data.get("id")
    commodity = data.get("commodity")
    with get_db_cursor() as cursor:
        if sub_id:
            cursor.execute("UPDATE sms_subscriptions SET active = false WHERE id = %s AND user_id = %s", (sub_id, request.user["user_id"]))
        elif commodity:
            cursor.execute("UPDATE sms_subscriptions SET active = false WHERE commodity = %s AND user_id = %s", (commodity, request.user["user_id"]))
        else:
            return jsonify({"error": "id or commodity is required"}), 400
    return jsonify({"success": True, "message": "Subscription disabled"})


@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    with get_db_cursor(commit=False) as cursor:
        stats = {}
        for table in ["users", "commodities", "markets", "price_history", "live_prices", "buyers", "sellers", "news"]:
            cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
            stats[table] = cursor.fetchone()["count"]
    return jsonify({"success": True, "stats": stats})


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT id, username, email, phone, first_name, last_name, role, is_active,
                   created_at, last_login
            FROM users ORDER BY created_at DESC
        """)
        users = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "users": users, "count": len(users)})


@app.route("/api/admin/users/<uuid:user_id>", methods=["PUT"])
@admin_required
def admin_update_user(user_id):
    data = get_json()
    allowed = ["email", "phone", "first_name", "last_name", "role", "is_active", "location", "province", "district"]
    updates = {field: data[field] for field in allowed if field in data}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    set_clause = ", ".join([f"{field} = %s" for field in updates])
    with get_db_cursor() as cursor:
        cursor.execute(f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id", list(updates.values()) + [str(user_id)])
    return jsonify({"success": True, "message": "User updated"})


@app.route("/api/admin/users/<uuid:user_id>", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE users SET is_active = false WHERE id = %s", (str(user_id),))
    return jsonify({"success": True, "message": "User disabled"})


@app.route("/api/admin/users/<uuid:user_id>/reset-password", methods=["POST"])
@admin_required
def admin_reset_password(user_id):
    data = get_json()
    password = data.get("new_password") or "123456"
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (generate_password_hash(password), str(user_id)))
    return jsonify({"success": True, "message": "Password reset"})


@app.route("/api/admin/verify-price", methods=["POST"])
@admin_required
def admin_verify_price():
    data = get_json()
    price_id = data.get("price_id")
    approve = bool(data.get("approve", True))
    if not price_id:
        return jsonify({"error": "price_id is required"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE price_history SET is_verified = %s WHERE id = %s RETURNING id", (approve, price_id))
        if not cursor.fetchone():
            return jsonify({"error": "Price not found"}), 404
    threading.Thread(target=retrain_forecast_model, daemon=True).start()
    return jsonify({"success": True, "message": "Price verification updated"})


@app.route("/api/admin/prices/<int:price_id>", methods=["DELETE"])
@admin_required
def admin_delete_price(price_id):
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM price_history WHERE id = %s RETURNING id", (price_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Price not found"}), 404
    cache.clear()
    return jsonify({"success": True, "message": "Price deleted"})


@app.route("/api/admin/buyers/pending", methods=["GET"])
@admin_required
def admin_pending_buyers():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM buyers WHERE is_verified = false AND status = 'active' ORDER BY created_at DESC")
        buyers = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "buyers": buyers, "count": len(buyers)})


@app.route("/api/admin/buyers/<int:buyer_id>/verify", methods=["POST"])
@admin_required
def admin_verify_buyer(buyer_id):
    """Verify/approve a buyer"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM buyers WHERE id = %s", (buyer_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Buyer not found"}), 404
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE buyers SET is_verified = true WHERE id = %s", (buyer_id,))
        
        cache.clear()
        return jsonify({"success": True, "message": "Buyer verified successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/buyers/<int:buyer_id>/reject", methods=["POST"])
@admin_required
def admin_reject_buyer(buyer_id):
    """Reject/deactivate a buyer"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM buyers WHERE id = %s", (buyer_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Buyer not found"}), 404
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE buyers SET status = 'inactive' WHERE id = %s", (buyer_id,))
        
        cache.clear()
        return jsonify({"success": True, "message": "Buyer rejected successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ===================== ADMIN BUYERS MANAGEMENT =====================

@app.route("/api/admin/buyers", methods=["GET"])
@admin_required
def admin_get_all_buyers():
    """Get all buyers with optional filtering"""
    status = request.args.get("status", None)
    verified = request.args.get("verified", None)
    search = request.args.get("search", None)
    
    query = "SELECT * FROM buyers WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if verified is not None:
        verified_bool = verified.lower() in ['true', '1', 'yes']
        query += " AND is_verified = %s"
        params.append(verified_bool)
    
    if search:
        search_term = f"%{search}%"
        query += " AND (business_name ILIKE %s OR contact_person ILIKE %s OR contact_phone ILIKE %s OR contact_email ILIKE %s)"
        params.extend([search_term, search_term, search_term, search_term])
    
    query += " ORDER BY created_at DESC"
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, params)
        buyers = clean_rows(cursor.fetchall())
    
    return jsonify({"success": True, "buyers": buyers, "count": len(buyers)})


@app.route("/api/admin/buyers/<int:buyer_id>", methods=["GET"])
@admin_required
def admin_get_buyer(buyer_id):
    """Get a specific buyer"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM buyers WHERE id = %s", (buyer_id,))
        buyer = cursor.fetchone()
        if not buyer:
            return jsonify({"error": "Buyer not found"}), 404
        buyer = clean_rows([buyer])[0]
    return jsonify({"success": True, "buyer": buyer})


@app.route("/api/admin/buyers", methods=["POST"])
@admin_required
def admin_create_buyer():
    """Create a new buyer as admin"""
    data = get_json()
    try:
        cols = table_columns("buyers")
        commodity_id = find_commodity_id(data.get("commodity"))
        
        with get_db_cursor() as cursor:
            fields = {
                "business_name": data.get("business_name") or data.get("name"),
                "contact_person": data.get("contact_person") or data.get("name"),
                "contact_phone": data.get("contact_phone") or data.get("phone"),
                "contact_email": data.get("contact_email") or data.get("email"),
                "location": data.get("location"),
                "notes": data.get("notes"),
                "is_verified": coerce_bool(data.get("is_verified", False)),
                "status": data.get("status", "active"),
                "rating": data.get("rating", 4.0),
            }
            
            if "commodity" in cols:
                fields["commodity"] = data.get("commodity")
            if "commodity_id" in cols:
                fields["commodity_id"] = commodity_id
            if "max_price" in cols:
                fields["max_price"] = data.get("max_price") or data.get("price")
            if "max_price_per_kg" in cols:
                fields["max_price_per_kg"] = data.get("max_price") or data.get("price")
            if "min_volume" in cols:
                fields["min_volume"] = data.get("min_volume") or data.get("volume")
            if "min_volume_required" in cols:
                fields["min_volume_required"] = data.get("min_volume") or data.get("volume")
            if "added_by" in cols:
                fields["added_by"] = request.user.get("username")
            if "user_id" in cols and data.get("user_id"):
                fields["user_id"] = data.get("user_id")
            
            fields = {key: value for key, value in fields.items() if key in cols and value is not None}
            
            columns = ", ".join(fields.keys())
            placeholders = ", ".join(["%s"] * len(fields))
            cursor.execute(f"INSERT INTO buyers ({columns}) VALUES ({placeholders}) RETURNING id", list(fields.values()))
            buyer_id = cursor.fetchone()["id"]
        
        cache.clear()
        return jsonify({"success": True, "message": "Buyer created successfully", "id": buyer_id}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/buyers/<int:buyer_id>", methods=["PUT"])
@admin_required
def admin_update_buyer(buyer_id):
    """Update a buyer"""
    data = get_json()
    cols = table_columns("buyers")
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM buyers WHERE id = %s", (buyer_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Buyer not found"}), 404
        
        allowed_fields = [
            "business_name", "contact_person", "contact_phone", "contact_email",
            "commodity", "location", "max_price", "max_price_per_kg",
            "min_volume", "min_volume_required", "notes", "status",
            "is_verified", "rating", "average_rating"
        ]
        
        updates = {field: data[field] for field in allowed_fields if field in data and field in cols}
        
        if "name" in data and "business_name" in cols:
            updates["business_name"] = data["name"]
        if "phone" in data and "contact_phone" in cols:
            updates["contact_phone"] = data["phone"]
        if "email" in data and "contact_email" in cols:
            updates["contact_email"] = data["email"]
        if "price" in data and "max_price" in cols:
            updates["max_price"] = data["price"]
        if "price" in data and "max_price_per_kg" in cols:
            updates["max_price_per_kg"] = data["price"]
        if "volume" in data and "min_volume" in cols:
            updates["min_volume"] = data["volume"]
        if "volume" in data and "min_volume_required" in cols:
            updates["min_volume_required"] = data["volume"]
        
        if "is_verified" in data:
            updates["is_verified"] = coerce_bool(data["is_verified"])
        if "rating" in data:
            if "rating" in cols:
                updates["rating"] = data["rating"]
            if "average_rating" in cols:
                updates["average_rating"] = data["rating"]
        
        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400
        
        set_clause = ", ".join([f"{field} = %s" for field in updates])
        params = list(updates.values()) + [buyer_id]
        
        with get_db_cursor() as cursor:
            cursor.execute(f"UPDATE buyers SET {set_clause} WHERE id = %s", params)
        
        cache.clear()
        return jsonify({"success": True, "message": "Buyer updated successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/buyers/<int:buyer_id>", methods=["DELETE"])
@admin_required
def admin_delete_buyer(buyer_id):
    """Delete a buyer (soft delete)"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM buyers WHERE id = %s", (buyer_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Buyer not found"}), 404
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE buyers SET status = 'deleted' WHERE id = %s", (buyer_id,))
        
        cache.clear()
        return jsonify({"success": True, "message": "Buyer deleted successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ===================== ADMIN SELLERS MANAGEMENT =====================

@app.route("/api/admin/sellers", methods=["GET"])
@admin_required
def admin_get_all_sellers():
    """Get all sellers with optional filtering"""
    status = request.args.get("status", None)
    verified = request.args.get("verified", None)
    search = request.args.get("search", None)
    
    query = "SELECT * FROM sellers WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if verified is not None:
        verified_bool = verified.lower() in ['true', '1', 'yes']
        query += " AND is_verified = %s"
        params.append(verified_bool)
    
    if search:
        search_term = f"%{search}%"
        query += " AND (farm_name ILIKE %s OR business_name ILIKE %s OR contact_person ILIKE %s OR contact_phone ILIKE %s OR contact_email ILIKE %s)"
        params.extend([search_term, search_term, search_term, search_term, search_term])
    
    query += " ORDER BY created_at DESC"
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, params)
        sellers = clean_rows(cursor.fetchall())
    
    return jsonify({"success": True, "sellers": sellers, "count": len(sellers)})


@app.route("/api/admin/sellers/<int:seller_id>", methods=["GET"])
@admin_required
def admin_get_seller(seller_id):
    """Get a specific seller"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM sellers WHERE id = %s", (seller_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({"error": "Seller not found"}), 404
        seller = clean_rows([seller])[0]
    return jsonify({"success": True, "seller": seller})


@app.route("/api/admin/sellers", methods=["POST"])
@admin_required
def admin_create_seller():
    """Create a new seller as admin"""
    data = get_json()
    try:
        cols = table_columns("sellers")
        commodity_id = find_commodity_id(data.get("commodity"))
        
        with get_db_cursor() as cursor:
            fields = {
                "farm_name": data.get("farm_name") or data.get("name"),
                "business_name": data.get("business_name") or data.get("name"),
                "contact_person": data.get("contact_person") or data.get("name"),
                "contact_phone": data.get("contact_phone") or data.get("phone"),
                "contact_email": data.get("contact_email") or data.get("email"),
                "location": data.get("location"),
                "notes": data.get("notes"),
                "is_verified": coerce_bool(data.get("is_verified", False)),
                "status": data.get("status", "active"),
                "rating": data.get("rating", 4.0),
            }
            
            if "commodity" in cols:
                fields["commodity"] = data.get("commodity")
            if "commodity_id" in cols:
                fields["commodity_id"] = commodity_id
            if "available_volume" in cols:
                fields["available_volume"] = data.get("available_volume") or data.get("volume")
            if "available_volume_kg" in cols:
                fields["available_volume_kg"] = data.get("available_volume") or data.get("volume")
            if "price_per_kg" in cols:
                fields["price_per_kg"] = data.get("price_per_kg") or data.get("price")
            if "user_id" in cols and data.get("user_id"):
                fields["user_id"] = data.get("user_id")
            
            fields = {key: value for key, value in fields.items() if key in cols and value is not None}
            
            columns = ", ".join(fields.keys())
            placeholders = ", ".join(["%s"] * len(fields))
            cursor.execute(f"INSERT INTO sellers ({columns}) VALUES ({placeholders}) RETURNING id", list(fields.values()))
            seller_id = cursor.fetchone()["id"]
        
        cache.clear()
        return jsonify({"success": True, "message": "Seller created successfully", "id": seller_id}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/sellers/<int:seller_id>", methods=["PUT"])
@admin_required
def admin_update_seller(seller_id):
    """Update a seller"""
    data = get_json()
    cols = table_columns("sellers")
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM sellers WHERE id = %s", (seller_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Seller not found"}), 404
        
        allowed_fields = [
            "farm_name", "business_name", "contact_person", "contact_phone",
            "contact_email", "commodity", "location", "price_per_kg",
            "available_volume", "available_volume_kg", "notes", "status",
            "is_verified", "rating", "average_rating"
        ]
        
        updates = {field: data[field] for field in allowed_fields if field in data and field in cols}
        
        if "name" in data and "business_name" in cols:
            updates["business_name"] = data["name"]
        if "name" in data and "farm_name" in cols:
            updates["farm_name"] = data["name"]
        if "phone" in data and "contact_phone" in cols:
            updates["contact_phone"] = data["phone"]
        if "email" in data and "contact_email" in cols:
            updates["contact_email"] = data["email"]
        if "price" in data and "price_per_kg" in cols:
            updates["price_per_kg"] = data["price"]
        if "volume" in data and "available_volume" in cols:
            updates["available_volume"] = data["volume"]
        if "volume" in data and "available_volume_kg" in cols:
            updates["available_volume_kg"] = data["volume"]
        
        if "is_verified" in data:
            updates["is_verified"] = coerce_bool(data["is_verified"])
        if "rating" in data:
            if "rating" in cols:
                updates["rating"] = data["rating"]
            if "average_rating" in cols:
                updates["average_rating"] = data["rating"]
        
        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400
        
        set_clause = ", ".join([f"{field} = %s" for field in updates])
        params = list(updates.values()) + [seller_id]
        
        with get_db_cursor() as cursor:
            cursor.execute(f"UPDATE sellers SET {set_clause} WHERE id = %s", params)
        
        cache.clear()
        return jsonify({"success": True, "message": "Seller updated successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/sellers/<int:seller_id>", methods=["DELETE"])
@admin_required
def admin_delete_seller(seller_id):
    """Delete a seller (soft delete)"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM sellers WHERE id = %s", (seller_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Seller not found"}), 404
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE sellers SET status = 'deleted' WHERE id = %s", (seller_id,))
        
        cache.clear()
        return jsonify({"success": True, "message": "Seller deleted successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/sellers/pending", methods=["GET"])
@admin_required
def admin_pending_sellers():
    """Get pending/unverified sellers"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM sellers WHERE is_verified = false AND status = 'active' ORDER BY created_at DESC")
        sellers = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "sellers": sellers, "count": len(sellers)})


@app.route("/api/admin/sellers/<int:seller_id>/verify", methods=["POST"])
@admin_required
def admin_verify_seller(seller_id):
    """Verify/approve a seller"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM sellers WHERE id = %s", (seller_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Seller not found"}), 404
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE sellers SET is_verified = true WHERE id = %s", (seller_id,))
        
        cache.clear()
        return jsonify({"success": True, "message": "Seller verified successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/sellers/<int:seller_id>/reject", methods=["POST"])
@admin_required
def admin_reject_seller(seller_id):
    """Reject/deactivate a seller"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT id FROM sellers WHERE id = %s", (seller_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Seller not found"}), 404
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE sellers SET status = 'inactive' WHERE id = %s", (seller_id,))
        
        cache.clear()
        return jsonify({"success": True, "message": "Seller rejected successfully"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/subscribers", methods=["GET"])
@admin_required
def admin_subscribers():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT ss.*, u.username, u.phone, u.email
            FROM sms_subscriptions ss
            LEFT JOIN users u ON ss.user_id = u.id
            ORDER BY ss.created_at DESC
        """)
        subscribers = clean_rows(cursor.fetchall())
    return jsonify({"success": True, "subscribers": subscribers, "count": len(subscribers)})


@app.route("/api/admin/broadcast", methods=["POST"])
@admin_required
def admin_broadcast():
    data = get_json()
    message = data.get("message")
    if not message:
        return jsonify({"error": "message is required"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO sms_history (message, type, status, provider, queued_at)
            VALUES (%s, 'broadcast', %s, 'admin', CURRENT_TIMESTAMP)
        """, (message, "simulated" if data.get("dry_run", True) else "pending"))
    return jsonify({"success": True, "message": "Broadcast queued"})


@app.route("/api/data/collect", methods=["POST"])
@admin_required
def collect_data():
    threading.Thread(target=retrain_forecast_model, daemon=True).start()
    return jsonify({"success": True, "message": "Data refresh started"})


@app.route("/api/backup/create", methods=["POST"])
@admin_required
def create_backup():
    return jsonify({"success": True, "message": "Backup endpoint available", "backup": None})


@app.route("/api/backup/list", methods=["GET"])
@admin_required
def list_backups():
    backup_dir = os.path.join(BASE_DIR, "backups")
    backups = []
    if os.path.isdir(backup_dir):
        backups = sorted(os.listdir(backup_dir), reverse=True)
    return jsonify({"success": True, "backups": backups})


@app.route("/api/status", methods=["GET"])
def api_status():
    try:
        with get_db_cursor(commit=False) as cursor:
            stats = {}
            for table in ["users", "live_prices", "commodities", "markets"]:
                cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
                stats[table] = cursor.fetchone()["count"]
        return jsonify({"status": "online", "success": True, "version": "3.0.0", "database": "PostgreSQL", "stats": stats})
    except Exception as exc:
        return jsonify({"status": "error", "success": False, "error": str(exc)}), 500


@app.route("/ussd", methods=["POST", "GET"])
def ussd_callback():
    text = request.form.get("text", "") if request.method == "POST" else request.args.get("text", "")
    if text == "":
        return "CON FarmConnect Zambia\n1. Market Prices\n2. Price Forecast\n3. Find Buyers\n0. Exit"
    if text == "1":
        return "END Maize: ZMW 6.80/kg\nTomatoes: ZMW 8.50/kg\nBeans: ZMW 12.50/kg"
    if text == "2":
        return "END Maize forecast: Monitor. Prices expected to stay stable this week."
    if text == "3":
        return "END Visit FarmConnect or use the buyers menu to find verified buyers."
    return "END Thank you for using FarmConnect!"


@app.route("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({"message": "FarmConnect API is running", "version": "3.0.0"})


@app.route("/manifest.json")
def serve_manifest():
    manifest_path = os.path.join(BASE_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        return send_file(manifest_path)
    return jsonify({"name": "FarmConnect", "short_name": "FarmConnect"})


@app.route("/service-worker.js")
def serve_service_worker():
    worker_path = os.path.join(BASE_DIR, "service-worker.js")
    if os.path.exists(worker_path):
        return send_file(worker_path)
    return "", 204


@app.route("/static/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/<path:filename>")
def serve_frontend(filename):
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except Exception:
        return jsonify({"error": "Not found"}), 404


def print_banner():
    print("=" * 70)
    print("  FarmConnect Zambia - Live Prices and AI Forecasts v3.0")
    print("  Mulungushi University - ICT 431 Capstone")
    print("  Student: Daka Felix (202206453)")
    print("=" * 70)
    print("  Database: PostgreSQL")
    print("  Forecast retraining: every 6 hours")
    print("  Cache: Redis or in-memory")
    print("=" * 70)
    print("  AUTH:      POST /api/register, POST /api/login")
    print("  PRICES:    GET/POST /api/prices, GET /api/prices/history")
    print("  FORECAST:  GET /api/forecast, GET /api/forecast/realtime")
    print("  BUYERS:    GET/POST/PUT/DELETE /api/buyers")
    print("  SELLERS:   GET/POST/PUT/DELETE /api/sellers")
    print("  NEWS:      GET/POST/PUT/DELETE /api/news")
    print("  PROFILE:   GET/PUT /api/profile")
    print("  ADMIN:     /api/admin/*")
    print("  STATUS:    GET /api/status")
    print("=" * 70)
    print("  Default Admin: Felix / 5645")
    print("=" * 70)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=retrain_forecast_model, trigger="interval", hours=6, id="retrain_forecast", replace_existing=True)
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    if not init_db_pool():
        sys.exit(1)

    try:
        init_database()
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM live_prices")
            has_live_prices = cursor.fetchone()["count"] > 0
        if not has_live_prices:
            retrain_forecast_model()
    except Exception as exc:
        print(f"[ERROR] Database init failed: {exc}")
        sys.exit(1)

    start_scheduler()
    print_banner()

    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open("http://localhost:5000")), daemon=True).start()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    if socketio:
        socketio.run(app, debug=False, host=host, port=port, allow_unsafe_werkzeug=True)
    else:
        app.run(debug=False, host=host, port=port, threaded=True)
