# test_ussd_flow.py
import requests
import time

BASE_URL = "http://127.0.0.1:5001"

def test_ussd_flow():
    """Test complete USSD flow"""
    print("=" * 60)
    print("📱 TESTING USSD WEB INTERFACE")
    print("=" * 60)
    
    test_cases = [
        ("Initial", ""),
        ("Market Prices Menu", "1"),
        ("Maize Prices", "1*1"),
        ("Tomatoes Prices", "1*2"),
        ("Price Forecast Menu", "2"),
        ("Maize Forecast", "2*1"),
        ("Find Buyers Menu", "3"),
        ("Maize Buyers", "3*1"),
        ("Weather Info", "4"),
        ("Farming Tips", "5")
    ]
    
    for test_name, ussd_text in test_cases:
        print(f"\n🧪 Testing: {test_name}")
        print(f"   USSD Input: '{ussd_text}'")
        
        try:
            url = f"{BASE_URL}/ussd/test"
            if ussd_text:
                url += f"?text={ussd_text}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Extract first few lines
                lines = response_text.split('\n')[:4]
                preview = '\n'.join(lines)
                
                print(f"   ✅ Success")
                print(f"   Response preview: {preview}...")
                
                # Check if it's END or CON response
                if response_text.startswith("END"):
                    print(f"   Type: END session")
                elif response_text.startswith("CON"):
                    print(f"   Type: CONtinue session")
                else:
                    print(f"   Type: Unknown format")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
        except Exception as e:
            print(f"   ❌ Other error: {e}")
        
        time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 60)
    print("🌐 Testing Web Interface Pages:")
    print("=" * 60)
    
    pages = [
        ("Home", "/"),
        ("Status", "/ussd/status"),
        ("Sessions", "/ussd/sessions"),
        ("Stats", "/ussd/stats")
    ]
    
    for page_name, endpoint in pages:
        print(f"\n📄 Testing {page_name}: {BASE_URL}{endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Accessible")
                if endpoint == "/":
                    print(f"   Type: HTML page")
                else:
                    data = response.json()
                    print(f"   Type: JSON response")
                    if page_name == "Status":
                        print(f"   Service: {data.get('status', 'unknown')}")
                    elif page_name == "Stats":
                        print(f"   Active sessions: {data.get('sessions', {}).get('active', 0)}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_ussd_flow()