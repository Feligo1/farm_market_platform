# enhanced_forecast.py
"""
Advanced Machine Learning Models for Price Forecasting
- ARIMA (AutoRegressive Integrated Moving Average)
- LSTM (Long Short-Term Memory Neural Network)
- Ensemble Model (Combines multiple models)
- Model retraining pipeline
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Try importing advanced ML libraries
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("⚠️ statsmodels not available. ARIMA disabled.")

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn not available. Ensemble models disabled.")

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = False  # Set to True if tensorflow is installed
    # Note: TensorFlow is heavy, only enable if needed
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ TensorFlow not available. LSTM disabled.")

import logging
logger = logging.getLogger(__name__)

class EnhancedPriceForecast:
    """
    Advanced price forecasting with multiple ML models
    """
    
    def __init__(self, db_path: str = "farm_market.db"):
        self.db_path = db_path
        self.models = {}
        self.model_metrics = {}
        self.models_dir = "models/enhanced"
        os.makedirs(self.models_dir, exist_ok=True)
        
    def prepare_time_series_data(self, commodity: str, market: str, 
                                   days_history: int = 90) -> pd.Series:
        """Prepare time series data from database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        
        # Get historical prices
        query = """
            SELECT date(recorded_at) as date, AVG(price) as avg_price
            FROM market_prices
            WHERE commodity = ? AND market LIKE ? AND verified = 1
            GROUP BY date(recorded_at)
            ORDER BY date ASC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[commodity, f'%{market}%', days_history])
        conn.close()
        
        if df.empty:
            # Generate synthetic data for demo
            dates = pd.date_range(end=datetime.now(), periods=days_history, freq='D')
            base_price = self._get_base_price(commodity)
            prices = self._generate_synthetic_prices(base_price, days_history)
            return pd.Series(prices, index=dates)
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df['avg_price']
    
    def _get_base_price(self, commodity: str) -> float:
        """Get base price for commodity"""
        base_prices = {
            'Maize': 6.80, 'Tomatoes': 8.50, 'Beans': 12.50,
            'Groundnuts': 18.00, 'Rice': 9.00, 'Soybeans': 15.00,
            'Cassava': 4.50, 'Sweet Potatoes': 6.50, 'Onions': 7.00,
            'Cabbage': 5.00, 'Chicken': 35.00, 'Beef': 45.00
        }
        return base_prices.get(commodity, 10.00)
    
    def _generate_synthetic_prices(self, base_price: float, days: int) -> List[float]:
        """Generate synthetic price data for training"""
        prices = []
        current = base_price
        for i in range(days):
            # Add seasonality and random noise
            seasonal = 0.05 * np.sin(2 * np.pi * i / 365)
            trend = 0.0001 * i
            noise = np.random.normal(0, 0.02)
            change = seasonal + trend + noise
            current = current * (1 + change)
            prices.append(max(2, current))
        return prices
    
    # =========================================================
    # ARIMA MODEL
    # =========================================================
    
    def train_arima(self, commodity: str, market: str) -> Dict:
        """Train ARIMA model for price forecasting"""
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels not available"}
        
        try:
            # Get time series data
            series = self.prepare_time_series_data(commodity, market, days_history=90)
            
            if len(series) < 30:
                return {"error": "Insufficient data"}
            
            # Check stationarity
            adf_result = adfuller(series.dropna())
            is_stationary = adf_result[1] < 0.05
            
            # Determine differencing order
            d = 0 if is_stationary else 1
            
            # Fit ARIMA model (auto-select p, q using AIC)
            best_aic = float('inf')
            best_order = None
            best_model = None
            
            for p in range(0, 4):
                for q in range(0, 4):
                    try:
                        model = ARIMA(series, order=(p, d, q))
                        fitted = model.fit()
                        if fitted.aic < best_aic:
                            best_aic = fitted.aic
                            best_order = (p, d, q)
                            best_model = fitted
                    except:
                        continue
            
            if best_model is None:
                return {"error": "Could not fit ARIMA model"}
            
            # Generate forecast
            forecast_steps = 30
            forecast = best_model.forecast(steps=forecast_steps)
            
            # Calculate metrics
            predictions = best_model.predict(start=len(series)-30, end=len(series)-1)
            actual = series[-30:]
            
            mae = mean_absolute_error(actual, predictions)
            rmse = np.sqrt(mean_squared_error(actual, predictions))
            mape = np.mean(np.abs((actual - predictions) / actual)) * 100
            
            # Save model
            model_path = f"{self.models_dir}/arima_{commodity}_{market}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(best_model, f)
            
            metrics = {
                "model": "ARIMA",
                "order": best_order,
                "aic": best_aic,
                "mae": mae,
                "rmse": rmse,
                "mape": mape,
                "accuracy": max(0, 100 - mape)
            }
            
            self.model_metrics[f"arima_{commodity}_{market}"] = metrics
            
            return {
                "success": True,
                "forecast": forecast.tolist(),
                "metrics": metrics,
                "is_stationary": is_stationary
            }
            
        except Exception as e:
            logger.error(f"ARIMA training error: {e}")
            return {"error": str(e)}
    
    # =========================================================
    # LSTM MODEL (Neural Network)
    # =========================================================
    
    def prepare_lstm_data(self, data: np.ndarray, lookback: int = 30):
        """Prepare data for LSTM model"""
        X, y = [], []
        for i in range(lookback, len(data)):
            X.append(data[i-lookback:i])
            y.append(data[i])
        return np.array(X), np.array(y)
    
    def train_lstm(self, commodity: str, market: str) -> Dict:
        """Train LSTM neural network for price forecasting"""
        if not TENSORFLOW_AVAILABLE:
            return {"error": "TensorFlow not available. Use pip install tensorflow"}
        
        try:
            # Get time series data
            series = self.prepare_time_series_data(commodity, market, days_history=365)
            
            if len(series) < 100:
                return {"error": "Insufficient data for LSTM (need 100+ days)"}
            
            # Normalize data
            data = series.values.reshape(-1, 1)
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Prepare sequences
            lookback = 30
            X, y = self.prepare_lstm_data(data_scaled.flatten(), lookback)
            
            # Split data
            split = int(0.8 * len(X))
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            # Reshape for LSTM [samples, time steps, features]
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mse')
            
            # Train model
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            
            history = model.fit(
                X_train, y_train,
                epochs=100,
                batch_size=32,
                validation_split=0.1,
                callbacks=[early_stop],
                verbose=0
            )
            
            # Make predictions
            train_predict = model.predict(X_train, verbose=0)
            test_predict = model.predict(X_test, verbose=0)
            
            # Inverse transform
            train_predict = scaler.inverse_transform(train_predict)
            y_train_actual = scaler.inverse_transform(y_train.reshape(-1, 1))
            test_predict = scaler.inverse_transform(test_predict)
            y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))
            
            # Generate future forecast
            last_sequence = data_scaled[-lookback:].reshape(1, lookback, 1)
            future_forecast = []
            for _ in range(30):
                next_pred = model.predict(last_sequence, verbose=0)
                future_forecast.append(scaler.inverse_transform(next_pred)[0, 0])
                last_sequence = np.append(last_sequence[:, 1:, :], next_pred.reshape(1, 1, 1), axis=1)
            
            # Calculate metrics
            mae = mean_absolute_error(y_test_actual, test_predict)
            rmse = np.sqrt(mean_squared_error(y_test_actual, test_predict))
            mape = np.mean(np.abs((y_test_actual - test_predict) / y_test_actual)) * 100
            
            # Save model
            model_path = f"{self.models_dir}/lstm_{commodity}_{market}.h5"
            model.save(model_path)
            
            # Save scaler
            scaler_path = f"{self.models_dir}/lstm_scaler_{commodity}_{market}.pkl"
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            metrics = {
                "model": "LSTM",
                "layers": "2 LSTM layers + Dropout",
                "final_loss": history.history['loss'][-1],
                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "accuracy": max(0, 100 - mape)
            }
            
            self.model_metrics[f"lstm_{commodity}_{market}"] = metrics
            
            return {
                "success": True,
                "forecast": future_forecast,
                "metrics": metrics,
                "training_history": {
                    "loss": history.history['loss'][:10],
                    "val_loss": history.history['val_loss'][:10]
                }
            }
            
        except Exception as e:
            logger.error(f"LSTM training error: {e}")
            return {"error": str(e)}
    
    # =========================================================
    # ENSEMBLE MODEL (Combines multiple models)
    # =========================================================
    
    def train_ensemble(self, commodity: str, market: str) -> Dict:
        """Train ensemble model combining ARIMA and ML models"""
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not available"}
        
        try:
            # Get time series data
            series = self.prepare_time_series_data(commodity, market, days_history=180)
            
            if len(series) < 60:
                return {"error": "Insufficient data"}
            
            # Create features from lagged values
            df = pd.DataFrame({'price': series})
            for lag in range(1, 8):
                df[f'lag_{lag}'] = df['price'].shift(lag)
            
            # Add rolling statistics
            df['rolling_mean_7'] = df['price'].rolling(window=7).mean()
            df['rolling_std_7'] = df['price'].rolling(window=7).std()
            df['rolling_mean_30'] = df['price'].rolling(window=30).mean()
            
            # Add time features
            df['day_of_week'] = df.index.dayofweek
            df['day_of_month'] = df.index.day
            df['month'] = df.index.month
            
            # Drop NaN values
            df = df.dropna()
            
            # Prepare features and target
            feature_cols = ['lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_5', 'lag_6', 'lag_7',
                           'rolling_mean_7', 'rolling_std_7', 'rolling_mean_30',
                           'day_of_week', 'day_of_month', 'month']
            
            X = df[feature_cols].values
            y = df['price'].values
            
            # Split data
            split = int(0.8 * len(X))
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            # Train multiple models
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
            }
            
            predictions = {}
            metrics = {}
            
            for name, model in models.items():
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                predictions[name] = pred
                
                mae = mean_absolute_error(y_test, pred)
                rmse = np.sqrt(mean_squared_error(y_test, pred))
                mape = np.mean(np.abs((y_test - pred) / y_test)) * 100
                r2 = r2_score(y_test, pred)
                
                metrics[name] = {
                    "mae": mae,
                    "rmse": rmse,
                    "mape": mape,
                    "r2": r2,
                    "accuracy": max(0, 100 - mape)
                }
                
                # Save model
                model_path = f"{self.models_dir}/{name}_{commodity}_{market}.pkl"
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Ensemble prediction (average of all models)
            ensemble_pred = np.mean(list(predictions.values()), axis=0)
            ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
            ensemble_rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
            ensemble_mape = np.mean(np.abs((y_test - ensemble_pred) / y_test)) * 100
            
            metrics['ensemble'] = {
                "mae": ensemble_mae,
                "rmse": ensemble_rmse,
                "mape": ensemble_mape,
                "accuracy": max(0, 100 - ensemble_mape)
            }
            
            # Generate future forecast (next 30 days)
            last_row = df.iloc[-1:][feature_cols].values
            future_forecast = []
            current_features = last_row.copy()
            
            for _ in range(30):
                pred_forest = models['random_forest'].predict(current_features)[0]
                pred_gb = models['gradient_boosting'].predict(current_features)[0]
                ensemble_pred_day = (pred_forest + pred_gb) / 2
                future_forecast.append(ensemble_pred_day)
                
                # Update features for next prediction
                current_features[0][0] = ensemble_pred_day  # Update lag_1
                for i in range(1, 7):
                    current_features[0][i] = current_features[0][i-1]  # Shift lags
            
            self.model_metrics[f"ensemble_{commodity}_{market}"] = metrics
            
            return {
                "success": True,
                "forecast": future_forecast,
                "metrics": metrics,
                "models_used": list(models.keys())
            }
            
        except Exception as e:
            logger.error(f"Ensemble training error: {e}")
            return {"error": str(e)}
    
    # =========================================================
    # MODEL RETRAINING PIPELINE
    # =========================================================
    
    def retrain_all_models(self, commodity: str = None, market: str = None) -> Dict:
        """Retrain all models for a commodity/market"""
        results = {}
        
        commodities = [commodity] if commodity else ['Maize', 'Tomatoes', 'Beans', 'Groundnuts', 'Rice']
        markets_list = [market] if market else ['Lusaka', 'Kabwe', 'Ndola']
        
        for c in commodities:
            for m in markets_list:
                key = f"{c}_{m}"
                results[key] = {}
                
                # Train ARIMA
                if STATSMODELS_AVAILABLE:
                    arima_result = self.train_arima(c, m)
                    results[key]['arima'] = arima_result
                
                # Train Ensemble
                if SKLEARN_AVAILABLE:
                    ensemble_result = self.train_ensemble(c, m)
                    results[key]['ensemble'] = ensemble_result
                
                # Train LSTM (optional - heavy)
                # if TENSORFLOW_AVAILABLE:
                #     lstm_result = self.train_lstm(c, m)
                #     results[key]['lstm'] = lstm_result
        
        # Save all metrics
        self.save_metrics()
        
        return results
    
    def save_metrics(self):
        """Save model metrics to file"""
        metrics_path = f"{self.models_dir}/model_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.model_metrics, f, indent=2)
        logger.info(f"Model metrics saved to {metrics_path}")
    
    def get_best_model(self, commodity: str, market: str) -> Dict:
        """Get the best performing model for a commodity"""
        best_model = None
        best_accuracy = 0
        
        for model_name, metrics in self.model_metrics.items():
            if commodity in model_name and market in model_name:
                accuracy = metrics.get('accuracy', 0)
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_model = {
                        "name": model_name,
                        "accuracy": accuracy,
                        "metrics": metrics
                    }
        
        return best_model or {"name": "fallback", "accuracy": 70}
    
    def get_model_performance_report(self) -> Dict:
        """Generate comprehensive model performance report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "models_available": {
                "arima": STATSMODELS_AVAILABLE,
                "ensemble": SKLEARN_AVAILABLE,
                "lstm": TENSORFLOW_AVAILABLE
            },
            "model_metrics": self.model_metrics,
            "summary": {
                "total_models_trained": len(self.model_metrics),
                "best_accuracy": 0,
                "worst_accuracy": 100,
                "average_accuracy": 0
            }
        }
        
        accuracies = []
        for metrics in self.model_metrics.values():
            acc = metrics.get('accuracy', 0)
            if isinstance(acc, (int, float)):
                accuracies.append(acc)
        
        if accuracies:
            report['summary']['best_accuracy'] = max(accuracies)
            report['summary']['worst_accuracy'] = min(accuracies)
            report['summary']['average_accuracy'] = sum(accuracies) / len(accuracies)
        
        return report


# Initialize global instance
enhanced_forecaster = EnhancedPriceForecast()