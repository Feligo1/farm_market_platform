# =========================================================
# sms_service.py
# Enhanced SMS Service for FarmConnect with Africa's Talking
# =========================================================

import os
import json
import sqlite3
import logging
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# Try to import Africa's Talking
try:
    import africastalking
    AFRICASTALKING_AVAILABLE = True
except ImportError:
    AFRICASTALKING_AVAILABLE = False
    print("⚠️  Africa's Talking SDK not available")

# Try to import Twilio (optional backup)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️  Twilio SDK not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedSMSService:
    """Enhanced SMS Service with Africa's Talking and Twilio support"""
    
    def __init__(self, db_path='farm_market.db'):
        self.db_path = db_path
        self.sms_queue = []
        self.is_running = False
        self.scheduler_thread = None
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize SMS providers
        self.providers = self.initialize_providers()
        
        # Statistics
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_queued': 0,
            'last_sent': None,
            'providers': {}
        }
        
        logger.info("Enhanced SMS Service initialized")
    
    def load_config(self) -> Dict:
        """Load SMS service configuration"""
        config = {
            'providers': {
                'africastalking': {
                    'enabled': os.getenv('AFRICASTALKING_ENABLED', 'true').lower() == 'true',
                    'username': os.getenv('AFRICASTALKING_USERNAME', 'sandbox'),
                    'api_key': os.getenv('AFRICASTALKING_API_KEY', 'demo_key'),
                    'shortcode': os.getenv('AFRICASTALKING_SHORTCODE', ''),
                    'sender_id': os.getenv('AFRICASTALKING_SENDER_ID', 'FarmConnect'),
                    'priority': 1
                },
                'twilio': {
                    'enabled': os.getenv('TWILIO_ENABLED', 'false').lower() == 'true',
                    'account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
                    'auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
                    'phone_number': os.getenv('TWILIO_PHONE_NUMBER', ''),
                    'priority': 2
                }
            },
            'scheduling': {
                'alert_time': os.getenv('SMS_ALERT_TIME', '08:00'),
                'retry_attempts': int(os.getenv('SMS_RETRY_ATTEMPTS', '3')),
                'retry_delay': int(os.getenv('SMS_RETRY_DELAY', '60')),
                'batch_size': int(os.getenv('SMS_BATCH_SIZE', '50')),
                'queue_check_interval': int(os.getenv('QUEUE_CHECK_INTERVAL', '30'))
            },
            'templates': {
                'price_alert': 'FarmConnect: {commodity} price in {market}: ZMW {price}/{unit}. Trend: {trend}',
                'price_drop': 'ALERT: {commodity} price dropped to ZMW {price}. Good time to buy!',
                'price_rise': 'ALERT: {commodity} price rose to ZMW {price}. Consider selling!',
                'daily_summary': 'Daily Market Summary:\n{summary}\nText STOP to unsubscribe',
                'buyer_alert': 'New buyer for {commodity}: {name} ({phone}). Max price: ZMW {max_price}',
                'weather_alert': 'Weather Alert: {forecast}. Farming tip: {tip}',
                'welcome': 'Welcome to FarmConnect! Dial *123# for market prices. Your PIN: {pin}',
                'low_balance': 'ALERT: Your SMS balance is low ({balance}). Please top up.',
                'system_alert': 'System Alert: {message}'
            },
            'limits': {
                'daily_limit_per_user': int(os.getenv('SMS_DAILY_LIMIT', '5')),
                'message_length': 160,
                'rate_limit': int(os.getenv('SMS_RATE_LIMIT', '10'))  # messages per minute
            }
        }
        return config
    
    def initialize_providers(self) -> Dict:
        """Initialize SMS providers"""
        providers = {}
        
        # Africa's Talking
        if AFRICASTALKING_AVAILABLE and self.config['providers']['africastalking']['enabled']:
            try:
                username = self.config['providers']['africastalking']['username']
                api_key = self.config['providers']['africastalking']['api_key']
                
                if username != 'sandbox' and api_key != 'demo_key':
                    africastalking.initialize(username, api_key)
                    providers['africastalking'] = {
                        'client': africastalking.SMS,
                        'name': 'Africa\'s Talking',
                        'priority': self.config['providers']['africastalking']['priority'],
                        'enabled': True
                    }
                    logger.info("Africa's Talking SMS service initialized")
                else:
                    logger.warning("Africa's Talking using demo credentials")
                    providers['africastalking'] = {
                        'client': None,
                        'name': 'Africa\'s Talking (Demo)',
                        'priority': self.config['providers']['africastalking']['priority'],
                        'enabled': False
                    }
            except Exception as e:
                logger.error(f"Failed to initialize Africa's Talking: {e}")
                providers['africastalking'] = {
                    'client': None,
                    'name': 'Africa\'s Talking (Error)',
                    'priority': self.config['providers']['africastalking']['priority'],
                    'enabled': False
                }
        
        # Twilio
        if TWILIO_AVAILABLE and self.config['providers']['twilio']['enabled']:
            try:
                account_sid = self.config['providers']['twilio']['account_sid']
                auth_token = self.config['providers']['twilio']['auth_token']
                
                if account_sid and auth_token:
                    providers['twilio'] = {
                        'client': TwilioClient(account_sid, auth_token),
                        'name': 'Twilio',
                        'priority': self.config['providers']['twilio']['priority'],
                        'enabled': True
                    }
                    logger.info("Twilio SMS service initialized")
                else:
                    logger.warning("Twilio credentials not provided")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
        
        # Demo provider (fallback)
        if not providers:
            providers['demo'] = {
                'client': None,
                'name': 'Demo SMS',
                'priority': 99,
                'enabled': True
            }
            logger.info("Using demo SMS service")
        
        return providers
    
    def send_sms(self, to_number: str, message: str, 
                 message_type: str = 'notification',
                 priority: str = 'normal') -> Dict:
        """
        Send SMS message
        
        Args:
            to_number: Recipient phone number (format: +260971234567)
            message: SMS message content
            message_type: Type of message (notification, alert, marketing)
            priority: Priority level (high, normal, low)
        
        Returns:
            Dictionary with send status and details
        """
        try:
            # Validate phone number
            if not self.validate_phone_number(to_number):
                return {
                    'success': False,
                    'error': 'Invalid phone number format',
                    'phone': to_number,
                    'message_id': None
                }
            
            # Check daily limit
            if not self.check_daily_limit(to_number, message_type):
                return {
                    'success': False,
                    'error': 'Daily limit exceeded',
                    'phone': to_number,
                    'message_id': None
                }
            
            # Truncate message if too long
            message = self.truncate_message(message)
            
            # Prepare SMS data
            sms_data = {
                'to': to_number,
                'message': message,
                'type': message_type,
                'priority': priority,
                'attempts': 0,
                'status': 'queued',
                'queued_at': datetime.now().isoformat(),
                'provider_used': None,
                'message_id': None,
                'cost': 0.0
            }
            
            # For high priority, send immediately
            if priority == 'high':
                result = self.send_immediate(sms_data)
            else:
                # Add to queue for batch sending
                self.sms_queue.append(sms_data)
                self.stats['total_queued'] += 1
                result = {
                    'success': True,
                    'status': 'queued',
                    'queue_position': len(self.sms_queue),
                    'message': 'Message added to queue'
                }
            
            # Log to database
            self.log_sms_to_db(sms_data, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {
                'success': False,
                'error': str(e),
                'phone': to_number,
                'message_id': None
            }
    
    def send_immediate(self, sms_data: Dict) -> Dict:
        """Send SMS immediately"""
        providers_order = sorted(
            [p for p in self.providers.values() if p['enabled']],
            key=lambda x: x['priority']
        )
        
        for provider in providers_order:
            try:
                result = self.send_with_provider(provider, sms_data)
                if result['success']:
                    sms_data['provider_used'] = provider['name']
                    sms_data['status'] = 'sent'
                    sms_data['sent_at'] = datetime.now().isoformat()
                    
                    self.stats['total_sent'] += 1
                    self.stats['last_sent'] = sms_data['sent_at']
                    
                    # Update provider stats
                    if provider['name'] not in self.stats['providers']:
                        self.stats['providers'][provider['name']] = 0
                    self.stats['providers'][provider['name']] += 1
                    
                    return {
                        'success': True,
                        'status': 'sent',
                        'provider': provider['name'],
                        'message_id': result.get('message_id'),
                        'cost': result.get('cost', 0.0)
                    }
                    
            except Exception as e:
                logger.error(f"Provider {provider['name']} failed: {e}")
                continue
        
        # All providers failed
        sms_data['status'] = 'failed'
        self.stats['total_failed'] += 1
        
        return {
            'success': False,
            'status': 'failed',
            'error': 'All providers failed',
            'provider': None
        }
    
    def send_with_provider(self, provider: Dict, sms_data: Dict) -> Dict:
        """Send SMS using specific provider"""
        provider_name = provider['name'].lower()
        
        if 'africastalking' in provider_name and provider['client']:
            return self.send_with_africastalking(provider['client'], sms_data)
        elif 'twilio' in provider_name and provider['client']:
            return self.send_with_twilio(provider['client'], sms_data)
        else:
            # Demo mode
            return self.send_demo(sms_data)
    
    def send_with_africastalking(self, client, sms_data: Dict) -> Dict:
        """Send SMS using Africa's Talking"""
        try:
            sender_id = self.config['providers']['africastalking']['sender_id']
            
            response = client.send(
                sms_data['message'],
                [sms_data['to']],
                sender_id
            )
            
            if response['Recipients'][0]['status'] == 'Success':
                return {
                    'success': True,
                    'message_id': response['Recipients'][0]['messageId'],
                    'cost': float(response['Recipients'][0]['cost'].split(' ')[1])
                }
            else:
                return {
                    'success': False,
                    'error': response['Recipients'][0]['status']
                }
                
        except Exception as e:
            logger.error(f"Africa's Talking send error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_with_twilio(self, client, sms_data: Dict) -> Dict:
        """Send SMS using Twilio"""
        try:
            from_number = self.config['providers']['twilio']['phone_number']
            
            message = client.messages.create(
                body=sms_data['message'],
                from_=from_number,
                to=sms_data['to']
            )
            
            return {
                'success': True,
                'message_id': message.sid,
                'cost': 0.0  # Twilio doesn't return cost in response
            }
            
        except Exception as e:
            logger.error(f"Twilio send error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_demo(self, sms_data: Dict) -> Dict:
        """Demo SMS sending (for testing)"""
        logger.info(f"[DEMO SMS] To: {sms_data['to']}, Message: {sms_data['message'][:50]}...")
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Simulate 90% success rate
        if random.random() > 0.1:
            return {
                'success': True,
                'message_id': f"demo_{int(time.time())}_{random.randint(1000, 9999)}",
                'cost': 1.5
            }
        else:
            return {
                'success': False,
                'error': 'Demo failure simulation'
            }
    
    def send_template(self, to_number: str, template_name: str, 
                     variables: Dict = None) -> Dict:
        """Send SMS using predefined template"""
        if template_name not in self.config['templates']:
            return {
                'success': False,
                'error': f'Template {template_name} not found'
            }
        
        template = self.config['templates'][template_name]
        
        # Replace variables
        if variables:
            try:
                message = template.format(**variables)
            except KeyError as e:
                return {
                    'success': False,
                    'error': f'Missing template variable: {e}'
                }
        else:
            message = template
        
        return self.send_sms(to_number, message, template_name)
    
    def send_bulk_sms(self, phone_numbers: List[str], message: str,
                     batch_size: int = None) -> List[Dict]:
        """Send SMS to multiple recipients"""
        if batch_size is None:
            batch_size = self.config['scheduling']['batch_size']
        
        results = []
        for i in range(0, len(phone_numbers), batch_size):
            batch = phone_numbers[i:i + batch_size]
            batch_results = []
            
            for phone in batch:
                result = self.send_sms(phone, message, 'bulk')
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Rate limiting
            if i + batch_size < len(phone_numbers):
                time.sleep(60 / self.config['limits']['rate_limit'])
        
        return results
    
    def send_daily_alerts(self):
        """Send daily price alerts to subscribed users"""
        logger.info("Sending daily price alerts")
        
        try:
            # Get users with SMS alerts enabled
            users = self.get_users_with_alerts()
            
            # Get today's price changes
            price_changes = self.get_significant_price_changes()
            
            for user in users:
                user_alerts = []
                
                # Check user's subscribed commodities
                user_commodities = self.get_user_commodities(user['id'])
                
                for commodity, data in price_changes.items():
                    if commodity in user_commodities:
                        alert_type = 'price_drop' if data['change'] < 0 else 'price_rise'
                        
                        self.send_template(
                            user['phone'],
                            alert_type,
                            {
                                'commodity': commodity,
                                'price': data['price'],
                                'change': abs(data['change'])
                            }
                        )
                        user_alerts.append(commodity)
                
                # Send summary if alerts sent
                if user_alerts:
                    logger.info(f"Sent alerts to {user['phone']}: {user_alerts}")
        
        except Exception as e:
            logger.error(f"Error sending daily alerts: {e}")
    
    def process_queue(self):
        """Process SMS queue"""
        if not self.sms_queue:
            return
        
        logger.info(f"Processing SMS queue ({len(self.sms_queue)} messages)")
        
        # Sort by priority (high first)
        self.sms_queue.sort(key=lambda x: {'high': 0, 'normal': 1, 'low': 2}[x['priority']])
        
        # Process batch
        batch_size = min(self.config['scheduling']['batch_size'], len(self.sms_queue))
        batch = self.sms_queue[:batch_size]
        
        for sms_data in batch:
            result = self.send_immediate(sms_data)
            sms_data.update(result)
        
        # Remove processed messages
        self.sms_queue = self.sms_queue[batch_size:]
    
    def start_scheduler(self):
        """Start SMS scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        
        # Schedule daily alerts
        alert_time = self.config['scheduling']['alert_time']
        schedule.every().day.at(alert_time).do(self.send_daily_alerts)
        
        # Schedule queue processing
        interval = self.config['scheduling']['queue_check_interval']
        schedule.every(interval).seconds.do(self.process_queue)
        
        # Start scheduler in background thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"SMS scheduler started (alerts at {alert_time})")
    
    def stop_scheduler(self):
        """Stop SMS scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("SMS scheduler stopped")
    
    def validate_phone_number(self, phone: str) -> bool:
        """Validate Zambian phone number format"""
        import re
        
        # Zambian mobile formats
        patterns = [
            r'^\+2609[0-9]{8}$',      # +260971234567
            r'^\+2607[0-9]{8}$',      # +260771234567
            r'^09[0-9]{8}$',          # 0971234567
            r'^07[0-9]{8}$',          # 0771234567
            r'^2609[0-9]{8}$',        # 260971234567
            r'^2607[0-9]{8}$'         # 260771234567
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone):
                return True
        
        return False
    
    def truncate_message(self, message: str, max_length: int = None) -> str:
        """Truncate message to maximum length"""
        if max_length is None:
            max_length = self.config['limits']['message_length']
        
        if len(message) > max_length:
            message = message[:max_length - 3] + '...'
        
        return message
    
    def check_daily_limit(self, phone: str, message_type: str) -> bool:
        """Check if user has exceeded daily SMS limit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cur.execute('''
                SELECT COUNT(*) 
                FROM sms_history 
                WHERE phone = ? 
                AND DATE(sent_at) = ?
                AND type = ?
            ''', (phone, today, message_type))
            
            count = cur.fetchone()[0]
            conn.close()
            
            limit = self.config['limits']['daily_limit_per_user']
            return count < limit
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return True  # Allow if error
    
    def log_sms_to_db(self, sms_data: Dict, result: Dict):
        """Log SMS to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO sms_history 
                (phone, message, type, status, provider, message_id, 
                 cost, sent_at, queued_at, attempts, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sms_data['to'],
                sms_data['message'],
                sms_data.get('type', 'notification'),
                result.get('status', 'unknown'),
                sms_data.get('provider_used'),
                result.get('message_id'),
                result.get('cost', 0.0),
                sms_data.get('sent_at'),
                sms_data.get('queued_at'),
                sms_data.get('attempts', 0),
                result.get('error')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging SMS to DB: {e}")
    
    def get_users_with_alerts(self) -> List[Dict]:
        """Get users with SMS alerts enabled"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute('''
                SELECT user_id, phone, name, sms_alerts 
                FROM users 
                WHERE sms_alerts = 1 
                AND status = 'active'
                AND phone IS NOT NULL
            ''')
            
            users = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting users with alerts: {e}")
            return []
    
    def get_significant_price_changes(self, threshold: float = 5.0) -> Dict:
        """Get commodities with significant price changes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Get today's and yesterday's average prices
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            query = '''
                SELECT commodity, 
                       AVG(CASE WHEN DATE(recorded_at) = ? THEN price END) as today_price,
                       AVG(CASE WHEN DATE(recorded_at) = ? THEN price END) as yesterday_price
                FROM market_prices 
                WHERE verified = 1
                GROUP BY commodity
                HAVING today_price IS NOT NULL AND yesterday_price IS NOT NULL
            '''
            
            cur.execute(query, (today, yesterday))
            changes = {}
            
            for row in cur.fetchall():
                commodity, today_price, yesterday_price = row
                
                if today_price and yesterday_price:
                    change_percent = ((today_price - yesterday_price) / yesterday_price) * 100
                    
                    if abs(change_percent) >= threshold:
                        changes[commodity] = {
                            'price': round(today_price, 2),
                            'change': round(change_percent, 1),
                            'yesterday_price': round(yesterday_price, 2)
                        }
            
            conn.close()
            return changes
            
        except Exception as e:
            logger.error(f"Error getting price changes: {e}")
            return {}
    
    def get_user_commodities(self, user_id: str) -> List[str]:
        """Get commodities that user is interested in"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                SELECT main_crops FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cur.fetchone()
            conn.close()
            
            if result and result[0]:
                # Parse comma-separated crops
                return [crop.strip() for crop in result[0].split(',')]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting user commodities: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get SMS service statistics"""
        return {
            'queue_size': len(self.sms_queue),
            'stats': self.stats,
            'providers': {k: v['enabled'] for k, v in self.providers.items()},
            'config': {
                'alert_time': self.config['scheduling']['alert_time'],
                'daily_limit': self.config['limits']['daily_limit_per_user']
            }
        }
    
    def get_recent_messages(self, limit: int = 20) -> List[Dict]:
        """Get recent SMS messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute('''
                SELECT * FROM sms_history 
                ORDER BY sent_at DESC 
                LIMIT ?
            ''', (limit,))
            
            messages = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []
    
    def cleanup_old_messages(self, days: int = 30):
        """Clean up SMS messages older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cur.execute('''
                DELETE FROM sms_history 
                WHERE DATE(sent_at) < ?
            ''', (cutoff_date,))
            
            deleted = cur.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted} old SMS messages")
            
        except Exception as e:
            logger.error(f"Error cleaning up messages: {e}")

# =========================================================
# Usage Examples
# =========================================================

def example_usage():
    """Example usage of EnhancedSMSService"""
    
    # Initialize service
    sms_service = EnhancedSMSService()
    
    # Start scheduler
    sms_service.start_scheduler()
    
    # Send individual SMS
    result = sms_service.send_sms(
        to_number="+260971234567",
        message="Market prices for maize: ZMW 145.50/kg in Lusaka",
        message_type="price_alert",
        priority="normal"
    )
    
    print(f"Individual send result: {result}")
    
    # Send using template
    template_result = sms_service.send_template(
        to_number="+260971234568",
        template_name="price_alert",
        variables={
            "commodity": "Tomatoes",
            "market": "Kabwe Main Market",
            "price": 85.75,
            "unit": "kg",
            "trend": "falling"
        }
    )
    
    print(f"Template send result: {template_result}")
    
    # Send bulk messages
    phone_numbers = ["+260971234567", "+260971234568", "+260971234569"]
    bulk_result = sms_service.send_bulk_sms(
        phone_numbers=phone_numbers,
        message="New buyer registered for maize! Contact 0971111111"
    )
    
    print(f"Bulk send results: {len(bulk_result)} messages")
    
    # Get statistics
    stats = sms_service.get_stats()
    print(f"SMS Service Stats: {stats}")
    
    # Get recent messages
    recent = sms_service.get_recent_messages(limit=5)
    print(f"Recent messages: {recent}")
    
    # Stop scheduler when done
    # sms_service.stop_scheduler()

if __name__ == "__main__":
    example_usage()