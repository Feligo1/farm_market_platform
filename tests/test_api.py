import unittest
import json
from app import app

class TestMarketAPI(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_prices_endpoint(self):
        response = self.app.get('/api/prices')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
    
    def test_login(self):
        response = self.app.post('/api/login', 
            json={"username": "farmer", "password": "farmer123"})
        self.assertEqual(response.status_code, 200)
    
    def test_forecast_endpoint(self):
        response = self.app.get('/api/forecast?commodity=Maize')
        self.assertEqual(response.status_code, 200)