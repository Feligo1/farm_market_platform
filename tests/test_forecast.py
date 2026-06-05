import unittest
from forecast import simple_price_forecast, advanced_price_forecast
import pandas as pd
from datetime import datetime

class TestForecast(unittest.TestCase):
    
    def test_simple_forecast(self):
        # Create test data
        data = pd.DataFrame({
            'price': [100, 102, 105, 103, 107],
            'recorded_at': [datetime.now().isoformat() for _ in range(5)]
        })
        
        forecast = simple_price_forecast(data, 3)
        self.assertEqual(len(forecast), 3)
        self.assertIn('predicted_price', forecast[0])
    
    def test_advanced_forecast(self):
        data = pd.DataFrame({
            'price': [100, 102, 105, 103, 107, 110, 108, 112],
            'recorded_at': [datetime.now().isoformat() for _ in range(8)]
        })
        
        forecast = advanced_price_forecast(data, 3)
        self.assertEqual(len(forecast), 3)