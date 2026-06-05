#!/usr/bin/env python3
"""
Train Machine Learning Model for Zambian Commodity Price Prediction
Fixed version - handles shape mismatches correctly
"""

import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# =========================================================
# CONFIGURATION
# =========================================================

MODEL_DIR = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

COMMODITIES = ['Maize', 'Tomatoes', 'Beans', 'Groundnuts', 'Rice', 'Soybeans']
MARKETS = ['Lusaka', 'Kitwe', 'Ndola', 'Livingstone', 'Chipata']

# Real Zambian base prices (ZMW/kg)
BASE_PRICES = {
    'Maize': 6.80,
    'Tomatoes': 8.50,
    'Beans': 12.50,
    'Groundnuts': 18.00,
    'Rice': 9.00,
    'Soybeans': 15.00
}

# Market adjustment factors
MARKET_FACTORS = {
    'Lusaka': 1.00,
    'Kitwe': 1.02,
    'Ndola': 1.01,
    'Livingstone': 0.98,
    'Chipata': 0.95
}

# Seasonal factors (monthly multipliers based on Zambian growing seasons)
SEASONAL_FACTORS = {
    1: 0.95, 2: 0.92, 3: 0.90, 4: 0.93, 5: 0.97, 6: 1.02,
    7: 1.08, 8: 1.12, 9: 1.10, 10: 1.05, 11: 1.00, 12: 0.98
}

# =========================================================
# GENERATE HISTORICAL TRAINING DATA (2020-2026)
# =========================================================

def generate_historical_data():
    """Generate realistic historical price data for training"""
    print("\n📈 Generating historical price data (2020-2026)...")
    
    data = []
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2026, 4, 1)
    
    current_date = start_date
    while current_date <= end_date:
        month = current_date.month
        year = current_date.year
        
        # Yearly inflation trend (3% per year)
        year_trend = 1 + (year - 2020) * 0.03
        
        for commodity in COMMODITIES:
            base = BASE_PRICES[commodity]
            
            for market in MARKETS:
                # Calculate price with all factors
                seasonal = SEASONAL_FACTORS[month]
                market_mult = MARKET_FACTORS[market]
                
                # Add realistic random noise
                noise = np.random.normal(1, 0.05)
                
                # Calculate final price
                price = base * seasonal * market_mult * year_trend * noise
                
                # Apply commodity-specific constraints
                if commodity == 'Maize' and price < 5:
                    price = 5 + np.random.rand() * 2
                elif commodity == 'Tomatoes' and price > 25:
                    price = 25 - np.random.rand() * 5
                elif commodity == 'Groundnuts' and price > 30:
                    price = 30 - np.random.rand() * 3
                
                data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'year': year,
                    'month': month,
                    'day_of_week': current_date.weekday(),
                    'day_of_month': current_date.day,
                    'quarter': (month - 1) // 3 + 1,
                    'commodity': commodity,
                    'market': market,
                    'price': round(price, 2),
                    'market_factor': market_mult,
                    'seasonal_factor': seasonal
                })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    df = pd.DataFrame(data)
    print(f"   ✅ Generated {len(df)} training records")
    print(f"   📅 Date range: {df['date'].min()} to {df['date'].max()}")
    return df

# =========================================================
# FEATURE ENGINEERING - FIXED VERSION
# =========================================================

