# test_sms_functionality.py
import os
import sys

# Add parent directory to path to import from app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sms():
    """Test SMS functionality"""
    print("=" * 60)
    print("📱 TESTING SMS FUNCTIONALITY")
    print("=" * 60)
    
    # Test using Africa's Talking
    try:
        from backend.test_ussd import REAL_SMS_SERVICE, SMS_SERVICE
        
        if REAL_SMS_SERVICE:
            print("✅ Africa's Talking SMS service is available")
            
            # Test phone number (use a test number or your own)
            test_phone = "+260971234567"  # Replace with a real number for actual test
            test_message = "FarmConnect Test: This is a test SMS from the platform."
            
            print(f"\n📤 Testing SMS to: {test_phone}")
            print(f"   Message: {test_message}")
            
            try:
                # Try to send SMS
                response = SMS_SERVICE.send(test_message, [test_phone])
                print(f"   ✅ SMS sent successfully!")
                print(f"   Response: {response}")
            except Exception as e:
                print(f"   ⚠️  SMS send failed (might be sandbox restriction): {e}")
                print(f"   Note: Sandbox may restrict sending to real numbers")
        else:
            print("⚠️  Africa's Talking SMS service not available (simulation mode)")
            
    except ImportError:
        print("❌ Could not import SMS service from ussd_app.py")
    
    print("\n" + "=" * 60)
    print("💾 Testing SMS Database Logging:")
    print("=" * 60)
    
    # Test if SMS logs are being saved to database
    try:
        import sqlite3
        
        conn = sqlite3.connect('farm_market.db')
        cur = conn.cursor()
        
        # Check if sms_history table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sms_history'")
        if cur.fetchone():
            print("✅ sms_history table exists")
            
            # Count existing SMS logs
            cur.execute("SELECT COUNT(*) as count FROM sms_history")
            count = cur.fetchone()[0]
            print(f"   Total SMS logs: {count}")
            
            # Show recent SMS
            cur.execute("SELECT phone, message, status FROM sms_history ORDER BY sent_at DESC LIMIT 3")
            recent = cur.fetchall()
            
            if recent:
                print(f"   Recent SMS logs:")
                for sms in recent:
                    phone = sms[0]
                    message = sms[1][:30] + "..." if len(sms[1]) > 30 else sms[1]
                    status = sms[2]
                    print(f"     • {phone}: {message} [{status}]")
            else:
                print("   No SMS logs found yet")
        else:
            print("❌ sms_history table not found")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_sms()