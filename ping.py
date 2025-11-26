import requests
import time
import threading
import os

def keep_alive():
    """
    Background thread that pings the app every 10 minutes
    to prevent Render from sleeping
    """
    while True:
        try:
            # Get your Render app URL from environment variable
            app_url = os.getenv('RENDER_APP_URL', 'https://your-app.onrender.com')
            if app_url.startswith('https://'):
                response = requests.get(f"{app_url}/ping")
                print(f"✅ Pinged {app_url} - Status: {response.status_code}")
            else:
                print("⚠️  RENDER_APP_URL not set properly")
        except Exception as e:
            print(f"❌ Ping failed: {e}")
        
        # Wait for 10 minutes (600 seconds)
        time.sleep(600)

def start_ping():
    """Start the ping thread"""
    ping_thread = threading.Thread(target=keep_alive)
    ping_thread.daemon = True
    ping_thread.start()
    print("🔄 Background ping system started!")