def create_features(df):
    """Create features for ML model - FIXED shape mismatch"""
    print("\n🔧 Creating features...")
    
    # Sort for lag features
    df = df.sort_values(['commodity', 'market', 'date']).copy()
    
    # Create commodity and market dummy variables
    commodity_dummies = pd.get_dummies(df['commodity'], prefix='comm')
    market_dummies = pd.get_dummies(df['market'], prefix='market')
    
    # Cyclical features for month (so Dec and Jan are close)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    # Cyclical features for day of week
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Add lag features (previous month prices)
    df['price_lag_1'] = df.groupby(['commodity', 'market'])['price'].shift(1)
    df['price_lag_2'] = df.groupby(['commodity', 'market'])['price'].shift(2)
    df['price_lag_3'] = df.groupby(['commodity', 'market'])['price'].shift(3)
    
    # Rolling averages
    df['price_ma_3'] = df.groupby(['commodity', 'market'])['price'].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
    df['price_ma_6'] = df.groupby(['commodity', 'market'])['price'].transform(
        lambda x: x.rolling(6, min_periods=1).mean()
    )
    
    # Price momentum
    df['price_momentum'] = df.groupby(['commodity', 'market'])['price'].pct_change(periods=3)
    
    # Normalized year
    df['year_norm'] = (df['year'] - df['year'].min()) / (df['year'].max() - df['year'].min())
    
    # FIX: Drop rows with NaN values BEFORE creating feature matrix
    # This ensures X and y have the same number of samples
    original_len = len(df)
    df = df.dropna()
    dropped = original_len - len(df)
    if dropped > 0:
        print(f"   ⚠️ Dropped {dropped} rows with NaN values (due to lag features)")
    
    # Feature columns
    feature_cols = [
        'year', 'month_sin', 'month_cos', 'dow_sin', 'dow_cos',
        'quarter', 'year_norm', 
        'price_lag_1', 'price_lag_2', 'price_lag_3',
        'price_ma_3', 'price_ma_6', 'price_momentum',
        'market_factor', 'seasonal_factor'
    ]
    
    # Combine features
    X = pd.concat([
        df[feature_cols].reset_index(drop=True),
        commodity_dummies.loc[df.index].reset_index(drop=True),
        market_dummies.loc[df.index].reset_index(drop=True)
    ], axis=1)
    
    y = df['price'].values
    
    print(f"   ✅ Features shape: {X.shape}")
    print(f"   📊 Target shape: {y.shape}")
    print(f"   ✅ Matched: {X.shape[0]} = {y.shape[0]}")
    
    return X, y, df, feature_cols

# =========================================================
# TRAIN MODELS
# =========================================================

def train_models():
    """Train multiple models and save the best one"""
    
    print("\n" + "="*60)
    print("🌽 FARMConnect - Price Prediction Model Training")
    print("="*60)
    
    # Generate data
    df = generate_historical_data()
    
    # Create features
    X, y, df_features, feature_cols = create_features(df)
    
    # Split data (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )
    
    print(f"\n📊 Training set: {len(X_train):,} samples")
    print(f"📊 Test set: {len(X_test):,} samples")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Models to try
    models = {
        'Random Forest': RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),
        'Gradient Boosting': GradientBoostingRegressor(
            n_estimators=80,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=5,
            random_state=42
        ),
        'Ridge Regression': Ridge(alpha=1.0),
        'Linear Regression': LinearRegression()
    }
    
    results = []
    best_model = None
    best_score = -float('inf')
    best_name = ""
    
    print("\n" + "-"*60)
    print("📈 Training Results:")
    print("-"*60)
    
    for name, model in models.items():
        print(f"\n🔄 Training {name}...")
        
        # Train
        model.fit(X_train_scaled, y_train)
        
        # Predict
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation (use smaller subset for faster training)
        try:
            cv_scores = cross_val_score(model, X_train_scaled[:500], y_train[:500], cv=3, scoring='r2')
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
        except:
            cv_mean = 0
            cv_std = 0
        
        print(f"   ✅ MAE:  ZMW {mae:.3f}/kg")
        print(f"   ✅ RMSE: ZMW {rmse:.3f}/kg")
        print(f"   ✅ R²:   {r2:.4f}")
        print(f"   ✅ CV:   {cv_mean:.4f} (±{cv_std:.4f})")
        
        results.append({
            'name': name,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'cv_mean': cv_mean,
            'model': model
        })
        
        if r2 > best_score:
            best_score = r2
            best_model = model
            best_name = name
    
    # Display best model
    print("\n" + "="*60)
    print(f"🏆 BEST MODEL: {best_name}")
    print(f"   R² Score: {best_score:.4f}")
    print(f"   MAE: {min(r['mae'] for r in results):.3f} ZMW/kg")
    print("="*60)
    
    # Save model and preprocessing objects
    model_path = os.path.join(MODEL_DIR, 'price_forecast_model.pkl')
    scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
    features_path = os.path.join(MODEL_DIR, 'feature_columns.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    with open(features_path, 'wb') as f:
        pickle.dump(X.columns.tolist(), f)
    
    print(f"\n💾 Model saved to: {model_path}")
    print(f"💾 Scaler saved to: {scaler_path}")
    print(f"💾 Features saved to: {features_path}")
    
    # Feature importance (for tree-based models)
    if hasattr(best_model, 'feature_importances_'):
        print("\n📊 Top 10 Most Important Features:")
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]
        
        for i, idx in enumerate(indices, 1):
            print(f"   {i}. {X.columns[idx]}: {importances[idx]:.4f}")
    
    return best_model, scaler, X.columns.tolist()

