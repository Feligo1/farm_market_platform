#!/usr/bin/env python3
"""
USSD Menu Configuration for FarmConnect
Defines all USSD menu structures and navigation
Mulungushi University - ICT 431 Capstone Project
Student: Daka Felix (202206453)
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# =========================================================
# USSD MENU CONFIGURATION
# =========================================================

class USSDMenu:
    """USSD Menu Structure"""
    
    MAIN_MENU = {
        "1": "Market Prices",
        "2": "Price Forecast",
        "3": "Find Buyers",
        "4": "Weather Info",
        "5": "Farming Tips",
        "6": "My Account",
        "0": "Exit"
    }
    
    COMMODITIES = {
        "1": "Maize",
        "2": "Tomatoes", 
        "3": "Beans",
        "4": "Groundnuts",
        "5": "Rice",
        "6": "Soybeans",
        "7": "Sweet Potatoes",
        "8": "Cassava",
        "9": "Onions",
        "0": "Back"
    }
    
    FORECAST_DAYS = {
        "1": "7 Days",
        "2": "14 Days",
        "3": "30 Days",
        "0": "Back"
    }
    
    ACCOUNT_MENU = {
        "1": "View Profile",
        "2": "Change PIN",
        "3": "SMS Alerts",
        "4": "Price Alerts",
        "5": "My Subscriptions",
        "0": "Back"
    }
    
    MARKET_PRICES_SUB = {
        "1": "Lusaka",
        "2": "Kitwe",
        "3": "Ndola",
        "4": "Livingstone",
        "5": "Chipata",
        "6": "Kabwe",
        "7": "Solwezi",
        "0": "Back"
    }
    
    WEATHER_SUB = {
        "1": "Lusaka",
        "2": "Kabwe",
        "3": "Ndola",
        "4": "Kitwe",
        "5": "Livingstone",
        "6": "Chipata",
        "7": "Solwezi",
        "8": "Mansa",
        "0": "Back"
    }
    
    # Response messages
    WELCOME_MSG = "Welcome to FarmConnect Zambia! Your trusted market information platform."
    EXIT_MSG = "Thank you for using FarmConnect Zambia! Dial *384*7321# anytime to access market information."
    ERROR_MSG = "Invalid option. Please try again."
    NO_DATA_MSG = "No data available at the moment. Please try again later."
    
    @staticmethod
    def format_menu(title: str, options: Dict[str, str]) -> str:
        """Format USSD menu with title and options (CON - session continues)"""
        menu = f"CON {title}\n"
        menu += "─" * 30 + "\n"
        for key, value in options.items():
            menu += f"{key}. {value}\n"
        menu += "─" * 30 + "\n"
        menu += "Reply with option number:"
        return menu
    
    @staticmethod
    def format_response(title: str, content: str) -> str:
        """Format USSD response with title and content (END - session ends)"""
        response = f"END {title}\n"
        response += "─" * 30 + "\n"
        response += content
        response += "\n" + "─" * 30 + "\n"
        response += "Dial *384*7321# to return to main menu"
        return response
    
    @staticmethod
    def format_continue(title: str, content: str) -> str:
        """Format USSD continue (CON) response - session continues after this"""
        response = f"CON {title}\n"
        response += "─" * 30 + "\n"
        response += content
        response += "\n" + "─" * 30 + "\n"
        response += "Choose option:"
        return response
    
    @staticmethod
    def format_continue_response(title: str, content: str, options: Dict[str, str] = None) -> str:
        """Format USSD response that stays in CON mode for looping"""
        response = f"CON {title}\n"
        response += "─" * 30 + "\n"
        response += content
        response += "\n" + "─" * 30 + "\n"
        if options:
            for key, value in options.items():
                response += f"{key}. {value}\n"
            response += "0. Back to Main Menu\n"
            response += "─" * 30 + "\n"
            response += "Reply with option number:"
        else:
            response += "Press 0 to go back or * to return to main menu"
        return response


# =========================================================
# USSD SESSION MANAGER
# =========================================================

class USSDSessionManager:
    """Manage USSD sessions with persistence"""
    
    def __init__(self, db_connection=None):
        self.sessions = {}
        self.session_timeout = 300  # 5 minutes
        self.db = db_connection
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Check if session expired
            if (datetime.now() - session['last_activity']).total_seconds() > self.session_timeout:
                self.end_session(session_id)
                return None
            session['last_activity'] = datetime.now()
            return session
        return None
    
    def create_session(self, session_id: str, phone_number: str) -> Dict[str, Any]:
        """Create new session"""
        self.sessions[session_id] = {
            'phone': phone_number,
            'state': 'main',
            'menu_history': [],
            'data': {},
            'created': datetime.now(),
            'last_activity': datetime.now()
        }
        logger.info(f"Created session for {phone_number} with ID {session_id}")
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(data)
            self.sessions[session_id]['last_activity'] = datetime.now()
    
    def push_menu_state(self, session_id: str, state: str, menu_data: Dict = None) -> None:
        """Push new menu state onto history stack"""
        if session_id in self.sessions:
            self.sessions[session_id]['menu_history'].append({
                'state': self.sessions[session_id]['state'],
                'data': self.sessions[session_id]['data'].copy()
            })
            self.sessions[session_id]['state'] = state
            if menu_data:
                self.sessions[session_id]['data'].update(menu_data)
            self.sessions[session_id]['last_activity'] = datetime.now()
    
    def pop_menu_state(self, session_id: str) -> bool:
        """Pop previous menu state from history stack"""
        if session_id in self.sessions and self.sessions[session_id]['menu_history']:
            prev_state = self.sessions[session_id]['menu_history'].pop()
            self.sessions[session_id]['state'] = prev_state['state']
            self.sessions[session_id]['data'] = prev_state['data']
            self.sessions[session_id]['last_activity'] = datetime.now()
            return True
        return False
    
    def reset_to_main(self, session_id: str) -> None:
        """Reset session to main menu state"""
        if session_id in self.sessions:
            self.sessions[session_id]['state'] = 'main'
            self.sessions[session_id]['data'] = {}
            self.sessions[session_id]['menu_history'] = []
            self.sessions[session_id]['last_activity'] = datetime.now()
    
    def set_session_data(self, session_id: str, key: str, value: Any) -> None:
        """Set specific session data value"""
        if session_id in self.sessions:
            self.sessions[session_id]['data'][key] = value
            self.sessions[session_id]['last_activity'] = datetime.now()
    
    def get_session_data(self, session_id: str, key: str, default=None) -> Any:
        """Get specific session data value"""
        if session_id in self.sessions:
            return self.sessions[session_id]['data'].get(key, default)
        return default
    
    def end_session(self, session_id: str) -> None:
        """End session and clean up"""
        if session_id in self.sessions:
            phone = self.sessions[session_id].get('phone', 'unknown')
            logger.info(f"Ending session for {phone}")
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count removed"""
        expired = []
        for session_id, session in self.sessions.items():
            if (datetime.now() - session['last_activity']).total_seconds() > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            self.end_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)


