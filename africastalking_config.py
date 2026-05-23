# africastalking_config.py
import africastalking
import os
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AfricaTalkingService:
    """Production-ready Africa's Talking Integration"""
    
    def __init__(self):
        # Africa's Talking credentials
        self.username = 'sandbox'  # Use 'sandbox' for testing, your username for production
        self.api_key = 'atsk_9643a4f5a20be0fd835ff0eb5635fc56bacfd36272fb20e9a71573931e6a3b4228701070'
        
        # Initialize Africa's Talking SDK
        try:
            africastalking.initialize(self.username, self.api_key)
            self.sms = africastalking.SMS
            self.ussd = africastalking.USSD
            self.voice = africastalking.Voice
            self.airtime = africastalking.Airtime
            self.payment = africastalking.Payment
            
            logger.info("✅ Africa's Talking SDK initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Africa's Talking: {e}")
            raise
        
        # SMS settings
        self.sender_id = 'FarmConnect'  # Your approved sender ID
        self.short_code = '12345'  # Your USSD short code
        
        # Track message delivery
        self.message_queue = []
        
    def send_sms(self, phone_number, message, callback_url=None):
        """
        Send SMS to a single recipient or multiple recipients
        
        Args:
            phone_number: String or list of phone numbers (format: +260XXXXXXXXX)
            message: SMS content (max 160 characters per message)
            callback_url: Optional webhook URL for delivery reports
            
        Returns:
            dict: Response from Africa's Talking
        """
        try:
            # Format phone numbers (ensure they have country code)
            if isinstance(phone_number, str):
                phone_numbers = [self._format_phone_number(phone_number)]
            else:
                phone_numbers = [self._format_phone_number(p) for p in phone_number]
            
            # Prepare SMS payload
            sms_payload = {
                'to': phone_numbers,
                'message': message[:160],  # Limit to 160 characters
                'from': self.sender_id,
                'enqueue': True  # Queue message for better delivery
            }
            
            if callback_url:
                sms_payload['callback_url'] = callback_url
            
            # Send SMS
            response = self.sms.send(
                message,
                phone_numbers,
                sender_id=self.sender_id,
                enqueue=True
            )
            
            logger.info(f"📱 SMS sent to {phone_numbers}: {response}")
            
            # Log to database
            self._log_sms_to_db(phone_numbers, message, response)
            
            return {
                'success': True,
                'response': response,
                'message_id': response.get('SMSMessageData', {}).get('Message', [{}])[0].get('id'),
                'status': response.get('SMSMessageData', {}).get('Message', [{}])[0].get('status')
            }
            
        except Exception as e:
            logger.error(f"❌ SMS sending failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_sms(self, recipients, message):
        """
        Send bulk SMS to multiple recipients
        
        Args:
            recipients: List of (phone, name) tuples or dicts
            message: SMS content
        """
        phone_numbers = []
        for recipient in recipients:
            if isinstance(recipient, dict):
                phone = recipient.get('phone')
            else:
                phone = recipient[0]
            phone_numbers.append(self._format_phone_number(phone))
        
        return self.send_sms(phone_numbers, message)
    
    def send_price_alert(self, phone_number, commodity, price, market, trend):
        """
        Send formatted price alert SMS
        """
        message = f"FarmConnect Alert: {commodity} price at {market} is ZMW {price}/kg. Trend: {trend}. Dial *384*7321# for more info."
        return self.send_sms(phone_number, message)
    
    def send_forecast_alert(self, phone_number, commodity, forecast_price, days, confidence):
        """
        Send price forecast alert SMS
        """
        message = f"FarmConnect Forecast: {commodity} expected at ZMW {forecast_price}/kg in {days} days (confidence: {confidence}). Dial *384*7321# for details."
        return self.send_sms(phone_number, message)
    
    def send_welcome_message(self, phone_number, name, ussd_pin):
        """
        Send welcome message to new users
        """
        message = f"Welcome {name} to FarmConnect Zambia! Your USSD PIN is {ussd_pin}. Dial *384*7321# for market prices, forecasts, and buyers."
        return self.send_sms(phone_number, message)
    
    def send_buyer_contact(self, phone_number, buyer_name, buyer_phone, commodity, price):
        """
        Send buyer contact information via SMS
        """
        message = f"FarmConnect: {buyer_name} wants to buy {commodity} at ZMW {price}/kg. Contact: {buyer_phone}. Dial *384*7321# for more buyers."
        return self.send_sms(phone_number, message)
    
    def _format_phone_number(self, phone):
        """
        Format phone number to Africa's Talking format (+260XXXXXXXXX)
        """
        phone = str(phone).strip()
        
        # Remove any spaces or special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if missing
        if phone.startswith('0'):
            phone = '260' + phone[1:]
        elif not phone.startswith('260') and len(phone) == 9:
            phone = '260' + phone
        
        # Ensure it starts with +
        if not phone.startswith('+'):
            phone = '+' + phone
        
        return phone
    
    def _log_sms_to_db(self, phone_numbers, message, response):
        """
        Log SMS to database for tracking
        """
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('farm_market.db')
            cur = conn.cursor()
            
            message_id = response.get('SMSMessageData', {}).get('Message', [{}])[0].get('id', '')
            status = response.get('SMSMessageData', {}).get('Message', [{}])[0].get('status', '')
            
            for phone in phone_numbers if isinstance(phone_numbers, list) else [phone_numbers]:
                cur.execute('''
                    INSERT INTO sms_history (phone, message, type, status, provider, message_id, sent_at, cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    phone,
                    message,
                    'price_alert' if 'price' in message.lower() else 'notification',
                    status,
                    'Africa's Talking',
                    message_id,
                    datetime.now().isoformat(),
                    0.05  # Cost per SMS (adjust as needed)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log SMS to DB: {e}")
    
    def get_sms_balance(self):
        """
        Get SMS account balance from Africa's Talking
        """
        try:
            # This is a placeholder - actual implementation depends on Africa's Talking API
            # You may need to use their payments API to get balance
            return {
                'success': True,
                'balance': 100.00,  # Example balance
                'currency': 'USD'
            }
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# USSD Service with Africa's Talking
class AfricaTalkingUSSD:
    """USSD Service integrated with Africa's Talking"""
    
    def __init__(self, database_path='farm_market.db'):
        self.database_path = database_path
        self.sms_service = AfricaTalkingService()
        self.sessions = {}
        
    def handle_ussd_request(self, session_id, phone_number, text, service_code='*384*7321#'):
        """
        Handle USSD requests from Africa's Talking callback
        
        Args:
            session_id: Unique session ID from Africa's Talking
            phone_number: User's phone number
            text: User's input (with * separators)
            service_code: USSD service code
            
        Returns:
            str: USSD response (CON or END)
        """
        try:
            # Initialize session if new
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'phone': phone_number,
                    'state': 'initial',
                    'data': {},
                    'created': datetime.now(),
                    'last_activity': datetime.now()
                }
            
            session = self.sessions[session_id]
            session['last_activity'] = datetime.now()
            
            # Process USSD input
            if text == '':
                return self._show_main_menu(session)
            else:
                return self._process_menu(session, text)
                
        except Exception as e:
            logger.error(f"USSD handler error: {e}")
            return "END Service temporarily unavailable. Please try again later."
    
    def _show_main_menu(self, session):
        """Display main USSD menu"""
        response = "CON Welcome to FarmConnect Zambia\n"
        response += "=======================\n"
        response += "1. Check Market Prices\n"
        response += "2. Price Forecast\n"
        response += "3. Find Buyers\n"
        response += "4. Weather Information\n"
        response += "5. Farming Tips\n"
        response += "6. My Account\n"
        response += "0. Exit\n"
        response += "=======================\n"
        response += "Choose option:"
        
        session['state'] = 'main_menu'
        return response
    
    def _process_menu(self, session, text):
        """Process USSD menu navigation"""
        parts = text.split('*')
        current_level = len(parts) - 1
        
        if session['state'] == 'main_menu':
            return self._handle_main_menu(session, parts[0])
        
        elif session['state'] == 'price_menu':
            return self._handle_price_menu(session, parts)
        
        elif session['state'] == 'forecast_menu':
            return self._handle_forecast_menu(session, parts)
        
        elif session['state'] == 'buyer_menu':
            return self._handle_buyer_menu(session, parts)
        
        elif session['state'] == 'account_menu':
            return self._handle_account_menu(session, parts)
        
        else:
            return "END Invalid option. Dial *384*7321# to restart."
    
    def _handle_main_menu(self, session, option):
        """Handle main menu selection"""
        if option == '1':
            session['state'] = 'price_menu'
            return self._show_price_menu()
        
        elif option == '2':
            session['state'] = 'forecast_menu'
            return self._show_forecast_menu()
        
        elif option == '3':
            session['state'] = 'buyer_menu'
            return self._show_buyer_menu()
        
        elif option == '4':
            return self._show_weather_info()
        
        elif option == '5':
            return self._show_farming_tip()
        
        elif option == '6':
            session['state'] = 'account_menu'
            return self._show_account_menu(session)
        
        elif option == '0':
            self._cleanup_session(session)
            return "END Thank you for using FarmConnect!\nDial *384*7321# to return."
        
        else:
            return "END Invalid option. Dial *384*7321# to restart."
    
    def _show_price_menu(self):
        """Show commodity selection for prices"""
        response = "CON Select Commodity:\n"
        response += "1. Maize\n"
        response += "2. Tomatoes\n"
        response += "3. Beans\n"
        response += "4. Groundnuts\n"
        response += "5. Rice\n"
        response += "6. Soybeans\n"
        response += "7. Sweet Potatoes\n"
        response += "8. Back to Main Menu\n"
        response += "Choose option:"
        return response
    
    def _handle_price_menu(self, session, parts):
        """Handle price menu selection"""
        if len(parts) == 1:
            # Just selected commodity
            option = parts[0]
            commodity_map = {
                '1': 'Maize', '2': 'Tomatoes', '3': 'Beans',
                '4': 'Groundnuts', '5': 'Rice', '6': 'Soybeans',
                '7': 'Sweet Potatoes', '8': 'back'
            }
            
            if option == '8':
                return self._show_main_menu(session)
            
            commodity = commodity_map.get(option)
            if not commodity:
                return "END Invalid option. Dial *384*7321# to restart."
            
            # Get price for commodity
            price_data = self._get_commodity_price(commodity)
            
            if price_data:
                response = f"END {commodity} Prices:\n"
                response += f"Current: ZMW {price_data['price']}/kg\n"
                response += f"Market: {price_data['market']}\n"
                response += f"Trend: {price_data['trend']}\n"
                response += f"Last Update: {price_data['updated']}\n\n"
                response += "For more info:\n"
                response += "- SMS PRICE to 45678\n"
                response += "- Web: farmconnect.zm\n"
                response += "Dial *384*7321# to continue"
                
                # Optionally send SMS with full details
                if session.get('phone'):
                    self.sms_service.send_price_alert(
                        session['phone'],
                        commodity,
                        price_data['price'],
                        price_data['market'],
                        price_data['trend']
                    )
                
                return response
            else:
                return f"END No price data available for {commodity}. Try later or visit web portal."
        
        return "END Invalid input. Dial *384*7321# to restart."
    
    def _show_forecast_menu(self):
        """Show forecast menu"""
        response = "CON Forecast for:\n"
        response += "1. Maize (7 days)\n"
        response += "2. Tomatoes (7 days)\n"
        response += "3. Beans (7 days)\n"
        response += "4. Groundnuts (7 days)\n"
        response += "5. Rice (7 days)\n"
        response += "6. Back to Main Menu\n"
        response += "Choose option:"
        return response
    
    def _handle_forecast_menu(self, session, parts):
        """Handle forecast menu selection"""
        if len(parts) == 1:
            option = parts[0]
            commodity_map = {
                '1': 'Maize', '2': 'Tomatoes', '3': 'Beans',
                '4': 'Groundnuts', '5': 'Rice', '6': 'back'
            }
            
            if option == '6':
                return self._show_main_menu(session)
            
            commodity = commodity_map.get(option)
            if not commodity:
                return "END Invalid option. Dial *384*7321# to restart."
            
            # Get forecast
            forecast = self._get_commodity_forecast(commodity)
            
            if forecast:
                response = f"END {commodity} Forecast (7 days):\n"
                response += "=======================\n"
                for day in forecast[:5]:  # Show 5 days
                    response += f"{day['date']}: ZMW {day['price']}/kg\n"
                    response += f"  Trend: {day['trend']}\n"
                response += "=======================\n"
                response += "Recommendation: Sell within 3 days for best price\n"
                response += "Dial *384*7321# to continue"
                
                # Send SMS forecast
                if session.get('phone'):
                    self.sms_service.send_forecast_alert(
                        session['phone'],
                        commodity,
                        forecast[0]['price'],
                        7,
                        'medium'
                    )
                
                return response
            else:
                return f"END No forecast data for {commodity}. Try later."
        
        return "END Invalid input. Dial *384*7321# to restart."
    
    def _show_buyer_menu(self):
        """Show buyer selection menu"""
        response = "CON Find Buyers for:\n"
        response += "1. Maize\n"
        response += "2. Tomatoes\n"
        response += "3. Beans\n"
        response += "4. Groundnuts\n"
        response += "5. Rice\n"
        response += "6. All Commodities\n"
        response += "7. Back to Main Menu\n"
        response += "Choose option:"
        return response
    
    def _handle_buyer_menu(self, session, parts):
        """Handle buyer menu selection"""
        if len(parts) == 1:
            option = parts[0]
            commodity_map = {
                '1': 'Maize', '2': 'Tomatoes', '3': 'Beans',
                '4': 'Groundnuts', '5': 'Rice', '6': 'All',
                '7': 'back'
            }
            
            if option == '7':
                return self._show_main_menu(session)
            
            commodity = commodity_map.get(option)
            if not commodity:
                return "END Invalid option. Dial *384*7321# to restart."
            
            # Get buyers
            buyers = self._get_buyers(commodity)
            
            if buyers:
                response = f"END Top Buyers for {commodity}:\n"
                response += "=======================\n"
                for i, buyer in enumerate(buyers[:3], 1):
                    response += f"{i}. {buyer['name']}\n"
                    response += f"   Price: ZMW {buyer['price']}/kg\n"
                    response += f"   Min: {buyer['min_volume']} kg\n"
                    response += f"   Phone: {buyer['phone']}\n\n"
                response += "=======================\n"
                response += "SMS BUYER to 45678 for more\n"
                response += "Dial *384*7321# to continue"
                
                # Send buyer contact via SMS
                if session.get('phone') and buyers:
                    top_buyer = buyers[0]
                    self.sms_service.send_buyer_contact(
                        session['phone'],
                        top_buyer['name'],
                        top_buyer['phone'],
                        commodity,
                        top_buyer['price']
                    )
                
                return response
            else:
                return f"END No buyers found for {commodity}. Check web portal for updates."
        
        return "END Invalid input. Dial *384*7321# to restart."
    
    def _show_account_menu(self, session):
        """Show account management menu"""
        response = "CON My Account\n"
        response += "=======================\n"
        response += "1. View Profile\n"
        response += "2. Change USSD PIN\n"
        response += "3. SMS Alerts Settings\n"
        response += "4. Request Price Alert\n"
        response += "5. Back to Main Menu\n"
        response += "Choose option:"
        return response
    
    def _handle_account_menu(self, session, parts):
        """Handle account menu selection"""
        if len(parts) == 1:
            option = parts[0]
            
            if option == '1':
                return self._view_profile(session)
            elif option == '2':
                return self._change_pin_prompt(session)
            elif option == '3':
                return self._sms_alerts_menu(session)
            elif option == '4':
                return self._request_price_alert(session)
            elif option == '5':
                return self._show_main_menu(session)
            else:
                return "END Invalid option. Dial *384*7321# to restart."
        
        elif len(parts) == 2:
            # Handle PIN change
            if session.get('state') == 'change_pin':
                return self._confirm_pin_change(session, parts[1])
        
        return "END Invalid input. Dial *384*7321# to restart."
    
    def _view_profile(self, session):
        """View user profile"""
        phone = session['phone']
        user = self._get_user_by_phone(phone)
        
        if user:
            response = f"END Profile Information\n"
            response += "=======================\n"
            response += f"Name: {user.get('name', 'Not set')}\n"
            response += f"Phone: {user['phone']}\n"
            response += f"Role: {user.get('role', 'Farmer')}\n"
            response += f"Location: {user.get('location', 'Not set')}\n"
            response += f"SMS Alerts: {'ON' if user.get('sms_alerts') else 'OFF'}\n"
            response += "=======================\n"
            response += "Dial *384*7321# to continue"
            return response
        else:
            return f"END Account not found. Please register on web: farmconnect.zm/register"
    
    def _change_pin_prompt(self, session):
        """Prompt for new PIN"""
        session['state'] = 'change_pin'
        return "CON Enter new 4-digit USSD PIN:"
    
    def _confirm_pin_change(self, session, new_pin):
        """Confirm PIN change"""
        if len(new_pin) == 4 and new_pin.isdigit():
            success = self._update_ussd_pin(session['phone'], new_pin)
            if success:
                return "END USSD PIN changed successfully! Use your new PIN next login.\nDial *384*7321# to continue"
            else:
                return "END Failed to change PIN. Please try again later."
        else:
            return "END Invalid PIN. Please use 4 digits only.\nDial *384*7321# to restart"
    
    def _sms_alerts_menu(self, session):
        """SMS alerts settings menu"""
        response = "CON SMS Alerts Settings\n"
        response += "=======================\n"
        response += "1. Enable SMS Alerts\n"
        response += "2. Disable SMS Alerts\n"
        response += "3. Back to Account Menu\n"
        response += "Choose option:"
        return response
    
    def _request_price_alert(self, session):
        """Request price alert for a commodity"""
        response = "CON Request Price Alert for:\n"
        response += "1. Maize\n"
        response += "2. Tomatoes\n"
        response += "3. Beans\n"
        response += "4. Groundnuts\n"
        response += "5. Rice\n"
        response += "Choose commodity:"
        return response
    
    def _show_weather_info(self):
        """Show weather information"""
        response = "END Weather Forecast (Zambia):\n"
        response += "=======================\n"
        response += "Lusaka: Sunny, 28°C\n"
        response += "Kabwe: Partly cloudy, 26°C\n"
        response += "Ndola: Light rain, 24°C\n"
        response += "Livingstone: Sunny, 32°C\n"
        response += "=======================\n"
        response += "Good for: Harvesting and drying\n"
        response += "Dial *384*7321# to continue"
        return response
    
    def _show_farming_tip(self):
        """Show farming tip"""
        tips = [
            "Plant maize 2 weeks before rains for best yield",
            "Rotate crops to improve soil fertility",
            "Use organic manure for better soil health",
            "Harvest early morning for freshness",
            "Store grains in dry, cool place with good ventilation",
            "Test soil before planting for optimal fertilizer use",
            "Water early morning or late evening to reduce evaporation"
        ]
        
        import random
        tip = random.choice(tips)
        
        response = f"END Farming Tip:\n"
        response += "=======================\n"
        response += f"{tip}\n"
        response += "=======================\n"
        response += "More tips at: farmconnect.zm/tips\n"
        response += "Dial *384*7321# to continue"
        return response
    
    def _get_commodity_price(self, commodity):
        """Get current price from database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute('''
                SELECT price, market, price_trend, recorded_at 
                FROM market_prices 
                WHERE commodity=? AND verified=1 
                ORDER BY recorded_at DESC LIMIT 1
            ''', (commodity,))
            
            result = cur.fetchone()
            conn.close()
            
            if result:
                return {
                    'price': result['price'],
                    'market': result['market'],
                    'trend': result['price_trend'] or 'stable',
                    'updated': result['recorded_at'][:10] if result['recorded_at'] else 'today'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None
    
    def _get_commodity_forecast(self, commodity, days=7):
        """Get forecast from database or generate"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database_path)
            cur = conn.cursor()
            
            # Try to get from cache
            cur.execute('''
                SELECT forecast_data FROM forecast_cache 
                WHERE commodity=? AND forecast_days=? 
                ORDER BY generated_at DESC LIMIT 1
            ''', (commodity, days))
            
            result = cur.fetchone()
            conn.close()
            
            if result:
                import json
                return json.loads(result[0])
            
            # Generate forecast if not cached
            return self._generate_forecast(commodity, days)
            
        except Exception as e:
            logger.error(f"Error getting forecast: {e}")
            return self._generate_forecast(commodity, days)
    
    def _generate_forecast(self, commodity, days=7):
        """Generate simple forecast"""
        import random
        from datetime import datetime, timedelta
        
        # Get current price
        price_data = self._get_commodity_price(commodity)
        current_price = price_data['price'] if price_data else 100
        
        forecast = []
        for i in range(1, days + 1):
            date = (datetime.now() + timedelta(days=i)).strftime("%d/%m")
            variation = random.uniform(-0.05, 0.07)  # -5% to +7%
            price = round(current_price * (1 + variation), 2)
            trend = "up" if variation > 0 else "down" if variation < 0 else "stable"
            
            forecast.append({
                'date': date,
                'price': price,
                'trend': trend
            })
        
        return forecast
    
    def _get_buyers(self, commodity):
        """Get buyers from database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            if commodity == 'All':
                cur.execute('''
                    SELECT name, phone, commodity, max_price, min_volume, rating
                    FROM buyers 
                    WHERE status='active' AND verified=1
                    ORDER BY rating DESC LIMIT 10
                ''')
            else:
                cur.execute('''
                    SELECT name, phone, commodity, max_price, min_volume, rating
                    FROM buyers 
                    WHERE commodity=? AND status='active' AND verified=1
                    ORDER BY rating DESC LIMIT 5
                ''', (commodity,))
            
            results = cur.fetchall()
            conn.close()
            
            buyers = []
            for row in results:
                buyers.append({
                    'name': row['name'],
                    'phone': row['phone'],
                    'price': row['max_price'] or 0,
                    'min_volume': row['min_volume'] or 0,
                    'rating': row['rating'] or 4
                })
            
            return buyers
            
        except Exception as e:
            logger.error(f"Error getting buyers: {e}")
            return []
    
    def _get_user_by_phone(self, phone):
        """Get user by phone number"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute('''
                SELECT user_id, username, name, role, phone, location, sms_alerts, ussd_pin
                FROM users 
                WHERE phone=? AND status='active'
            ''', (phone,))
            
            result = cur.fetchone()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def _update_ussd_pin(self, phone, new_pin):
        """Update user's USSD PIN"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database_path)
            cur = conn.cursor()
            
            cur.execute('''
                UPDATE users 
                SET ussd_pin=? 
                WHERE phone=? AND status='active'
            ''', (new_pin, phone))
            
            conn.commit()
            affected = cur.rowcount
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"Error updating PIN: {e}")
            return False
    
    def _cleanup_session(self, session):
        """Clean up session data"""
        # Remove from memory after 5 minutes of inactivity
        import threading
        
        def delayed_cleanup(session_id):
            import time
            time.sleep(300)  # 5 minutes
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        threading.Thread(target=delayed_cleanup, args=(session.get('id'),), daemon=True).start()