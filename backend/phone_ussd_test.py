# phone_ussd_test.py - Run this for phone testing
from flask import Flask, render_template_string, request, jsonify
import random
from datetime import datetime

app = Flask(__name__)

@app.route('/phone-ussd')
def phone_ussd():
    """Mobile-friendly USSD simulator"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📱 FarmConnect USSD Simulator</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                -webkit-tap-highlight-color: transparent;
            }
            
            body {
                font-family: 'Courier New', monospace;
                background: #000;
                color: #fff;
                height: 100vh;
                display: flex;
                flex-direction: column;
                padding: 10px;
            }
            
            .ussd-header {
                background: #006400;
                color: white;
                padding: 15px;
                text-align: center;
                border-radius: 5px 5px 0 0;
                font-weight: bold;
            }
            
            .ussd-screen {
                background: #000;
                color: #0f0;
                padding: 20px;
                flex-grow: 1;
                overflow-y: auto;
                font-size: 16px;
                line-height: 1.5;
                white-space: pre-wrap;
                border: 1px solid #333;
                margin: 10px 0;
                border-radius: 5px;
            }
            
            .ussd-input {
                display: flex;
                margin: 10px 0;
            }
            
            .ussd-input input {
                flex-grow: 1;
                padding: 15px;
                font-size: 18px;
                background: #111;
                color: #0f0;
                border: 1px solid #333;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
            
            .ussd-input button {
                background: #006400;
                color: white;
                border: none;
                padding: 15px 20px;
                margin-left: 10px;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .keypad {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin-top: 10px;
            }
            
            .key {
                background: #222;
                color: white;
                border: 1px solid #444;
                padding: 20px;
                text-align: center;
                font-size: 24px;
                border-radius: 10px;
                cursor: pointer;
                user-select: none;
                -webkit-user-select: none;
            }
            
            .key:active {
                background: #006400;
            }
            
            .special-keys {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            
            .special-key {
                flex: 1;
                background: #333;
                color: white;
                padding: 15px;
                text-align: center;
                border-radius: 5px;
                cursor: pointer;
            }
            
            .phone-frame {
                max-width: 400px;
                margin: 0 auto;
                border: 2px solid #333;
                border-radius: 20px;
                padding: 10px;
                background: #111;
                height: 90vh;
            }
            
            @media (max-width: 400px) {
                .phone-frame {
                    border-radius: 10px;
                    padding: 5px;
                }
                .key {
                    padding: 15px;
                    font-size: 20px;
                }
            }
            
            .menu-option {
                padding: 5px 0;
                border-bottom: 1px solid #222;
            }
            
            .menu-option:last-child {
                border-bottom: none;
            }
        </style>
        <script>
            let ussdText = '';
            let sessionId = 'phone_' + Date.now();
            
            function updateScreen() {
                fetch('/ussd/test?text=' + encodeURIComponent(ussdText))
                    .then(response => response.json())
                    .then(data => {
                        const screen = document.getElementById('ussd-screen');
                        screen.innerHTML = formatResponse(data.response);
                        document.getElementById('ussd-input').value = '';
                        ussdText = '';
                    });
            }
            
            function formatResponse(response) {
                if (response.startsWith('CON ')) {
                    return '📱 FarmConnect Zambia\\n\\n' + response.substring(4).replace(/\\n/g, '\\n').replace(/(\\d\\.)/g, '\\n$1');
                } else if (response.startsWith('END ')) {
                    return response.substring(4).replace(/\\n/g, '\\n') + '\\n\\n📞 Dial *384*7321# to restart';
                }
                return response;
            }
            
            function sendKey(key) {
                const input = document.getElementById('ussd-input');
                if (key === '*') {
                    if (ussdText.length > 0 && !ussdText.endsWith('*')) {
                        ussdText += '*';
                    }
                } else if (key === '#') {
                    updateScreen();
                } else if (key === '←') {
                    ussdText = ussdText.slice(0, -1);
                } else if (key === 'C') {
                    ussdText = '';
                } else {
                    ussdText += key;
                }
                input.value = ussdText;
            }
            
            function sendInput() {
                updateScreen();
            }
            
            function simulatePhoneCall() {
                ussdText = '';
                updateScreen();
            }
            
            // Initial load
            window.onload = simulatePhoneCall;
            
            // Keyboard support
            document.addEventListener('keydown', (e) => {
                if (e.key >= '0' && e.key <= '9') {
                    sendKey(e.key);
                } else if (e.key === '*') {
                    sendKey('*');
                } else if (e.key === '#') {
                    sendKey('#');
                } else if (e.key === 'Enter') {
                    sendInput();
                } else if (e.key === 'Backspace') {
                    sendKey('←');
                }
            });
        </script>
    </head>
    <body>
        <div class="phone-frame">
            <div class="ussd-header">
                📞 *384*7321# - FarmConnect Zambia
            </div>
            
            <div class="ussd-screen" id="ussd-screen">
                Loading USSD...
            </div>
            
            <div class="ussd-input">
                <input type="text" id="ussd-input" placeholder="Enter USSD code..." readonly>
                <button onclick="sendInput()">SEND</button>
            </div>
            
            <div class="special-keys">
                <div class="special-key" onclick="sendKey('*')">*</div>
                <div class="special-key" onclick="sendKey('0')">0</div>
                <div class="special-key" onclick="sendKey('#')">#</div>
            </div>
            
            <div class="keypad">
                <div class="key" onclick="sendKey('1')">1</div>
                <div class="key" onclick="sendKey('2')">2</div>
                <div class="key" onclick="sendKey('3')">3</div>
                <div class="key" onclick="sendKey('4')">4</div>
                <div class="key" onclick="sendKey('5')">5</div>
                <div class="key" onclick="sendKey('6')">6</div>
                <div class="key" onclick="sendKey('7')">7</div>
                <div class="key" onclick="sendKey('8')">8</div>
                <div class="key" onclick="sendKey('9')">9</div>
                <div class="key" onclick="sendKey('←')">←</div>
                <div class="key" onclick="sendKey('0')">0</div>
                <div class="key" onclick="sendKey('C')">C</div>
            </div>
            
            <div style="text-align: center; margin-top: 15px; color: #666; font-size: 12px;">
                Scan QR to test on phone →
                <div id="qrcode"></div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.0/build/qrcode.min.js"></script>
        <script>
            // Generate QR code
            const qr = new QRCode(document.getElementById('qrcode'), {
                text: window.location.href,
                width: 100,
                height: 100,
                colorDark: "#006400",
                colorLight: "#ffffff",
            });
        </script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    print("📱 USSD Phone Simulator starting on http://127.0.0.1:5002/")
    print("📱 Open in phone browser or scan QR code")
    print("📱 Simulated USSD: *384*7321#")
    app.run(debug=True, port=5002, host='0.0.0.0')