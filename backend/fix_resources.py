import os

activities = [
    "SplashActivity.java",
    "LoginActivity.java", 
    "RegisterActivity.java",
    "MainActivity.java",
    "MarketPricesActivity.java",
    "PriceForecastActivity.java",
    "BuyersActivity.java",
    "ProfileActivity.java"
]

base_path = "FarmConnect/app/src/main/java/com/farmconnect/activities"

for activity in activities:
    filepath = os.path.join(base_path, activity)
    if os.path.exists(filepath):
        print(f"✅ {activity}")
    else:
        print(f"❌ {activity} - MISSING")