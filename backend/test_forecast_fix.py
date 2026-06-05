#!/usr/bin/env python3
"""
Test the forecast API after fix
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def test_forecast():
    print("=" * 60)
    print("🔮 Testing Fixed Forecast API")
    print("=" * 60)
    
    # First, check model status
    print("\n📊 1. Checking ML Model Status:")
    print("-" * 40)
    try:
        response = requests.get(f"{API_BASE}/forecast/model-status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ML Model Available: {data.get('ml_model_available', False)}")
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"   Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test forecast for Maize
    print("\n📊 2. 7-day Forecast for Maize in Lusaka:")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE}/forecast?commodity=Maize&market=Lusaka&days=7")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   Commodity: {data.get('commodity')}")
            print(f"   Market: {data.get('market')}")
            print(f"   Current Price: ZMW {data.get('current_price', 0)}/kg")
            print(f"   Model Used: {data.get('model_used', 'unknown')}")
            print(f"   ML Available: {data.get('ml_available', False)}")
            print(f"\n   📈 Forecast:")
            
            for f in data.get('forecast', [])[:7]:
                arrow = "▲" if f.get('trend') == 'up' else "▼" if f.get('trend') == 'down' else "●"
                print(f"      {f.get('date')}: ZMW {f.get('predicted_price')}/kg {arrow} ({f.get('change_percent', 0):+}%)")
            
            print(f"\n   💡 Recommendation:")
            rec = data.get('recommendations', {})
            print(f"      {rec.get('action', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_forecast()