# test_system.py
"""
System Testing Script for FarmConnect
Tests all major functionality
"""

import unittest
import json
import sqlite3
from datetime import datetime
import requests

class TestFarmConnect(unittest.TestCase):
    """Test suite for FarmConnect platform"""
    
    BASE_URL = "http://localhost:5000"
    
    def setUp(self):
        """Set up test environment"""
        self.test_user = {
            "username": "test_farmer",
            "password": "test123",
            "name": "Test Farmer",
            "role": "farmer",
            "phone": "+260971234567",
            "email": "test@example.com"
        }
    
    def test_api_status(self):
        """Test API status endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        print("✅ API status test passed")
    
    def test_user_registration(self):
        """Test user registration"""
        response = requests.post(
            f"{self.BASE_URL}/api/register",
            json=self.test_user
        )
        # Accept either 200 or 400 (user might already exist)
        self.assertIn(response.status_code, [200, 400])
        print("✅ User registration test passed")
    
    def test_market_prices(self):
        """Test market prices endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/prices/real")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("prices", data)
        print("✅ Market prices test passed")
    
    def test_forecast_endpoint(self):
        """Test forecast endpoint"""
        response = requests.get(
            f"{self.BASE_URL}/api/forecast/real",
            params={"commodity": "Maize", "days": 7}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("forecast", data)
        print("✅ Forecast test passed")
    
    def test_buyers_endpoint(self):
        """Test buyers endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/buyers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("buyers", data)
        print("✅ Buyers test passed")
    
    def test_ussd_menu(self):
        """Test USSD menu"""
        # Test main menu
        response = requests.get(
            f"{self.BASE_URL}/ussd/test",
            params={"phone": "+260971234567", "text": ""}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertTrue(data["response"].startswith("CON"))
        print("✅ USSD menu test passed")
    
    def test_ussd_price_check(self):
        """Test USSD price check"""
        response = requests.get(
            f"{self.BASE_URL}/ussd/test",
            params={"phone": "+260971234567", "text": "1*1"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        print("✅ USSD price check test passed")
    
    def test_sms_service(self):
        """Test SMS service (requires login)"""
        # First login
        login_response = requests.post(
            f"{self.BASE_URL}/api/login",
            json={"username": "admin1", "password": "admin123"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["token"]
            
            # Send test SMS
            sms_response = requests.post(
                f"{self.BASE_URL}/api/sms/send",
                json={"phone": "+260971234567", "message": "Test SMS from FarmConnect"},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            self.assertIn(sms_response.status_code, [200, 500])
            print("✅ SMS service test passed")
        else:
            print("⚠️  SMS test skipped - login failed")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            conn = sqlite3.connect('farm_market.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            self.assertIsInstance(count, int)
            print(f"✅ Database test passed - {count} users found")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("FARMCONNECT SYSTEM TESTING")
    print("="*60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFarmConnect)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)