# =========================================================
# ZAMBIAN WEATHER DATA
# =========================================================

ZAMBIAN_WEATHER = {
    'Lusaka': {'temp': 28, 'condition': 'Sunny', 'humidity': 45, 'rainfall': '0mm'},
    'Kabwe': {'temp': 26, 'condition': 'Partly Cloudy', 'humidity': 50, 'rainfall': '0mm'},
    'Ndola': {'temp': 24, 'condition': 'Light Rain', 'humidity': 70, 'rainfall': '5mm'},
    'Kitwe': {'temp': 25, 'condition': 'Cloudy', 'humidity': 65, 'rainfall': '2mm'},
    'Livingstone': {'temp': 32, 'condition': 'Sunny', 'humidity': 35, 'rainfall': '0mm'},
    'Chipata': {'temp': 27, 'condition': 'Clear', 'humidity': 48, 'rainfall': '0mm'},
    'Solwezi': {'temp': 23, 'condition': 'Rain', 'humidity': 75, 'rainfall': '8mm'},
    'Mansa': {'temp': 22, 'condition': 'Thunderstorms', 'humidity': 80, 'rainfall': '15mm'}
}

# Default price data for testing
DEFAULT_PRICES = {
    ('Maize', 'Lusaka'): 6.80,
    ('Maize', 'Kitwe'): 6.82,
    ('Maize', 'Ndola'): 6.78,
    ('Maize', 'Livingstone'): 6.75,
    ('Maize', 'Chipata'): 6.70,
    ('Tomatoes', 'Lusaka'): 8.50,
    ('Tomatoes', 'Kitwe'): 8.00,
    ('Beans', 'Lusaka'): 12.50,
    ('Groundnuts', 'Lusaka'): 18.00,
    ('Rice', 'Lusaka'): 9.00,
    ('Soybeans', 'Lusaka'): 15.00,
    ('Cassava', 'Lusaka'): 4.50,
    ('Sweet Potatoes', 'Lusaka'): 5.00,
    ('Onions', 'Lusaka'): 7.00,
}

