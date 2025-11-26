from app import app
from bot import run_bot
import threading

# Bot ko alag thread mein run kare
def start_bot():
    run_bot()

# Flask app start hone par bot bhi start ho
if __name__ == "__main__":
    # Bot thread start kare
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask app run kare
    app.run()