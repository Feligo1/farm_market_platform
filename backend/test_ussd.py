# test_ussd.py - Updated version
import requests
import json

NGROK_URL = "https://semimystically-unpummelled-lanora.ngrok-free.dev"

# Headers to bypass ngrok warning
headers = {
    'ngrok-skip-browser-warning': 'true',
    'User-Agent': 'AfricaTalking/1.0'  # Custom User-Agent also works
}

def test_ussd():
    print("=" * 60)
    print("📱 Testing FarmConnect USSD Service")
    print("=" * 60)
    print(f"Ngrok URL: {NGROK_URL}\n")
    
    # Test 1: API Status with header
    print("1️⃣ Testing API Status...")
    try:
        response = requests.get(
            f"{NGROK_URL}/api/status", 
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is online")
            print(f"   Status: {data.get('status')}")
            print(f"   SMS Service: {data.get('services', {}).get('sms')}")
        else:
            print(f"❌ API returned: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    print()
    
    # Test 2: USSD Main Menu with header
    print("2️⃣ Testing USSD Main Menu...")
    try:
        response = requests.get(
            f"{NGROK_URL}/ussd/test",
            params={"phone": "+260971234567", "text": ""},
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Main Menu Response:")
            print("-" * 40)
            print(data.get('response', ''))
            print("-" * 40)
        else:
            print(f"❌ Main menu failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Main menu test failed: {e}")
    
    print()
    print("=" * 60)
    print("✅ USSD Testing Complete!")
    print("=" * 60)
    print()
    print("📱 FOR AFRICA'S TALKING CONFIGURATION:")
    print(f"1. Update your USSD callback URL to: {NGROK_URL}/ussd")
    print("2. Important: Africa's Talking needs to send the header to bypass warning")
    print("3. If it doesn't work, use localtunnel instead:")
    print("   npm install -g localtunnel")
    print("   lt --port 5000 --subdomain farmconnect")
    print()

if __name__ == "__main__":
    test_ussd()