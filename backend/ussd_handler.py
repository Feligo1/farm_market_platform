# =========================================================
# ussd_handler.py - Africa's Talking USSD Integration
# =========================================================

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AfricaTalkingUSSD:
    """
    Africa's Talking USSD Handler
    This class handles USSD requests from Africa's Talking gateway
    """
    
    def __init__(self, api_key: str = None, username: str = "sandbox"):
        """
        Initialize Africa's Talking USSD handler
        
        Args:
            api_key: Africa's Talking API key
            username: Africa's Talking username (default: sandbox)
        """
        self.api_key = api_key or os.getenv('AFRICASTALKING_API_KEY')
        self.username = username
        self.service_code = "*384*7321#"
        self.sessions = {}
        
        # Initialize Africa's Talking SDK if available
        try:
            import africastalking
            africastalking.initialize(username, self.api_key)
            self.africastalking = africastalking
            self.initialized = True
            logger.info("✅ Africa's Talking USSD SDK initialized")
        except ImportError:
            logger.warning("⚠️  Africa's Talking SDK not installed. Using mock mode.")
            self.initialized = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Africa's Talking: {e}")
            self.initialized = False
    
    def handle_ussd_request(self, session_id: str, phone_number: str, text: str) -> str:
        """
        Main USSD request handler - this is the entry point for Africa's Talking
        
        Args:
            session_id: Unique session identifier
            phone_number: User's phone number in international format
            text: User's input (empty for first request)
            
        Returns:
            USSD response with CON or END prefix
        """
        try:
            # Format phone number to standard format
            phone_number = self._format_phone_number(phone_number)
            
            # Get or create session
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "phone": phone_number,
                    "state": "start",
                    "data": {},
                    "created": datetime.now(),
                    "last_activity": datetime.now()
                }
            
            session = self.sessions[session_id]
            session["last_activity"] = datetime.now()
            
            # Log the request
            logger.info(f"📱 USSD Request - Session: {session_id}, Phone: {phone_number}, Text: '{text}'")
            
            # Process based on current state
            if text == "":
                # First request - show main menu
                response = self._get_main_menu()
                session["state"] = "main_menu"
                return response
            
            elif text == "0":
                # Exit
                self._cleanup_session(session_id)
                return "END Thank you for using FarmConnect! Dial *384*7321# again for more information."
            
            elif text == "1":
                # Market Prices menu
                response = self._get_commodity_menu()
                session["state"] = "price_menu"
                return response
            
            elif text == "2":
                # Price Forecast menu
                response = self._get_forecast_menu()
                session["state"] = "forecast_menu"
                return response
            
            elif text == "3":
                # Find Buyers menu
                response = self._get_buyer_menu()
                session["state"] = "buyer_menu"
                return response
            
            elif text == "4":
                # Weather Info
                weather = self._get_weather_info()
                return f"END {weather}\n\nReply 0 to exit or dial *384*7321# to start over."
            
            elif text == "5":
                # Farming Tips
                tip = self._get_farming_tip()
                return f"END {tip}\n\nReply 0 to exit or dial *384*7321# to start over."
            
            elif text == "99":
                # Help
                return self._get_help_menu()
            
            # Handle nested menus
            elif session["state"] == "price_menu" and text.isdigit():
                return self._handle_price_selection(session, text)
            
            elif session["state"] == "forecast_menu" and text.isdigit():
                return self._handle_forecast_selection(session, text)
            
            elif session["state"] == "buyer_menu" and text.isdigit():
                return self._handle_buyer_selection(session, text)
            
            else:
                # Invalid input
                return self._get_invalid_menu()
                
        except Exception as e:
            logger.error(f"❌ USSD handler error: {e}")
            return "END Service temporarily unavailable. Please try again later."
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to standard format"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Check if it's a Zambian number
        if len(phone) == 9:
            phone = f"+260{phone}"
        elif len(phone) == 10 and phone.startswith('0'):
            phone = f"+260{phone[1:]}"
        elif len(phone) == 12 and phone.startswith('260'):
            phone = f"+{phone}"
        elif not phone.startswith('+'):
            phone = f"+{phone}"
        
        return phone
    
    def _get_main_menu(self) -> str:
        """Generate main menu"""
        menu = "CON 🌾 FarmConnect Zambia\n"
        menu += "=" * 25 + "\n"
        menu += "1️⃣ Check Market Prices\n"
        menu += "2️⃣ Price Forecast\n"
        menu += "3️⃣ Find Buyers\n"
        menu += "4️⃣ Weather Info\n"
        menu += "5️⃣ Farming Tips\n"
        menu += "9️⃣ Help\n"
        menu += "0️⃣ Exit\n"
        menu += "=" * 25 + "\n"
        menu += "Select option:"
        return menu
    
    def _get_commodity_menu(self) -> str:
        """Generate commodity selection menu"""
        menu = "CON 📊 Select Commodity:\n"
        menu += "=" * 25 + "\n"
        menu += "1️⃣ Maize\n"
        menu += "2️⃣ Tomatoes\n"
        menu += "3️⃣ Beans\n"
        menu += "4️⃣ Groundnuts\n"
        menu += "5️⃣ Rice\n"
        menu += "6️⃣ Soybeans\n"
        menu += "0️⃣ Back to Main Menu\n"
        menu += "=" * 25 + "\n"
        menu += "Select option:"
        return menu
    
    def _get_forecast_menu(self) -> str:
        """Generate forecast menu"""
        menu = "CON 📈 Price Forecast:\n"
        menu += "=" * 25 + "\n"
        menu += "1️⃣ Maize (7-day)\n"
        menu += "2️⃣ Tomatoes (7-day)\n"
        menu += "3️⃣ Beans (7-day)\n"
        menu += "4️⃣ Groundnuts (7-day)\n"
        menu += "0️⃣ Back to Main Menu\n"
        menu += "=" * 25 + "\n"
        menu += "Select option:"
        return menu
    
    def _get_buyer_menu(self) -> str:
        """Generate buyer menu"""
        menu = "CON 👥 Find Buyers:\n"
        menu += "=" * 25 + "\n"
        menu += "1️⃣ Maize Buyers\n"
        menu += "2️⃣ Tomato Buyers\n"
        menu += "3️⃣ Bean Buyers\n"
        menu += "4️⃣ Groundnut Buyers\n"
        menu += "5️⃣ All Buyers\n"
        menu += "0️⃣ Back to Main Menu\n"
        menu += "=" * 25 + "\n"
        menu += "Select option:"
        return menu
    
    def _get_help_menu(self) -> str:
        """Generate help menu"""
        help_text = "END ℹ️ FarmConnect Help\n"
        help_text += "=" * 25 + "\n"
        help_text += "How to use:\n"
        help_text += "• Select numbers to navigate\n"
        help_text += "• Press 0 to go back\n"
        help_text += "• Press 0 twice to exit\n\n"
        help_text += "Services:\n"
        help_text += "1 - Check market prices\n"
        help_text += "2 - Get price forecasts\n"
        help_text += "3 - Find buyers\n"
        help_text += "4 - Weather updates\n"
        help_text += "5 - Farming tips\n\n"
        help_text += "Need more help?\n"
        help_text += "SMS HELP to 45678 or\n"
        help_text += "Visit farmconnect.zm\n"
        help_text += "=" * 25
        return help_text
    
    def _get_invalid_menu(self) -> str:
        """Generate invalid input menu"""
        return "CON ❌ Invalid option!\n\n1️⃣ Try again\n0️⃣ Exit\n\nSelect option:"
    
    def _handle_price_selection(self, session: dict, option: str) -> str:
        """Handle commodity price selection"""
        commodities = {
            "1": "Maize",
            "2": "Tomatoes",
            "3": "Beans",
            "4": "Groundnuts",
            "5": "Rice",
            "6": "Soybeans"
        }
        
        if option == "0":
            # Go back to main menu
            session["state"] = "main_menu"
            return self._get_main_menu()
        
        commodity = commodities.get(option)
        if not commodity:
            return self._get_invalid_menu()
        
        # Get price from database or API
        price_data = self._get_commodity_price(commodity)
        
        if price_data:
            response = f"END 📊 {commodity} Prices\n"
            response += "=" * 25 + "\n"
            response += f"Current: ZMW {price_data['price']}/kg\n"
            response += f"Market: {price_data['market']}\n"
            response += f"Trend: {price_data['trend']}\n"
            response += f"Updated: {price_data['updated']}\n"
            response += "=" * 25 + "\n"
            response += "Reply 0 to exit or\n"
            response += "Dial *384*7321# to start over"
        else:
            response = f"END Sorry, no price data available for {commodity}\n\nPlease try again later."
        
        # Clean up session
        self._cleanup_session(session.get("session_id"))
        return response
    
    def _handle_forecast_selection(self, session: dict, option: str) -> str:
        """Handle forecast selection"""
        commodities = {
            "1": "Maize",
            "2": "Tomatoes",
            "3": "Beans",
            "4": "Groundnuts"
        }
        
        if option == "0":
            session["state"] = "main_menu"
            return self._get_main_menu()
        
        commodity = commodities.get(option)
        if not commodity:
            return self._get_invalid_menu()
        
        # Get forecast
        forecast = self._get_commodity_forecast(commodity)
        
        response = f"END 📈 {commodity} 7-Day Forecast\n"
        response += "=" * 25 + "\n"
        for day in forecast:
            response += f"{day['date']}: ZMW {day['price']}\n"
            response += f"  Trend: {day['trend']}\n"
        response += "=" * 25 + "\n"
        response += "Tip: Sell when price is high!\n"
        response += "Reply 0 to exit"
        
        self._cleanup_session(session.get("session_id"))
        return response
    
    def _handle_buyer_selection(self, session: dict, option: str) -> str:
        """Handle buyer selection"""
        buyers_map = {
            "1": "Maize",
            "2": "Tomatoes",
            "3": "Beans",
            "4": "Groundnuts",
            "5": "All"
        }
        
        if option == "0":
            session["state"] = "main_menu"
            return self._get_main_menu()
        
        commodity = buyers_map.get(option)
        if not commodity:
            return self._get_invalid_menu()
        
        # Get buyers
        buyers = self._get_buyers(commodity)
        
        response = f"END 👥 "
        if commodity == "All":
            response += "All Buyers\n"
        else:
            response += f"{commodity} Buyers\n"
        response += "=" * 25 + "\n"
        
        if buyers:
            for i, buyer in enumerate(buyers[:5], 1):
                response += f"{i}. {buyer['name']}\n"
                response += f"   📞 {buyer['phone']}\n"
                if buyer.get('location'):
                    response += f"   📍 {buyer['location']}\n"
                response += "\n"
        else:
            response += "No buyers found at the moment.\n"
            response += "Check back later!\n"
        
        response += "=" * 25 + "\n"
        response += "Reply 0 to exit"
        
        self._cleanup_session(session.get("session_id"))
        return response
    
    def _get_commodity_price(self, commodity: str) -> Optional[Dict]:
        """Get commodity price from database"""
        try:
            # Try to get from database
            from app import get_db
            conn = get_db()
            cur = conn.cursor()
            
            # Check if we're using PostgreSQL or SQLite
            if hasattr(conn, 'execute') and 'postgresql' in str(type(conn)):
                cur.execute("""
                    SELECT price, market, price_trend, recorded_at 
                    FROM market_prices 
                    WHERE commodity = %s AND verified = 1 
                    ORDER BY recorded_at DESC LIMIT 1
                """, (commodity,))
            else:
                cur.execute("""
                    SELECT price, market, price_trend, recorded_at 
                    FROM market_prices 
                    WHERE commodity = ? AND verified = 1 
                    ORDER BY recorded_at DESC LIMIT 1
                """, (commodity,))
            
            result = cur.fetchone()
            
            if hasattr(conn, 'close'):
                conn.close()
            
            if result:
                return {
                    "price": result['price'],
                    "market": result['market'],
                    "trend": result.get('price_trend', 'stable'),
                    "updated": self._format_date(result['recorded_at'])
                }
            
            # Fallback to sample data
            return self._get_sample_price(commodity)
            
        except Exception as e:
            logger.error(f"Error getting price for {commodity}: {e}")
            return self._get_sample_price(commodity)
    
    def _get_sample_price(self, commodity: str) -> Dict:
        """Get sample price data"""
        import random
        base_prices = {
            "Maize": (120, 180),
            "Tomatoes": (80, 150),
            "Beans": (160, 250),
            "Groundnuts": (180, 280),
            "Rice": (200, 300),
            "Soybeans": (150, 220)
        }
        
        min_price, max_price = base_prices.get(commodity, (100, 200))
        price = round(random.uniform(min_price, max_price), 2)
        
        trends = ["rising 📈", "falling 📉", "stable ➡️"]
        trend = random.choice(trends)
        
        markets = ["Lusaka Market", "Kabwe Market", "Ndola Market", "Livingstone Market"]
        market = random.choice(markets)
        
        return {
            "price": price,
            "market": market,
            "trend": trend,
            "updated": datetime.now().strftime("%H:%M, %d/%m/%Y")
        }
    
    def _get_commodity_forecast(self, commodity: str, days: int = 7) -> List[Dict]:
        """Get price forecast"""
        import random
        base_price = self._get_commodity_price(commodity)["price"]
        
        forecast = []
        for i in range(1, days + 1):
            date = (datetime.now() + timedelta(days=i)).strftime("%d/%m")
            variation = random.uniform(-0.08, 0.12)  # -8% to +12%
            price = round(base_price * (1 + variation), 2)
            trend = "📈 Up" if variation > 0.03 else "📉 Down" if variation < -0.03 else "➡️ Stable"
            
            forecast.append({
                "date": date,
                "price": price,
                "trend": trend
            })
        
        return forecast
    
    def _get_buyers(self, commodity: str) -> List[Dict]:
        """Get buyers from database"""
        try:
            from app import get_db
            conn = get_db()
            cur = conn.cursor()
            
            if commodity == "All":
                if hasattr(conn, 'execute') and 'postgresql' in str(type(conn)):
                    cur.execute("""
                        SELECT name, phone, location, commodity 
                        FROM buyers 
                        WHERE status = 'active' AND verified = 1
                        ORDER BY rating DESC LIMIT 10
                    """)
                else:
                    cur.execute("""
                        SELECT name, phone, location, commodity 
                        FROM buyers 
                        WHERE status = 'active' AND verified = 1
                        ORDER BY rating DESC LIMIT 10
                    """)
            else:
                if hasattr(conn, 'execute') and 'postgresql' in str(type(conn)):
                    cur.execute("""
                        SELECT name, phone, location, commodity 
                        FROM buyers 
                        WHERE commodity LIKE %s AND status = 'active' AND verified = 1
                        ORDER BY rating DESC LIMIT 10
                    """, (f'%{commodity}%',))
                else:
                    cur.execute("""
                        SELECT name, phone, location, commodity 
                        FROM buyers 
                        WHERE commodity LIKE ? AND status = 'active' AND verified = 1
                        ORDER BY rating DESC LIMIT 10
                    """, (f'%{commodity}%',))
            
            buyers = [dict(row) for row in cur.fetchall()]
            
            if hasattr(conn, 'close'):
                conn.close()
            
            if buyers:
                return buyers
            
            # Sample buyers
            return [
                {"name": "Agri Trading Ltd", "phone": "0971111111", "location": "Lusaka"},
                {"name": "Farm Produce Co.", "phone": "0972222222", "location": "Kabwe"},
                {"name": "Grain Masters", "phone": "0973333333", "location": "Ndola"}
            ]
            
        except Exception as e:
            logger.error(f"Error getting buyers: {e}")
            return [
                {"name": "Agri Trading Ltd", "phone": "0971111111", "location": "Lusaka"},
                {"name": "Farm Produce Co.", "phone": "0972222222", "location": "Kabwe"}
            ]
    
    def _get_weather_info(self) -> str:
        """Get weather information"""
        import random
        weather_options = [
            "☀️ Sunny, 32°C\nGood for drying crops",
            "🌤️ Partly cloudy, 28°C\nGood for fieldwork",
            "🌧️ Light rain expected\nGood for planting",
            "⛈️ Heavy rains forecast\nHarvest quickly!",
            "💨 Dry and windy\nIrrigate if possible"
        ]
        return random.choice(weather_options)
    
    def _get_farming_tip(self) -> str:
        """Get farming tip"""
        import random
        tips = [
            "🌽 Maize: Plant 2 weeks before rains for best yield",
            "🔄 Rotate crops to improve soil fertility",
            "💩 Use organic manure for better soil health",
            "🌅 Harvest early morning for freshness",
            "🏠 Store grains in dry, cool place",
            "💧 Water tomatoes in morning to prevent disease",
            "🐛 Check crops weekly for pests",
            "🌾 Save quality seeds for next season"
        ]
        return random.choice(tips)
    
    def _format_date(self, date_str: str) -> str:
        """Format date string"""
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime("%H:%M, %d/%m/%Y")
        except:
            pass
        return "Today"
    
    def _cleanup_session(self, session_id: str):
        """Clean up USSD session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_old_sessions(self):
        """Remove old sessions (called by scheduler)"""
        now = datetime.now()
        expired = []
        
        for sid, session in self.sessions.items():
            if (now - session["last_activity"]).seconds > 300:  # 5 minutes
                expired.append(sid)
        
        for sid in expired:
            del self.sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired USSD sessions")