# =========================================================
# TEST PREDICTION
# =========================================================

def test_prediction(model, scaler, feature_cols):
    """Test the trained model with sample predictions"""
    
    print("\n" + "="*60)
    print("🔮 Sample Price Predictions")
    print("="*60)
    
    # Get current date info
    now = datetime.now()
    month = now.month
    year = now.year
    
    test_cases = [
        ('Maize', 'Lusaka'),
        ('Maize', 'Kitwe'),
        ('Tomatoes', 'Lusaka'),
        ('Beans', 'Ndola'),
        ('Groundnuts', 'Chipata'),
        ('Rice', 'Livingstone')
    ]
    
    for commodity, market in test_cases:
        # Build feature vector
        base_price = BASE_PRICES[commodity]
        market_factor = MARKET_FACTORS.get(market, 1.0)
        seasonal_factor = SEASONAL_FACTORS.get(month, 1.0)
        
        features = {
            'year': year,
            'month_sin': np.sin(2 * np.pi * month / 12),
            'month_cos': np.cos(2 * np.pi * month / 12),
            'dow_sin': np.sin(2 * np.pi * now.weekday() / 7),
            'dow_cos': np.cos(2 * np.pi * now.weekday() / 7),
            'quarter': (month - 1) // 3 + 1,
            'year_norm': (year - 2020) / 6,
            'price_lag_1': base_price,
            'price_lag_2': base_price * 0.98,
            'price_lag_3': base_price * 0.97,
            'price_ma_3': base_price,
            'price_ma_6': base_price,
            'price_momentum': 0.01,
            'market_factor': market_factor,
            'seasonal_factor': seasonal_factor,
            f'comm_{commodity}': 1,
            f'market_{market}': 1
        }
        
        # Add zeros for other commodities/markets
        for c in COMMODITIES:
            if c != commodity:
                features[f'comm_{c}'] = 0
        for m in MARKETS:
            if m != market:
                features[f'market_{m}'] = 0
        
        # Create DataFrame
        feature_df = pd.DataFrame([features])
        
        # Ensure all columns exist
        for col in feature_cols:
            if col not in feature_df.columns:
                feature_df[col] = 0
        
        feature_df = feature_df[feature_cols]
        
        # Scale and predict
        X_scaled = scaler.transform(feature_df)
        predicted_price = model.predict(X_scaled)[0]
        
        # Ensure realistic bounds
        predicted_price = max(2.0, min(predicted_price, 40.0))
        
        print(f"\n   {commodity} in {market}:")
        print(f"      Current: ZMW {base_price:.2f}/kg")
        print(f"      Predicted: ZMW {predicted_price:.2f}/kg")
        print(f"      Change: {((predicted_price - base_price) / base_price * 100):+.1f}%")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    try:
        model, scaler, feature_cols = train_models()
        test_prediction(model, scaler, feature_cols)
        
        print("\n" + "="*60)
        print("✅ Training complete! Model ready for use.")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have enough RAM")
        print("2. Try reducing the date range")
        print("3. Run: pip install --upgrade scikit-learn pandas numpy")