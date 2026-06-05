# test_logistics.py
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    """Test the API endpoints"""
    print("🧪 Testing FarmConnect API...")
    
    # Test status endpoint
    print("\n1. Testing status endpoint...")
    response = requests.get(f"{BASE_URL}/api/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"📊 Logistics available: {data.get('services', {}).get('logistics')}")
    else:
        print(f"❌ Status test failed: {response.status_code}")
    
    # Test login
    print("\n2. Testing login...")
    login_data = {
        "username": "farmer1",
        "password": "farmer123"
    }
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Login successful")
        print(f"🔑 Token: {token[:50]}...")
        
        # Test logistics endpoints with token
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\n3. Testing storage facilities...")
        response = requests.get(f"{BASE_URL}/api/logistics/storage/facilities", headers=headers)
        if response.status_code == 200:
            data = response.json()
            facilities = data.get('facilities', [])
            print(f"✅ Found {len(facilities)} storage facilities")
            if facilities:
                print(f"📦 First facility: {facilities[0].get('name')}")
        else:
            print(f"❌ Storage facilities test failed: {response.status_code}")
        
        # Test creating a delivery request
        print("\n4. Testing delivery request...")
        delivery_data = {
            "farmer_id": data.get('user', {}).get('id'),
            "pickup_location": "Lusaka Farm, Chongwe Road",
            "delivery_location": "Lusaka Central Market",
            "commodity": "Tomatoes",
            "quantity": 500,
            "pickup_date": "2024-01-15",
            "temperature_required": True,
            "min_temperature": 5,
            "max_temperature": 10
        }
        response = requests.post(f"{BASE_URL}/api/logistics/request", 
                                json=delivery_data, headers=headers)
        if response.status_code == 200:
            delivery_response = response.json()
            print(f"✅ Delivery request created")
            print(f"📋 Request ID: {delivery_response.get('request_id')}")
            print(f"💰 Quoted price: ZMW {delivery_response.get('quoted_price')}")
            
            # Test getting available transporters
            if delivery_response.get('request_id'):
                print("\n5. Testing available transporters...")
                time.sleep(2)  # Wait a bit
                params = {"request_id": delivery_response.get('request_id')}
                response = requests.get(f"{BASE_URL}/api/logistics/transports/available", 
                                       headers=headers, params=params)
                if response.status_code == 200:
                    transporters_data = response.json()
                    transporters = transporters_data.get('transporters', [])
                    print(f"✅ Found {len(transporters)} available transporters")
                    if transporters:
                        print(f"🚚 First transporter: {transporters[0].get('name')}")
                        print(f"📞 Phone: {transporters[0].get('phone')}")
                else:
                    print(f"❌ Transporters test failed: {response.status_code}")
        
        else:
            print(f"❌ Delivery request test failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    else:
        print(f"❌ Login test failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test public endpoints
    print("\n6. Testing public endpoints...")
    
    # Market prices
    response = requests.get(f"{BASE_URL}/api/prices/real")
    if response.status_code == 200:
        data = response.json()
        prices = data.get('prices', [])
        print(f"✅ Market prices: {len(prices)} records")
    else:
        print(f"❌ Market prices test failed: {response.status_code}")
    
    # Buyers
    response = requests.get(f"{BASE_URL}/api/buyers")
    if response.status_code == 200:
        data = response.json()
        buyers = data.get('buyers', [])
        print(f"✅ Buyers: {len(buyers)} records")
    else:
        print(f"❌ Buyers test failed: {response.status_code}")
    
    print("\n" + "="*50)
    print("🎉 All tests completed!")

if __name__ == "__main__":
    test_api()