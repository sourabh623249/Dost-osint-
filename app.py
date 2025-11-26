from flask import Flask, jsonify
import threading
import time
import os
from ping import start_ping

app = Flask(__name__)

@app.route('/')
def home():
    return "🦁 Yadav ji ka bot is running! 👑"

@app.route('/health')
def health():
    return jsonify({
        "status": "active",
        "message": "Bot is running smoothly",
        "timestamp": time.time()
    })

@app.route('/ping')
def ping():
    return "pong"

# Start ping system when app starts
start_ping()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)