# mobile_ussd.py - Mobile-friendly USSD interface
from flask import Flask, render_template_string, request, jsonify
import requests
import json

app = Flask(__name__)
BASE_URL = "http://127.0.0.1:5000"  # Your local Flask app

@app.route('/mobile-ussd')
def mobile_ussd():
    """Mobile-optimized USSD interface"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📱 FarmConnect USSD</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                -webkit-tap-highlight-color: transparent;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #2E8B57 0%, #1f6b43 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 100%;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 20px;
                padding: 20px;
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            
            .header h1 {
                font-size: 24px;
                margin-bottom: 10px;
                color: white;
            }
            
            .ussd-code {
                font-size: 32px;
                font-weight: bold;
                background: rgba(0,0,0,0.3);
                padding: 15px;
                border-radius: 10px;
                display: inline-block;
                margin: 10px 0;
            }
            
            .screen {
                background: rgba(0, 0, 0, 0.8);
                color: #00FF00;
                padding: 25px;
                border-radius: 15px;
                min-height: 300px;
                margin-bottom: 20px;
                font-family: 'Courier New', monospace;
                font-size: 18px;
                line-height: 1.6;
                white-space: pre-wrap;
                overflow-y: auto;
                border: 2px solid rgba(255,255,255,0.1);
            }
            
            .input-container {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .input-container input {
                flex: 1;
                padding: 18px;
                font-size: 20px;
                border: none;
                border-radius: 10px;
                background: rgba(255,255,255,0.9);
                text-align: center;
                font-weight: bold;
            }
            
            .btn {
                background: #FFA500;
                color: white;
                border: none;
                padding: 18px 25px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .btn:hover, .btn:active {
                background: #FF8C00;
                transform: translateY(-2px);
            }
            
            .keypad {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .key {
                background: rgba(255,255,255,0.15);
                color: white;
                border: 2px solid rgba(255,255,255,0.2);
                padding: 25px;
                font-size: 28px;
                font-weight: bold;
                text-align: center;
                border-radius: 15px;
                cursor: pointer;
                user-select: none;
                transition: all 0.2s;
            }
            
            .key:active {
                background: rgba(255,255,255,0.3);
                transform: scale(0.95);
            }
            
            .special-keys {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .special-key {
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .quick-links {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                justify-content: center;
                margin-top: 20px;
            }
            
            .quick-link {
                background: rgba(255,255,255,0.1);
                color: white;
                padding: 12px 20px;
                border-radius: 25px;
                text-decoration: none;
                font-size: 14px;
                transition: all 0.3s;
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .quick-link:hover {
                background: rgba(255,255,255,0.2);
                transform: translateY(-2px);
            }
            
            .status {
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background: rgba(0,0,0,0.3);
                border-radius: 10px;
                font-size: 14px;
            }
            
            @media (max-width: 480px) {
                .key {
                    padding: 20px;
                    font-size: 24px;
                }
                .screen {
                    font-size: 16px;
                    padding: 20px;
                }
            }
            
            .menu-option {
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .menu-option:last-child {
                border-bottom: none;
            }
            
            .menu-option:hover {
                background: rgba(255,255,255,0.05);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌾 FarmConnect Zambia</h1>
                <div class="ussd-code">*384*7321#</div>
                <p>USSD Simulator for Farmers</p>
            </div>
            
            <div class="screen" id="ussd-screen">
                Loading USSD service...
            </div>
            
            <div class="input-container">
                <input type="text" id="ussd-input" placeholder="Dial *384*7321#" readonly>
                <button class="btn" onclick="sendUSSD()">SEND</button>
            </div>
            
            <div class="special-keys">
                <div class="special-key" onclick="addKey('*')">*</div>
                <div class="special-key" onclick="addKey('0')">0</div>
                <div class="special-key" onclick="addKey('#')">#</div>
            </div>
            
            <div class="keypad">
                <div class="key" onclick="addKey('1')">1</div>
                <div class="key" onclick="addKey('2')">2</div>
                <div class="key" onclick="addKey('3')">3</div>
                <div class="key" onclick="addKey('4')">4</div>
                <div class="key" onclick="addKey('5')">5</div>
                <div class="key" onclick="addKey('6')">6</div>
                <div class="key" onclick="addKey('7')">7</div>
                <div class="key" onclick="addKey('8')">8</div>
                <div class="key" onclick="addKey('9')">9</div>
                <div class="key" onclick="clearKey()" style="font-size: 20px;">CLEAR</div>
                <div class="key" onclick="backspace()" style="font-size: 20px;">⌫</div>
                <div class="key" onclick="resetUSSD()" style="font-size: 20px;">RESET</div>
            </div>
            
            <div class="quick-links">
                <a href="javascript:void(0)" onclick="quickTest('')" class="quick-link">Start USSD</a>
                <a href="javascript:void(0)" onclick="quickTest('1')" class="quick-link">Market Prices</a>
                <a href="javascript:void(0)" onclick="quickTest('1*1')" class="quick-link">Maize Prices</a>
                <a href="javascript:void(0)" onclick="quickTest('2')" class="quick-link">Price Forecast</a>
                <a href="javascript:void(0)" onclick="quickTest('3')" class="quick-link">Find Buyers</a>
                <a href="javascript:void(0)" onclick="quickTest('4')" class="quick-link">Weather Info</a>
                <a href="javascript:void(0)" onclick="quickTest('5')" class="quick-link">Farming Tips</a>
            </div>
            
            <div class="status">
                📍 Connected to: {{ base_url }}<br>
                📱 Service Code: *384*7321#
            </div>
        </div>
        
        <script>
            let ussdText = '';
            const baseUrl = '{{ base_url }}';
            
            // Format USSD response for display
            function formatResponse(response) {
                if (!response) return 'No response from server';
                
                if (response.startsWith('CON ')) {
                    return '📱 FarmConnect Zambia\\n' + 
                           '────────────────────\\n' + 
                           response.substring(4).replace(/\\n/g, '\\n');
                } else if (response.startsWith('END ')) {
                    return response.substring(4).replace(/\\n/g, '\\n') + 
                           '\\n────────────────────\\n' +
                           '📞 Dial *384*7321# to restart';
                }
                return response;
            }
            
            // Send USSD request
            async function sendUSSD() {
                try {
                    const response = await fetch(`${baseUrl}/ussd/test?text=${encodeURIComponent(ussdText)}`);
                    const data = await response.json();
                    
                    const screen = document.getElementById('ussd-screen');
                    screen.innerHTML = formatResponse(data.response);
                    screen.scrollTop = screen.scrollHeight;
                    
                    // Clear input after sending
                    document.getElementById('ussd-input').value = '';
                    ussdText = '';
                    
                } catch (error) {
                    document.getElementById('ussd-screen').innerHTML = 
                        '❌ Connection error\\n' +
                        'Please check your internet connection';
                }
            }
            
            // Add key to input
            function addKey(key) {
                ussdText += key;
                document.getElementById('ussd-input').value = ussdText;
            }
            
            // Clear input
            function clearKey() {
                ussdText = '';
                document.getElementById('ussd-input').value = '';
            }
            
            // Backspace
            function backspace() {
                ussdText = ussdText.slice(0, -1);
                document.getElementById('ussd-input').value = ussdText;
            }
            
            // Reset to initial USSD
            function resetUSSD() {
                ussdText = '';
                sendUSSD();
            }
            
            // Quick test functions
            function quickTest(text) {
                ussdText = text;
                sendUSSD();
            }
            
            // Keyboard support
            document.addEventListener('keydown', (e) => {
                if (e.key >= '0' && e.key <= '9') {
                    addKey(e.key);
                } else if (e.key === '*') {
                    addKey('*');
                } else if (e.key === '#') {
                    addKey('#');
                } else if (e.key === 'Enter') {
                    sendUSSD();
                } else if (e.key === 'Backspace') {
                    backspace();
                } else if (e.key === 'Escape') {
                    clearKey();
                }
            });
            
            // Initial load - start USSD
            window.onload = resetUSSD;
            
            // Auto-refresh connection status
            setInterval(async () => {
                try {
                    const response = await fetch(`${baseUrl}/api/status`);
                    const data = await response.json();
                    document.querySelector('.status').innerHTML = 
                        `✅ Connected to: ${baseUrl}<br>` +
                        `📱 Service Code: *384*7321#<br>` +
                        `🕐 ${new Date().toLocaleTimeString()}`;
                } catch (error) {
                    document.querySelector('.status').innerHTML = 
                        `❌ Connection lost - trying to reconnect...<br>` +
                        `📱 Service Code: *384*7321#`;
                }
            }, 30000);
        </script>
    </body>
    </html>
    ''', base_url=BASE_URL)

@app.route('/mobile-test')
def mobile_test():
    """Simple mobile test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>FarmConnect Mobile Test</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; padding: 20px; text-align: center; background: #2E8B57; color: white; }
            .btn { display: block; background: white; color: #2E8B57; padding: 15px; margin: 10px; border-radius: 10px; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>📱 FarmConnect Mobile</h1>
        <a href="/mobile-ussd" class="btn">📞 USSD Simulator</a>
        <a href="/" class="btn">🌐 Full Website</a>
        <a href="/ussd/test" class="btn">🧪 USSD API Test</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 60)
    print("📱 MOBILE USSD INTERFACE")
    print("=" * 60)
    print(f"🌐 Your ngrok URL: https://semimystically-unpummelled-lanora.ngrok-free.dev")
    print(f"📱 Mobile interface: http://127.0.0.1:5001/mobile-ussd")
    print(f"📱 On phone: https://semimystically-unpummelled-lanora.ngrok-free.dev/mobile-ussd")
    print("=" * 60)
    app.run(debug=True, port=5001, host='0.0.0.0')