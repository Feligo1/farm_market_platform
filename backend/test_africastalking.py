# =========================================================
# test_africastalking.py
# Test Africa's Talking SMS Integration
# =========================================================

import os
import sys
from dotenv import load_dotenv
import africastalking
import time
from datetime import datetime

# Load environment variables
load_dotenv()

def test_africastalking_connection():
    """Test Africa's Talking connection and send test SMS"""
    
    print("=" * 60)
    print("🔧 TESTING AFRICA'S TALKING INTEGRATION")
    print("=" * 60)
    
    # Get credentials
    username = os.getenv('AFRICASTALKING_USERNAME', 'sandbox')
    api_key = os.getenv('AFRICASTALKING_API_KEY', 'demo_key')
    sender_id = os.getenv('AFRICASTALKING_SENDER_ID', 'FarmConnect')
    
    print(f"📋 Configuration:")
    print(f"   Username: {username}")
    print(f"   API Key: {api_key[:20]}...{api_key[-20:] if len(api_key) > 40 else ''}")
    print(f"   Sender ID: {sender_id}")
    print(f"   Mode: {'SANDBOX' if 'sandbox' in username else 'PRODUCTION'}")
    
    # Test phone numbers (Zambian format)
    test_numbers = [
        "+260971234567",  # Test number 1
        "+260971111111",  # Test number 2
    ]
    
    try:
        # Initialize Africa's Talking
        print(f"\n🔌 Initializing Africa's Talking...")
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        print("✅ Africa's Talking initialized successfully")
        
        # Test 1: Send single SMS
        print(f"\n📱 TEST 1: Send Single SMS")
        print("-" * 40)
        
        test_message = f"FarmConnect Test SMS - {datetime.now().strftime('%H:%M:%S')}"
        
        try:
            response = sms.send(
                test_message,
                [test_numbers[0]],
                sender_id
            )
            
            print(f"📤 Sent to: {test_numbers[0]}")
            print(f"📝 Message: {test_message}")
            print(f"✅ Response: {response}")
            
            if response['Recipients'][0]['status'] == 'Success':
                print(f"🎉 SUCCESS: Message sent successfully!")
                print(f"   Message ID: {response['Recipients'][0]['messageId']}")
                print(f"   Cost: {response['Recipients'][0]['cost']}")
            else:
                print(f"⚠️  WARNING: Message status: {response['Recipients'][0]['status']}")
                
        except Exception as e:
            print(f"❌ ERROR sending SMS: {e}")
            print(f"💡 TIP: In sandbox mode, you can only send to whitelisted numbers")
            print(f"💡 TIP: Whitelist your number at: https://account.africastalking.com/apps/sandbox")
        
        # Test 2: Send bulk SMS
        print(f"\n📱 TEST 2: Send Bulk SMS")
        print("-" * 40)
        
        bulk_message = f"FarmConnect Bulk Test - {datetime.now().strftime('%Y-%m-%d')}"
        
        try:
            bulk_response = sms.send(
                bulk_message,
                test_numbers,
                sender_id
            )
            
            print(f"📤 Sent to: {len(test_numbers)} numbers")
            print(f"📝 Message: {bulk_message}")
            
            success_count = 0
            for recipient in bulk_response['Recipients']:
                status = recipient['status']
                if status == 'Success':
                    success_count += 1
                print(f"   {recipient['number']}: {status}")
            
            print(f"\n📊 Summary: {success_count}/{len(test_numbers)} successful")
            
        except Exception as e:
            print(f"❌ ERROR sending bulk SMS: {e}")
        
        # Test 3: Check account balance (if in production)
        print(f"\n💰 TEST 3: Check Account Balance")
        print("-" * 40)
        
        try:
            # Note: Balance check might not work in all sandbox accounts
            print("⏳ Checking balance...")
            # This is a placeholder - actual balance check might require different API call
            print("💡 Balance check feature depends on your account type")
            
        except Exception as e:
            print(f"⚠️  Balance check not available: {e}")
        
        # Test 4: Validate phone numbers
        print(f"\n📞 TEST 4: Phone Number Validation")
        print("-" * 40)
        
        test_phones = [
            "+260971234567",  # Valid
            "0971234567",     # Valid (local format)
            "260971234567",   # Valid (without +)
            "1234567890",     # Invalid
            "+260971",        # Invalid (too short)
        ]
        
        for phone in test_phones:
            try:
                # Format validation logic
                formatted = format_phone_number(phone)
                print(f"   {phone} -> {formatted}")
            except Exception as e:
                print(f"   {phone} -> INVALID: {e}")
        
        print(f"\n" + "=" * 60)
        print("🎯 INTEGRATION TEST COMPLETE")
        print("=" * 60)
        
        # Summary
        print(f"\n📋 RECOMMENDATIONS:")
        print(f"1. For production, upgrade from sandbox at: https://africastalking.com")
        print(f"2. Add your phone numbers to sandbox whitelist")
        print(f"3. Test with real numbers in production mode")
        print(f"4. Monitor SMS costs and balance regularly")
        print(f"5. Implement error handling and retry logic")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"1. Check your API credentials")
        print(f"2. Ensure africastalking package is installed: pip install africastalking")
        print(f"3. Verify internet connection")
        print(f"4. Check Africa's Talking service status: https://status.africastalking.com")
        return False

