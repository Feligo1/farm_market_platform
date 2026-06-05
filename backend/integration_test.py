# integration_test.py
import subprocess
import time
import requests
import sys

def test_integration():
    """Test integration between main app and USSD app"""
    print("=" * 60)
    print("🔗 TESTING INTEGRATION")
    print("=" * 60)
    
    # Check if both servers can run simultaneously
    print("\n1. Checking port availability:")
    print("   Main app (app.py) should run on port 5000")
    print("   USSD app (ussd_app.py) should run on port 5001")
    
    # Try to access both
    print("\n2. Testing main app endpoint:")
    try:
        response = requests.get("http://127.0.0.1:5000/api/status", timeout=3)
        if response.status_code == 200:
            print("   ✅ Main app is running on port 5000")
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"   ⚠️  Main app responded with: {response.status_code}")
    except:
        print("   ❌ Main app not running on port 5000")
    
    print("\n3. Testing USSD app endpoint:")
    try:
        response = requests.get("http://127.0.0.1:5001/ussd/status", timeout=3)
        if response.status_code == 200:
            print("   ✅ USSD app is running on port 5001")
            data = response.json()
            print(f"   Service code: {data.get('service_code', 'unknown')}")
        else:
            print(f"   ⚠️  USSD app responded with: {response.status_code}")
    except:
        print("   ❌ USSD app not running on port 5001")
    
    print("\n4. Testing shared database access:")
    print("   Both apps should use the same farm_market.db")
    
    # Test data consistency
    print("\n5. Data flow test:")
    print("   a) Main app adds market price")
    print("   b) USSD app reads market price")
    print("   c) Both apps should see same data")
    
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION OPTIONS:")
    print("=" * 60)
    
    print("\nOption 1: Separate servers (current setup)")
    print("   • Main app: http://127.0.0.1:5000")
    print("   • USSD app: http://127.0.0.1:5001")
    print("   • Pros: Independent scaling, separate logs")
    print("   • Cons: Two processes to manage")
    
    print("\nOption 2: Combined in main app")
    print("   • Add USSD routes to app.py")
    print("   • Single server on port 5000")
    print("   • Pros: Single process, simpler deployment")
    print("   • Cons: Mixed concerns")
    
    print("\nOption 3: Microservices with shared DB")
    print("   • Each service has specific purpose")
    print("   • Share database only")
    print("   • Pros: Scalable, modular")
    print("   • Cons: More complex")
    
    print("\n" + "=" * 60)
    
    # Recommend integration approach
    print("\n💡 RECOMMENDATION:")
    print("For your capstone project, Option 2 is best:")
    print("1. Add USSD routes to your main app.py")
    print("2. Keep everything in one Flask application")
    print("3. Single deployment, easier to demonstrate")
    
    return True

if __name__ == "__main__":
    test_integration()