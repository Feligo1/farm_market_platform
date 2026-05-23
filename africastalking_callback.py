# africastalking_callback.py
"""
Africa's Talking Callback Handlers
Handles SMS delivery reports and USSD callbacks
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

callback_bp = Blueprint('callback', __name__)

@callback_bp.route('/africastalking/sms/callback', methods=['POST'])
def sms_callback():
    """
    Handle SMS delivery reports from Africa's Talking
    """
    try:
        data = request.get_json()
        
        if data and 'data' in data:
            for message in data['data']:
                message_id = message.get('id')
                phone_number = message.get('to')
                status = message.get('status')
                status_code = message.get('statusCode')
                network_code = message.get('networkCode')
                
                logger.info(f"SMS Delivery Report: {message_id} - {phone_number} - {status}")
                
                # Update SMS status in database
                update_sms_delivery_status(message_id, status, status_code)
                
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"SMS callback error: {e}")
        return jsonify({"status": "error"}), 500

@callback_bp.route('/africastalking/ussd/callback', methods=['POST'])
def ussd_callback():
    """
    Handle USSD requests from Africa's Talking
    This is the main USSD callback endpoint
    """
    try:
        # Get request data
        session_id = request.form.get('sessionId')
        phone_number = request.form.get('phoneNumber')
        service_code = request.form.get('serviceCode')
        text = request.form.get('text', '')
        
        logger.info(f"USSD Callback: Session={session_id}, Phone={phone_number}, Text={text}")
        
        # Process USSD request
        from app import ussd_service
        response = ussd_service.handle_ussd(session_id, phone_number, text, service_code)
        
        return response, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"USSD callback error: {e}")
        return "END Service error. Please try again later.", 200

@callback_bp.route('/africastalking/airtime/callback', methods=['POST'])
def airtime_callback():
    """
    Handle airtime delivery reports from Africa's Talking
    """
    try:
        data = request.get_json()
        
        if data and 'data' in data:
            for transaction in data['data']:
                transaction_id = transaction.get('id')
                phone_number = transaction.get('phoneNumber')
                amount = transaction.get('amount')
                status = transaction.get('status')
                
                logger.info(f"Airtime Delivery: {transaction_id} - {phone_number} - {status} - {amount}")
                
                # Log airtime transaction
                log_airtime_transaction(transaction_id, phone_number, amount, status)
                
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Airtime callback error: {e}")
        return jsonify({"status": "error"}), 500

def update_sms_delivery_status(message_id, status, status_code):
    """Update SMS delivery status in database"""
    try:
        import sqlite3
        conn = sqlite3.connect('farm_market.db')
        cur = conn.cursor()
        
        cur.execute('''
            UPDATE sms_history 
            SET delivery_status = ?, status_code = ?, delivery_time = ?
            WHERE message_id = ?
        ''', (status, status_code, datetime.now().isoformat(), message_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to update SMS status: {e}")

def log_airtime_transaction(transaction_id, phone_number, amount, status):
    """Log airtime transaction to database"""
    try:
        import sqlite3
        conn = sqlite3.connect('farm_market.db')
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS airtime_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                phone_number TEXT,
                amount REAL,
                status TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        cur.execute('''
            INSERT INTO airtime_transactions (transaction_id, phone_number, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (transaction_id, phone_number, amount, status, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to log airtime transaction: {e}")