#!/usr/bin/env python3
"""
Enhanced Price Forecasting Module with Trained ML Models
For FarmConnect - Zambian Market Information Platform
"""

import pickle
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sqlite3
import logging

# Setup logging
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')

# Commodity and market lists
COMMODITIES = ['Maize', 'Tomatoes', 'Beans', 'Groundnuts', 'Rice', 'Soybeans', 
               'Sweet Potatoes', 'Cassava', 'Onions', 'Cabbage']
MARKETS = ['Lusaka', 'Kitwe', 'Ndola', 'Livingstone', 'Chipata', 'Kabwe', 'Solwezi', 'Mongu']

# Default base prices (ZMW/kg) - Updated with accurate Zambian prices
DEFAULT_BASE_PRICES = {
    'Maize': 6.80,
    'Tomatoes': 8.50,
    'Beans': 12.50,
    'Groundnuts': 18.00,
    'Rice': 9.00,
    'Soybeans': 15.00,
    'Sweet Potatoes': 5.00,
    'Cassava': 4.00,
    'Onions': 10.00,
    'Cabbage': 4.00,
    'Sunflower': 12.00,
    'Wheat': 7.50,
    'Millet': 5.00,
    'Sorghum': 4.80,
    'Cowpeas': 10.00,
    'Pigeon Peas': 11.00
}

# Market adjustment factors
MARKET_FACTORS = {
    'Lusaka': 1.00,
    'Kitwe': 1.02,
    'Ndola': 1.01,
    'Livingstone': 0.98,
    'Chipata': 0.95,
    'Kabwe': 0.97,
    'Solwezi': 1.05,
    'Mongu': 0.94,
    'Chingola': 1.03,
    'Mufulira': 1.02,
    'Luanshya': 1.00,
    'Kasama': 0.96
}

# Seasonal factors (monthly)
SEASONAL_FACTORS = {
    1: 0.95, 2: 0.92, 3: 0.90, 4: 0.93, 5: 0.97, 6: 1.02,
    7: 1.08, 8: 1.12, 9: 1.10, 10: 1.05, 11: 1.00, 12: 0.98
}

# =========================================================
# MODEL LOADING
# =========================================================

_model = None
_scaler = None
_feature_cols = None

def load_model():
    """Load the trained ML model"""
    global _model, _scaler, _feature_cols
    
    model_path = os.path.join(MODEL_DIR, 'price_forecast_model.pkl')
    scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
    features_path = os.path.join(MODEL_DIR, 'feature_columns.pkl')
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            with open(model_path, 'rb') as f:
                _model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                _scaler = pickle.load(f)
            with open(features_path, 'rb') as f:
                _feature_cols = pickle.load(f)
            logger.info(f"✅ ML Model loaded successfully from {MODEL_DIR}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Error loading model: {e}")
    
    logger.warning("⚠️ ML Model not found. Using statistical fallback.")
    logger.info("💡 Run 'python train_model.py' to train the ML model")
    return False

def is_model_available():
    """Check if ML model is available"""
    if _model is None:
        return load_model()
    return _model is not None

# =========================================================
# DATABASE HELPER
# =========================================================

