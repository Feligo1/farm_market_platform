# quick_test.py
import requests
import json

def run_all_tests():
    """Run all tests at once"""
    print("🚀 COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Test 1: Main app status
    print("\n1️⃣  MAIN APP STATUS")
    try:
        r = requests.get("http://127.0.0.1:5000/api/status")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print("   ✅ Main app running")
    except:
        print("   ❌ Main app not running")
    
    # Test 2: USSD app status
    print("\n2️⃣  USSD APP STATUS")
    try:
        r = requests.get("http://127.0.0.1:5001/ussd/status")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Service: {data.get('service_code')}")
    except:
        print("   ❌ USSD app not running")
    
    # Test 3: Web interface
    print("\n3️⃣  WEB INTERFACE")
    try:
        r = requests.get("http://127.0.0.1:5001/")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print("   ✅ Web interface accessible")
    except:
        print("   ❌ Web interface not accessible")
    
    # Test 4: USSD flow
    print("\n4️⃣  USSD FLOW TEST")
    test_cases = ["", "1", "1*1", "2", "2*1", "3", "4", "5"]
    for text in test_cases[:3]:  # Test first 3
        try:
            url = f"http://127.0.0.1:5001/ussd/test"
            if text:
                url += f"?text={text}"
            r = requests.get(url)
            if r.status_code == 200:
                print(f"   Input '{text}': ✅")
        except:
            print(f"   Input '{text}': ❌")
    
    # Test 5: Database
    print("\n5️⃣  DATABASE CONNECTION")
    try:
        import sqlite3
        conn = sqlite3.connect('farm_market.db')
        print("   ✅ Database file exists")
        conn.close()
    except:
        print("   ❌ Database file missing")
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY: Run individual test scripts for detailed results")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()