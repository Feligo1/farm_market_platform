# hotfix.py - Run this while app.py is running
import requests
import time

def test_endpoints():
    """Test all endpoints after fixes"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing endpoints after fixes...")
    
    endpoints = [
        ("/api/status", "GET"),
        ("/api/prices/real?limit=5", "GET"),
        ("/api/buyers?limit=3", "GET"),
        ("/api/forecast/real?commodity=Maize", "GET"),
        ("/ussd/test", "GET"),
        ("/ussd/test?text=1", "GET"),
        ("/ussd/test?text=1*1", "GET"),
    ]
    
    for endpoint, method in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🔍 Testing {method} {endpoint}")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Success ({response.status_code})")
                
                # Show response preview for some endpoints
                if endpoint == "/api/prices/real":
                    data = response.json()
                    prices = data.get('prices', [])
                    if prices:
                        print(f"   📊 Prices: {len(prices)} records")
                        for price in prices[:2]:
                            print(f"      • {price.get('commodity')}: {price.get('price')} at {price.get('market')}")
                
                elif endpoint.startswith("/ussd"):
                    data = response.json()
                    resp_text = data.get('response', '')
                    if "CON " in resp_text:
                        print(f"   📱 USSD: Continue session")
                        print(f"      Menu: {resp_text[:50]}...")
                    elif "END " in resp_text:
                        print(f"   📱 USSD: End session")
                        print(f"      Result: {resp_text[:50]}...")
                
            elif response.status_code == 404:
                print(f"   ❌ Not found ({response.status_code})")
            elif response.status_code == 500:
                print(f"   ❌ Server error ({response.status_code})")
                try:
                    error_data = response.json()
                    print(f"      Error: {error_data.get('error', 'Unknown')[:100]}")
                except:
                    print(f"      Error: Could not parse error response")
            else:
                print(f"   ⚠️  Unexpected: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Could not connect to server")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("📋 RECOMMENDED ACTIONS:")
    print("=" * 60)
    print("1. If /api/prices/real still fails with 'no such column: region'")
    print("   Run: python fix_issues.py")
    print("2. If zambian_data.py has 'time' error")
    print("   Check zambian_data.py imports section")
    print("3. Restart app.py after all fixes")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()
    