def get_db():
    """Get database connection"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'farm_market.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_current_price(commodity, market):
    """Get current price from database"""
    try:
        conn = get_db()
        if conn is None:
            return DEFAULT_BASE_PRICES.get(commodity, 10.0)
        
        cur = conn.cursor()
        cur.execute("""
            SELECT price FROM market_prices
            WHERE commodity = ? AND market LIKE ? AND verified = 1
            ORDER BY recorded_at DESC LIMIT 1
        """, (commodity, f"%{market}%"))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return row['price']
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
    
    return DEFAULT_BASE_PRICES.get(commodity, 10.0)

# =========================================================
# ML-BASED FORECAST
# =========================================================

def get_ml_forecast(commodity, market, days=7, current_price=None):
    """
    Get forecast using trained ML model
    """
    if not is_model_available():
        return None
    
    global _model, _scaler, _feature_cols
    
    # Get current price if not provided
    if current_price is None:
        current_price = get_current_price(commodity, market)
    
    now = datetime.now()
    predictions = []
    last_price = current_price
    
    for day in range(1, days + 1):
        forecast_date = now + timedelta(days=day)
        month = forecast_date.month
        year = forecast_date.year
        
        try:
            # Build feature vector
            features = {
                'year': year,
                'month_sin': np.sin(2 * np.pi * month / 12),
                'month_cos': np.cos(2 * np.pi * month / 12),
                'dow_sin': np.sin(2 * np.pi * forecast_date.weekday() / 7),
                'dow_cos': np.cos(2 * np.pi * forecast_date.weekday() / 7),
                'quarter': (month - 1) // 3 + 1,
                'year_norm': (year - 2020) / 6,
                'price_lag_1': last_price,
                'price_lag_2': last_price * 0.98,
                'price_ma_3': last_price,
                'market_factor': MARKET_FACTORS.get(market, 1.0),
                'seasonal_factor': SEASONAL_FACTORS.get(month, 1.0),
            }
            
            # Add commodity one-hot encoding
            for c in COMMODITIES:
                features[f'comm_{c}'] = 1 if c == commodity else 0
            
            # Add market one-hot encoding
            for m in MARKETS[:5]:
                features[f'market_{m}'] = 1 if m == market else 0
            
            # Create DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure all columns exist
            if _feature_cols:
                for col in _feature_cols:
                    if col not in feature_df.columns:
                        feature_df[col] = 0
                feature_df = feature_df[_feature_cols]
            
            # Scale and predict
            if _scaler:
                X_scaled = _scaler.transform(feature_df)
                predicted_price = _model.predict(X_scaled)[0]
            else:
                predicted_price = _model.predict(feature_df)[0]
            
            # Ensure realistic bounds
            predicted_price = max(2.0, min(predicted_price, 50.0))
            
        except Exception as e:
            logger.warning(f"ML prediction failed, using fallback: {e}")
            # Fallback prediction using simple method
            seasonal = SEASONAL_FACTORS.get(month, 1.0)
            market_factor = MARKET_FACTORS.get(market, 1.0)
            trend = 0.002 * day
            predicted_price = last_price * (1 + trend + (seasonal - 1) * 0.05 + (market_factor - 1) * 0.02)
            predicted_price = max(2.0, min(predicted_price, 50.0))
        
        # Calculate change
        change_percent = ((predicted_price - last_price) / last_price) * 100
        
        # Confidence based on forecast horizon
        if day <= 3:
            confidence = 'high'
        elif day <= 7:
            confidence = 'medium'
        elif day <= 14:
            confidence = 'low'
        else:
            confidence = 'very_low'
        
        predictions.append({
            'date': forecast_date.strftime('%Y-%m-%d'),
            'predicted_price': round(predicted_price, 2),
            'change_percent': round(change_percent, 1),
            'trend': 'up' if predicted_price > last_price else 'down' if predicted_price < last_price else 'stable',
            'confidence': confidence,
            'model': 'ml_linear_regression'
        })
        
        last_price = predicted_price
    
    return predictions

# =========================================================
# ENHANCED FORECAST WITH HYBRID APPROACH
# =========================================================

def enhanced_price_forecast(df, days=7, commodity="Maize", market="Lusaka", model_type="auto"):
    """
    Enhanced price forecast using ML or statistical methods
    """
    # Try ML first
    if model_type in ['auto', 'ml'] and is_model_available():
        try:
            current_price = float(df['price'].iloc[0]) if len(df) > 0 else DEFAULT_BASE_PRICES.get(commodity, 10.0)
            ml_forecast = get_ml_forecast(commodity, market, days, current_price)
            if ml_forecast:
                return ml_forecast
        except Exception as e:
            logger.warning(f"ML forecast failed: {e}")
    
    # Fallback to statistical method (seasonal + trend)
    if len(df) > 0:
        historical_prices = df['price'].values[:30]
        if len(historical_prices) > 1:
            try:
                trend = np.polyfit(range(len(historical_prices)), historical_prices, 1)[0]
                trend = max(-0.01, min(trend, 0.01))  # Cap trend to reasonable values
            except:
                trend = 0.001
        else:
            trend = 0.001
        seasonal = SEASONAL_FACTORS.get(datetime.now().month, 1.0)
        current_price = historical_prices[0]
    else:
        trend = 0.001
        seasonal = 1.0
        current_price = DEFAULT_BASE_PRICES.get(commodity, 10.0)
    
    market_factor = MARKET_FACTORS.get(market, 1.0)
    
    predictions = []
    for i in range(1, days + 1):
        forecast_date = datetime.now() + timedelta(days=i)
        month = forecast_date.month
        seasonal_factor = SEASONAL_FACTORS.get(month, 1.0)
        
        # Combine trend, seasonality, and market factors
        change = (trend * i) + (seasonal_factor - seasonal) * 0.05 + (market_factor - 1.0) * 0.02
        predicted_price = current_price * (1 + change + (random.random() - 0.5) * 0.01)
        
        # Ensure bounds
        predicted_price = max(2.0, min(predicted_price, 50.0))
        
        change_percent = ((predicted_price - current_price) / current_price) * 100
        
        # Confidence based on forecast horizon
        if i <= 3:
            confidence = 'medium'
        elif i <= 7:
            confidence = 'low'
        else:
            confidence = 'very_low'
        
        predictions.append({
            'date': forecast_date.strftime('%Y-%m-%d'),
            'predicted_price': round(predicted_price, 2),
            'change_percent': round(change_percent, 1),
            'trend': 'up' if predicted_price > current_price else 'down' if predicted_price < current_price else 'stable',
            'confidence': confidence,
            'model': 'statistical_fallback'
        })
    
    return predictions

def get_market_forecast(commodity, market, days):
    """Get forecast for specific commodity and market"""
    try:
        conn = get_db()
        if conn is None:
            return enhanced_price_forecast(pd.DataFrame(), days, commodity, market)
        
        cur = conn.cursor()
        cur.execute("""
            SELECT price, recorded_at FROM market_prices
            WHERE commodity=? AND market LIKE ? AND verified=1
            ORDER BY recorded_at DESC LIMIT 90
        """, (commodity, f"%{market}%"))
        rows = cur.fetchall()
        conn.close()
        
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            return enhanced_price_forecast(df, days, commodity, market)
        else:
            return enhanced_price_forecast(pd.DataFrame(), days, commodity, market)
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return enhanced_price_forecast(pd.DataFrame(), days, commodity, market)

def get_all_markets_forecast(commodity, days):
    """Get forecast for all markets"""
    forecasts = {}
    for market in MARKETS:
        forecasts[market] = get_market_forecast(commodity, market, days)
    return forecasts

def get_forecast_recommendations(commodity, market):
    """Generate trading recommendations based on forecast"""
    forecast = get_market_forecast(commodity, market, 14)
    
    if not forecast or len(forecast) < 7:
        return {
            'buy_sell': 'Hold',
            'timing': 'Monitor market',
            'reason': 'Insufficient data for accurate forecast',
            'action': 'Check prices daily on FarmConnect',
            'confidence': 'low'
        }
    
    # Analyze forecast trend
    prices = [f['predicted_price'] for f in forecast]
    first_price = prices[0]
    last_price = prices[-1]
    peak_price = max(prices)
    peak_day = prices.index(peak_price) + 1
    
    overall_change = ((last_price - first_price) / first_price) * 100
    
    if overall_change > 5:
        action = 'Hold for better price'
        timing = f'Consider selling around day {peak_day}'
        reason = f'Expected price increase of {overall_change:.1f}% over 14 days'
        buy_sell = 'Hold'
    elif overall_change < -3:
        action = 'Sell soon to avoid losses'
        timing = 'Within 3-5 days'
        reason = f'Expected price decrease of {abs(overall_change):.1f}%'
        buy_sell = 'Sell'
    else:
        action = 'Hold or sell gradually'
        timing = 'Monitor market daily'
        reason = f'Prices expected to remain stable (±{abs(overall_change):.1f}%)'
        buy_sell = 'Hold'
    
    # Determine confidence
    if abs(overall_change) > 5:
        confidence = 'high'
    elif abs(overall_change) > 2:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return {
        'buy_sell': buy_sell,
        'timing': timing,
        'reason': reason,
        'action': action,
        'confidence': confidence,
        'expected_change_percent': round(overall_change, 1),
        'peak_day': peak_day,
        'peak_price': round(peak_price, 2)
    }

def analyze_market_forecasts(commodity=None):
    """Analyze forecasts across all commodities and markets"""
    results = {}
    commodities_to_analyze = [commodity] if commodity else COMMODITIES
    
    for c in commodities_to_analyze:
        results[c] = {}
        for m in MARKETS[:5]:  # Limit to main markets
            forecast = get_market_forecast(c, m, 7)
            if forecast and len(forecast) > 0:
                results[c][m] = {
                    'current_price': forecast[0]['predicted_price'],
                    'forecast_7d': forecast[-1]['predicted_price'],
                    'change_percent': forecast[-1]['change_percent'],
                    'trend': forecast[-1]['trend'],
                    'recommendation': get_forecast_recommendations(c, m)
                }
    
    return results

def get_historical_prices(commodity, market, days=30):
    """Get historical prices for a commodity and market"""
    try:
        conn = get_db()
        if conn is None:
            return []
        
        cur = conn.cursor()
        cur.execute("""
            SELECT price, recorded_at FROM market_prices
            WHERE commodity=? AND market LIKE ? AND verified=1
            ORDER BY recorded_at DESC LIMIT ?
        """, (commodity, f"%{market}%", days))
        rows = cur.fetchall()
        conn.close()
        
        return [{'price': r['price'], 'date': r['recorded_at']} for r in rows]
    except Exception as e:
        logger.error(f"Error fetching historical prices: {e}")
        return []

# =========================================================
# API COMPATIBLE FUNCTIONS
# =========================================================

def get_forecast_api(commodity, market, days):
    """API-compatible forecast function"""
    return get_market_forecast(commodity, market, days)

# Load model on module import
print("📊 Loading price forecast model...")
load_model()
print("=" * 50)