# Default buyers data
DEFAULT_BUYERS = {
    'Maize': [
        {'name': 'Agri Trading Ltd', 'price': 140.00, 'min_volume': 1000, 'phone': '+260971111111', 'rating': 4.5},
        {'name': 'Grain Masters', 'price': 135.00, 'min_volume': 2000, 'phone': '+260973333333', 'rating': 4.2},
        {'name': 'Zambia Grain Ltd', 'price': 138.00, 'min_volume': 1500, 'phone': '+260974444444', 'rating': 4.0}
    ],
    'Tomatoes': [
        {'name': 'Fresh Produce Co.', 'price': 90.00, 'min_volume': 500, 'phone': '+260972222222', 'rating': 4.3}
    ],
    'Beans': [
        {'name': 'Organic Farms', 'price': 180.00, 'min_volume': 800, 'phone': '+260975555555', 'rating': 4.7}
    ]
}


# =========================================================
# USSD HANDLER - Main Processing Logic
# =========================================================

class USSDHandler:
    """Main USSD request handler"""
    
    def __init__(self, session_manager: USSDSessionManager, sms_service=None, db=None):
        self.session_manager = session_manager
        self.sms_service = sms_service
        self.db = db
        self.menu = USSDMenu()
    
    def handle_request(self, session_id: str, phone_number: str, text: str) -> str:
        """
        Main entry point for USSD request processing
        Returns USSD response string (CON for continue, END for exit)
        """
        # Get or create session
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(session_id, phone_number)
        
        # Parse input text - this is the full chain from AT
        # e.g., "" -> main menu, "1" -> commodity list, "1*1" -> price for maize
        parts = text.split('*') if text else []
        depth = len(parts)
        current_state = session.get('state', 'main')
        
        logger.info(f"USSD Request: session={session_id}, phone={phone_number}, text='{text}', depth={depth}, state={current_state}")
        
        # Handle exit
        if text == '0' and depth == 1 and current_state == 'main':
            self.session_manager.end_session(session_id)
            return self.menu.format_response("Goodbye", self.menu.EXIT_MSG)
        
        # Handle back navigation
        if parts and parts[-1] == '0' and depth > 1:
            # Go back one level
            if self.session_manager.pop_menu_state(session_id):
                # Return to previous menu
                prev_state = session.get('state', 'main')
                if prev_state == 'commodity_selection':
                    return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
                elif prev_state == 'forecast_commodity':
                    return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
                elif prev_state == 'buyer_commodity':
                    return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
                elif prev_state == 'account_menu':
                    return self.menu.format_menu("My Account", self.menu.ACCOUNT_MENU)
                elif prev_state == 'main':
                    return self.show_main_menu()
        
        # Handle main menu navigation
        if depth == 0:
            return self.show_main_menu()
        
        # Process based on current state
        try:
            if current_state == 'main':
                return self.process_main_menu(session_id, parts[0])
            elif current_state == 'commodity_selection':
                return self.process_commodity_selection(session_id, parts[-1])
            elif current_state == 'market_selection':
                return self.process_market_selection(session_id, parts[-1])
            elif current_state == 'forecast_commodity':
                return self.process_forecast_commodity(session_id, parts[-1])
            elif current_state == 'forecast_days':
                return self.process_forecast_days(session_id, parts[-1])
            elif current_state == 'buyer_commodity':
                return self.process_buyer_commodity(session_id, parts[-1])
            elif current_state == 'account_menu':
                return self.process_account_menu(session_id, parts[-1])
            elif current_state == 'change_pin':
                return self.process_change_pin(session_id, parts[-1])
            elif current_state == 'pin_confirmation':
                return self.process_pin_confirmation(session_id, parts[-1])
            elif current_state == 'alert_commodity':
                return self.process_alert_commodity(session_id, parts[-1])
            elif current_state == 'alert_threshold':
                return self.process_alert_threshold(session_id, parts[-1])
            elif current_state == 'weather_selection':
                return self.process_weather_selection(session_id, parts[-1])
            else:
                self.session_manager.reset_to_main(session_id)
                return self.show_main_menu()
                
        except Exception as e:
            logger.error(f"USSD handler error: {e}")
            return self.menu.format_response("Service Error", "Please try again later.")
    
    def show_main_menu(self) -> str:
        """Display main menu"""
        return self.menu.format_menu("FarmConnect Zambia", self.menu.MAIN_MENU)
    
    def process_main_menu(self, session_id: str, choice: str) -> str:
        """Process main menu selection"""
        
        if choice == '1':  # Market Prices
            self.session_manager.update_session(session_id, {'state': 'commodity_selection'})
            return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
        
        elif choice == '2':  # Price Forecast
            self.session_manager.update_session(session_id, {'state': 'forecast_commodity'})
            return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
        
        elif choice == '3':  # Find Buyers
            self.session_manager.update_session(session_id, {'state': 'buyer_commodity'})
            return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
        
        elif choice == '4':  # Weather Info
            self.session_manager.update_session(session_id, {'state': 'weather_selection'})
            return self.menu.format_menu("Select District", self.menu.WEATHER_SUB)
        
        elif choice == '5':  # Farming Tips
            return self.get_farming_tip(session_id)
        
        elif choice == '6':  # My Account
            self.session_manager.update_session(session_id, {'state': 'account_menu'})
            return self.menu.format_menu("My Account", self.menu.ACCOUNT_MENU)
        
        elif choice == '0':  # Exit
            self.session_manager.end_session(session_id)
            return self.menu.format_response("Goodbye", self.menu.EXIT_MSG)
        
        else:
            return self.menu.format_menu("Invalid Option\nTry Again", self.menu.MAIN_MENU)
    
    def process_weather_selection(self, session_id: str, choice: str) -> str:
        """Process weather district selection - returns to main menu after showing weather"""
        
        if choice == '0':
            self.session_manager.reset_to_main(session_id)
            return self.show_main_menu()
        
        district = self.menu.WEATHER_SUB.get(choice)
        if not district:
            return self.menu.format_menu("Invalid Option\nSelect District", self.menu.WEATHER_SUB)
        
        weather = ZAMBIAN_WEATHER.get(district, ZAMBIAN_WEATHER.get('Lusaka'))
        response = f"📍 Weather in {district}\n"
        response += f"🌡️ Temperature: {weather['temp']}°C\n"
        response += f"☁️ Condition: {weather['condition']}\n"
        response += f"💧 Humidity: {weather['humidity']}%\n"
        response += f"🌧️ Rainfall: {weather['rainfall']}\n\n"
        response += "Press 0 to go back to main menu"
        
        self.session_manager.reset_to_main(session_id)
        return self.menu.format_response("Weather Report", response)
    
    def process_commodity_selection(self, session_id: str, choice: str) -> str:
        """Process commodity selection for market prices"""
        
        if choice == '0':
            self.session_manager.reset_to_main(session_id)
            return self.show_main_menu()
        
        commodity = self.menu.COMMODITIES.get(choice)
        if not commodity:
            return self.menu.format_menu("Invalid Option\nSelect Commodity", self.menu.COMMODITIES)
        
        # Show markets for selected commodity
        self.session_manager.set_session_data(session_id, 'selected_commodity', commodity)
        self.session_manager.update_session(session_id, {'state': 'market_selection'})
        return self.menu.format_menu(f"{commodity} - Select Market", self.menu.MARKET_PRICES_SUB)
    
    def process_market_selection(self, session_id: str, choice: str) -> str:
        """Process market selection and show price - returns to main menu"""
        commodity = self.session_manager.get_session_data(session_id, 'selected_commodity')
        
        if choice == '0':
            self.session_manager.update_session(session_id, {'state': 'commodity_selection'})
            return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
        
        market = self.menu.MARKET_PRICES_SUB.get(choice)
        if not market:
            return self.menu.format_menu("Invalid Option\nSelect Market", self.menu.MARKET_PRICES_SUB)
        
        # Get price from database
        price = self.get_price_from_db(commodity, market)
        
        if price:
            response = f"📍 {commodity} at {market}\n"
            response += f"💰 Price: ZMW {price:.2f}/kg\n"
            response += f"📅 Updated: Today\n\n"
            response += "Press 0 to go back to main menu"
            
            self.session_manager.reset_to_main(session_id)
            return self.menu.format_response(f"{commodity} Price", response)
        else:
            return self.menu.format_response("No Data", self.menu.NO_DATA_MSG)
    
    def process_forecast_commodity(self, session_id: str, choice: str) -> str:
        """Process commodity selection for forecast"""
        
        if choice == '0':
            self.session_manager.reset_to_main(session_id)
            return self.show_main_menu()
        
        commodity = self.menu.COMMODITIES.get(choice)
        if not commodity:
            return self.menu.format_menu("Invalid Option\nSelect Commodity", self.menu.COMMODITIES)
        
        self.session_manager.set_session_data(session_id, 'forecast_commodity', commodity)
        self.session_manager.update_session(session_id, {'state': 'forecast_days'})
        return self.menu.format_menu("Select Forecast Period", self.menu.FORECAST_DAYS)
    
    def process_forecast_days(self, session_id: str, choice: str) -> str:
        """Process forecast days selection and show forecast - returns to main menu"""
        
        if choice == '0':
            self.session_manager.update_session(session_id, {'state': 'forecast_commodity'})
            return self.menu.format_menu("Select Commodity", self.menu.COMMODITIES)
        
        days_map = {"1": 7, "2": 14, "3": 30}
        days = days_map.get(choice)
        if not days:
            return self.menu.format_menu("Invalid Option\nSelect Period", self.menu.FORECAST_DAYS)
        
        commodity = self.session_manager.get_session_data(session_id, 'forecast_commodity')
        
        # Get forecast from database
        forecast = self.get_forecast_from_db(commodity, days)
        
        if forecast:
            response = f"📈 {commodity} Forecast ({days} days)\n"
            response += "─" * 25 + "\n"
            for i, f in enumerate(forecast[:5]):
                arrow = "▲" if f.get('trend') == 'up' else "▼"
                response += f"Day {i+1}: ZMW {f.get('price', 0):.2f} {arrow}\n"
            response += "─" * 25 + "\n"
            response += "Press 0 to go back to main menu"
            
            self.session_manager.reset_to_main(session_id)
            return self.menu.format_response(f"{commodity} Forecast", response)
        else:
            return self.menu.format_response("No Forecast", self.menu.NO_DATA_MSG)
    
    def process_buyer_commodity(self, session_id: str, choice: str) -> str:
        """Process buyer search by commodity - returns to main menu"""
        
        if choice == '0':
            self.session_manager.reset_to_main(session_id)
            return self.show_main_menu()
        
        commodity = self.menu.COMMODITIES.get(choice)
        if not commodity:
            return self.menu.format_menu("Invalid Option\nSelect Commodity", self.menu.COMMODITIES)
        
        # Get buyers from database
        buyers = self.get_buyers_from_db(commodity)
        
        if buyers:
            response = f"🏢 Buyers for {commodity}\n"
            response += "─" * 25 + "\n"
            for i, b in enumerate(buyers[:3]):
                stars = "★" * int(b.get('rating', 4)) + "☆" * (5 - int(b.get('rating', 4)))
                response += f"{i+1}. {b.get('name', 'N/A')} {stars}\n"
                response += f"   💰 Price: ZMW {b.get('price', 0):.2f}/kg\n"
                response += f"   📦 Min: {b.get('min_volume', 0)}kg\n"
                response += f"   📞 {b.get('phone', 'N/A')}\n\n"
            response += "Press 0 to go back to main menu"
            
            self.session_manager.reset_to_main(session_id)
            return self.menu.format_response("Buyers Found", response)
        else:
            return self.menu.format_response("No Buyers", f"No buyers found for {commodity}.\nPress 0 to go back")
    
    def process_account_menu(self, session_id: str, choice: str) -> str:
        """Process account menu selection"""
        
        if choice == '0':
            self.session_manager.reset_to_main(session_id)
            return self.show_main_menu()
        
        elif choice == '1':  # View Profile
            profile = self.get_user_profile(session_id)
            if profile:
                response = f"👤 Profile\n"
                response += f"Name: {profile.get('name', 'N/A')}\n"
                response += f"Role: {profile.get('role', 'Farmer')}\n"
                response += f"Location: {profile.get('location', 'N/A')}\n"
                response += f"SMS Alerts: {'ON' if profile.get('sms_alerts') else 'OFF'}\n\n"
                response += "Press 0 to go back to main menu"
                return self.menu.format_response("My Profile", response)
            else:
                return self.menu.format_response("No Account", "Please register at farmconnect.zm")
        
        elif choice == '2':  # Change PIN
            self.session_manager.update_session(session_id, {'state': 'change_pin'})
            return self.menu.format_continue("Change USSD PIN", "Enter new 4-digit PIN:")
        
        elif choice == '3':  # SMS Alerts
            status = self.toggle_sms_alerts(session_id)
            response = f"SMS alerts are now {status}\n\nPress 0 to go back to main menu"
            self.session_manager.reset_to_main(session_id)
            return self.menu.format_response("SMS Alerts", response)
        
        elif choice == '4':  # Price Alerts
            self.session_manager.update_session(session_id, {'state': 'alert_commodity'})
            return self.menu.format_menu("Set Price Alert\nSelect Commodity", self.menu.COMMODITIES)
        
        elif choice == '5':  # My Subscriptions
            subscriptions = self.get_subscriptions(session_id)
            if subscriptions:
                response = "📋 Your Subscriptions\n"
                response += "─" * 25 + "\n"
                for sub in subscriptions:
                    response += f"• {sub.get('commodity', 'N/A')} at {sub.get('threshold', 5)}%\n"
                response += "\nPress 0 to go back to main menu"
                return self.menu.format_response("Subscriptions", response)
            else:
                return self.menu.format_response("No Subscriptions", "You have no active subscriptions")
        
        else:
            return self.menu.format_menu("Invalid Option\nMy Account", self.menu.ACCOUNT_MENU)
    
    def process_change_pin(self, session_id: str, pin: str) -> str:
        """Process PIN change"""
        
        if len(pin) != 4 or not pin.isdigit():
            return self.menu.format_continue("Change USSD PIN", "Invalid PIN.\nEnter 4-digit PIN:")
        
        self.session_manager.set_session_data(session_id, 'new_pin', pin)
        self.session_manager.update_session(session_id, {'state': 'pin_confirmation'})
        return self.menu.format_continue("Confirm New PIN", f"Confirm your new PIN:\n{pin}\n\nType the same PIN again:")
    
    def process_pin_confirmation(self, session_id: str, confirm_pin: str) -> str:
        """Process PIN confirmation"""
        
        new_pin = self.session_manager.get_session_data(session_id, 'new_pin')
        
        if confirm_pin == new_pin:
            success = self.save_user_pin(session_id, new_pin)
            if success:
                response = "✅ PIN changed successfully!\nUse your new PIN for USSD access.\n\nPress 0 to go back"
                self.session_manager.reset_to_main(session_id)
                return self.menu.format_response("PIN Changed", response)
            else:
                return self.menu.format_response("Error", "Failed to change PIN. Try again.")
        else:
            return self.menu.format_continue("PIN Mismatch", "PINs do not match.\nEnter new 4-digit PIN:")
    
    def process_alert_commodity(self, session_id: str, choice: str) -> str:
        """Process alert commodity selection"""
        
        if choice == '0':
            self.session_manager.update_session(session_id, {'state': 'account_menu'})
            return self.menu.format_menu("My Account", self.menu.ACCOUNT_MENU)
        
        commodity = self.menu.COMMODITIES.get(choice)
        if not commodity:
            return self.menu.format_menu("Invalid Option\nSelect Commodity", self.menu.COMMODITIES)
        
        self.session_manager.set_session_data(session_id, 'alert_commodity', commodity)
        self.session_manager.update_session(session_id, {'state': 'alert_threshold'})
        return self.menu.format_continue("Set Alert Threshold", f"Enter threshold % for {commodity}:\n(Alert when price changes by this %)\n\nExample: 5")
    
    def process_alert_threshold(self, session_id: str, threshold: str) -> str:
        """Process alert threshold and create alert"""
        
        try:
            threshold_val = float(threshold)
            if threshold_val < 1 or threshold_val > 50:
                return self.menu.format_continue("Invalid Threshold", "Threshold must be between 1% and 50%\n\nEnter threshold %:")
        except ValueError:
            return self.menu.format_continue("Invalid Input", "Please enter a number (1-50):")
        
        commodity = self.session_manager.get_session_data(session_id, 'alert_commodity')
        
        # Save alert to database
        success = self.save_price_alert(session_id, commodity, threshold_val)
        
        if success:
            response = f"✅ Alert set for {commodity}!\nYou will be notified when price changes by {threshold_val}%\n\nPress 0 to go back"
            self.session_manager.reset_to_main(session_id)
            return self.menu.format_response("Alert Set", response)
        else:
            return self.menu.format_response("Error", "Failed to set alert. Try again.")
    
    def get_farming_tip(self, session_id: str) -> str:
        """Get farming tip - returns to main menu"""
        tips = [
            "🌱 Plant maize 2 weeks before rains for best yield",
            "🔄 Rotate crops every season to improve soil fertility",
            "💩 Use organic manure to reduce fertilizer costs",
            "🌅 Harvest early morning to keep produce fresh longer",
            "🏺 Store grains in dry, ventilated places to prevent mould",
            "🧪 Test your soil before planting for optimal fertilizer use",
            "🤝 Join a farmer cooperative to get better prices",
            "💧 Water early morning or late evening to reduce evaporation",
            "🌾 Mulching helps retain soil moisture and suppress weeds",
            "📊 Monitor market prices daily to sell at peak times",
            "🐝 Use integrated pest management for healthier crops",
            "🌿 Practice crop rotation to maintain soil health"
        ]
        import random
        tip = random.choice(tips)
        response = f"{tip}\n\nPress 0 to go back to main menu"
        
        self.session_manager.reset_to_main(session_id)
        return self.menu.format_response("Farming Tip", response)
    
    # =========================================================
    # DATABASE HELPER METHODS
    # =========================================================
    
    def get_price_from_db(self, commodity: str, market: str) -> float:
        """Get price from database"""
        return DEFAULT_PRICES.get((commodity, market), None)
    
    def get_forecast_from_db(self, commodity: str, days: int) -> list:
        """Get forecast from database"""
        base_price = DEFAULT_PRICES.get((commodity, 'Lusaka'), 10.00)
        forecast = []
        current = base_price
        for i in range(1, days + 1):
            # Simple forecast: slight upward trend with some variation
            change = 0.01 + (i * 0.001) + (random.random() - 0.5) * 0.005
            current = current * (1 + change)
            forecast.append({
                'price': current,
                'trend': 'up' if change > 0 else 'down'
            })
        return forecast
    
    def get_buyers_from_db(self, commodity: str) -> list:
        """Get buyers from database"""
        return DEFAULT_BUYERS.get(commodity, [])
    
    def get_user_profile(self, session_id: str) -> dict:
        """Get user profile from database"""
        phone = self.session_manager.get_session_data(session_id, 'phone', '')
        return {'name': 'John Farmer', 'role': 'farmer', 'location': 'Lusaka', 'sms_alerts': True}
    
    def save_user_pin(self, session_id: str, pin: str) -> bool:
        """Save user PIN to database"""
        logger.info(f"Saving PIN for session {session_id}")
        return True
    
    def toggle_sms_alerts(self, session_id: str) -> str:
        """Toggle SMS alerts"""
        return "ON"
    
    def get_subscriptions(self, session_id: str) -> list:
        """Get user subscriptions"""
        return []
    
    def save_price_alert(self, session_id: str, commodity: str, threshold: float) -> bool:
        """Save price alert to database"""
        logger.info(f"Saving alert for {commodity} with threshold {threshold}%")
        return True


# =========================================================
# FACTORY FUNCTION
# =========================================================

def create_ussd_handler(db=None, sms_service=None) -> USSDHandler:
    """Factory function to create USSD handler instance"""
    session_manager = USSDSessionManager(db)
    return USSDHandler(session_manager, sms_service, db)