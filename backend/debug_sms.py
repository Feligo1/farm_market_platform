import os
import africastalking
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("AFRICA'S TALKING DEBUG")
print("=" * 60)

# Check credentials
username = os.getenv("AFRICASTALKING_USERNAME")
api_key = os.getenv("AFRICASTALKING_API_KEY")

print(f"Username: {username}")
print(f"API Key exists: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key sample: {api_key[:20] if api_key else 'None'}...")
print(f"Current directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

if not username or not api_key:
    print("\n❌ ERROR: Missing credentials!")
    exit(1)

print("\n🔧 Testing SDK initialization...")
try:
    # Initialize SDK
    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
    print("✅ SDK initialized successfully!")
    
    # Test sending
    print("\n📱 Testing SMS send...")
    print(f"Using test number: +254700000000")
    
    response = sms.send("Test message from debug script", ["+254700000000"])
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    
    if 'SMSMessageData' in response:
        recipients = response['SMSMessageData'].get('Recipients', [])
        if recipients:
            recipient = recipients[0]
            print(f"\n📊 Recipient Status:")
            print(f"  Status: {recipient.get('status')}")
            print(f"  Status Code: {recipient.get('statusCode')}")
            print(f"  Number: {recipient.get('number')}")
            print(f"  Message ID: {recipient.get('messageId')}")
            
            if recipient.get('statusCode') == 101:
                print("\n🎉 SUCCESS! SMS sent via Africa's Talking!")
            else:
                print(f"\n⚠️ SMS not sent. Status: {recipient.get('status')}")
        else:
            print("\n❌ No recipients in response")
    else:
        print(f"\n❌ Unexpected response format: {response}")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()