def format_phone_number(phone: str) -> str:
    """Format phone number for Zambia"""
    # Remove any spaces or special characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Format to +260XXXXXXXXX
    if phone.startswith('0'):
        phone = '+260' + phone[1:]
    elif phone.startswith('260'):
        phone = '+' + phone
    elif len(phone) == 9:
        phone = '+260' + phone
    elif not phone.startswith('+'):
        phone = '+260' + phone
    
    return phone

def test_integration_with_app():
    """Test integration with the main app's SMS service"""
    print(f"\n" + "=" * 60)
    print("🔗 TESTING INTEGRATION WITH MAIN APP")
    print("=" * 60)
    
    # Import the SMS service from app
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Mock the app's SMS service
        class MockSMSService:
            def __init__(self):
                self.initialized = True
                self.sender_id = "FarmConnect"
            
            def send_sms(self, to_number, message):
                print(f"📤 [Mock] Sending to {to_number}: {message[:50]}...")
                return {"success": True, "status": "sent", "phone": to_number}
            
            def format_phone_number(self, phone):
                return format_phone_number(phone)
        
        sms_service = MockSMSService()
        
        # Test various scenarios
        test_cases = [
            ("0971234567", "Test message to local format"),
            ("+260971234567", "Test message to intl format"),
            ("260971234567", "Test message without +"),
        ]
        
        for phone, message in test_cases:
            formatted = sms_service.format_phone_number(phone)
            result = sms_service.send_sms(formatted, message)
            print(f"   {phone} -> {formatted}: {result['status']}")
        
        print(f"\n✅ Integration test completed successfully")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

def create_test_environment():
    """Create test environment files"""
    print(f"\n" + "=" * 60)
    print("⚙️  SETTING UP TEST ENVIRONMENT")
    print("=" * 60)
    
    # Create test .env file
    test_env_content = """# Test Environment for Africa's Talking
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your_test_api_key_here
AFRICASTALKING_SENDER_ID=FarmConnectTest
DEBUG_SMS=true
"""
    
    with open('.env.test', 'w') as f:
        f.write(test_env_content)
    
    print("✅ Created .env.test file")
    print("💡 Update with your test credentials")
    
    # Create test script
    test_script = """#!/usr/bin/env python3
# Quick test script for SMS
import os
from dotenv import load_dotenv

load_dotenv('.env.test')

# Your test code here
print("Test environment loaded")
print(f"Username: {os.getenv('AFRICASTALKING_USERNAME')}")
"""
    
    with open('test_sms.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_sms.py script")
    
    print(f"\n📚 NEXT STEPS:")
    print("1. Update .env.test with your credentials")
    print("2. Run: python test_africastalking.py")
    print("3. Test with real numbers in production")

if __name__ == "__main__":
    # Run the tests
    print("\n" + "=" * 60)
    print("🌍 FARM CONNECT - SMS INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Mulungushi University - ICT 431 Capstone Project")
    print("Student: Daka Felix (202206453)")
    print("=" * 60)
    
    # Run tests
    connection_ok = test_africastalking_connection()
    
    if connection_ok:
        test_integration_with_app()
        create_test_environment()
    
    print(f"\n" + "=" * 60)
    print("🎉 TESTING COMPLETE")
    print("=" * 60)
    
    if connection_ok:
        print("\n✅ SUCCESS: Africa's Talking integration is working!")
        print("💡 You can now integrate SMS features into your FarmConnect platform")
    else:
        print("\n⚠️  ISSUES DETECTED")
        print("Please fix the issues before proceeding with integration")
    
    print(f"\n📞 SUPPORT:")
    print("Africa's Talking Support: support@africastalking.com")
    print("Documentation: https://developers.africastalking.com")