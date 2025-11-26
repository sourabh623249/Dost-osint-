import sqlite3
import requests
import asyncio
import os
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Bot configuration - Environment variables se
BOT_TOKEN = os.getenv('BOT_TOKEN', "8407523987:AAHF0OhQRX-SeL9T_5OU7XNs9iFvJs3NNEw")
PHONE_API_BASE = "https://splexxo123-7saw.vercel.app/api/seller?mobile="
API_KEY = "&key=SPLEXXO"
AADHAR_API_URL = "https://aadharinfo.gauravcyber0.workers.dev/?aadhar="
GST_API_URL = "https://gstlookup.hideme.eu.org/?gstNumber="
ADMIN_IDS = ["8035914752", "6727548057", "8295606531"]
ADMIN_USERNAME = "@jasveer63"

# Database setup - Render compatible
def get_db_connection():
    conn = sqlite3.connect('yadav.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id TEXT PRIMARY KEY, 
                  username TEXT,
                  total_searches INTEGER DEFAULT 0,
                  joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Groups table
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (group_id TEXT PRIMARY KEY,
                  group_name TEXT,
                  added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Protected numbers table
    c.execute('''CREATE TABLE IF NOT EXISTS protected_numbers
                 (number TEXT PRIMARY KEY,
                  response TEXT,
                  protected_by TEXT,
                  protected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Search history table
    c.execute('''CREATE TABLE IF NOT EXISTS search_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  search_type TEXT,
                  search_query TEXT,
                  search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("🦁 Yadav ji ka system ready hai! 👑")

# User functions
def create_user(user_id, username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username) 
                 VALUES (?, ?)''', (user_id, username))
    conn.commit()
    conn.close()

def add_group(group_id, group_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO groups (group_id, group_name) 
                 VALUES (?, ?)''', (group_id, group_name))
    conn.commit()
    conn.close()
    print(f"✅ Group added: {group_name} ({group_id})")

def get_all_groups():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT group_id FROM groups')
    groups = c.fetchall()
    conn.close()
    return [group[0] for group in groups]

def update_search_count(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET total_searches = total_searches + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_search_history(user_id, search_type, search_query):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO search_history (user_id, search_type, search_query) VALUES (?, ?, ?)', 
              (user_id, search_type, search_query))
    conn.commit()
    conn.close()

# Get all users AND groups for broadcast
def get_all_chats():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all private users
    c.execute('SELECT user_id FROM users WHERE user_id NOT IN ({})'.format(','.join(['?']*len(ADMIN_IDS))), ADMIN_IDS)
    users = c.fetchall()
    
    # Get all groups
    c.execute('SELECT group_id FROM groups')
    groups = c.fetchall()
    
    conn.close()
    
    # Combine user IDs and group IDs
    all_chats = [user[0] for user in users] + [group[0] for group in groups]
    print(f"📊 Total chats for broadcast: {len(all_chats)} (Users: {len(users)}, Groups: {len(groups)})")
    return all_chats

# Protected numbers functions
def add_protected_number(number, response, admin_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO protected_numbers 
                 (number, response, protected_by) VALUES (?, ?, ?)''', 
              (number, response, admin_id))
    conn.commit()
    conn.close()

def get_protected_number(number):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT response FROM protected_numbers WHERE number = ?', (number,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_protected():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT number, response FROM protected_numbers')
    result = c.fetchall()
    conn.close()
    return result

# API calls
def search_number(number):
    try:
        # Check protected numbers first
        protected_response = get_protected_number(number)
        if protected_response:
            return f"protected:{protected_response}"
        
        if number == "7052500819":
            return "special"
        
        # Dynamic API URL for each number
        api_url = f"{PHONE_API_BASE}{number}{API_KEY}"
        print(f"🔍 API Calling: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API Data: {data}")
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"🔥 API Exception: {e}")
        return None

def search_aadhar(aadhar):
    try:
        api_url = f"{AADHAR_API_URL}{aadhar}"
        response = requests.get(api_url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def search_gst(gst_number):
    try:
        api_url = f"{GST_API_URL}{gst_number}"
        response = requests.get(api_url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Format result functions
def format_phone_result(data, number):
    if data == "special":
        return "❌ Beta jis thali me khata ussi mei ched krta 🤡"
    
    if isinstance(data, str) and data.startswith("protected:"):
        return data.replace("protected:", "")
    
    if not data or 'data' not in data:
        return "❌ No data found for this number\n\n💡 Try another number or contact admin"
    
    records = data['data']
    if not records:
        return "❌ No records found for this number\n\n💡 Database mein data nahi hai"
    
    result = f"🔍 🦁Yadav🦁 - Mobile Info: {number}\n"
    result += f"📊 Total Records Found: {len(records)}\n\n"
    
    for i, record in enumerate(records, 1):
        result += f"➖ Source {i} Results:\n"
        result += "────────────────────\n"
        result += f"📋 Record {i}:\n"
        result += f"👤 Name: {record.get('name', 'N/A')}\n"
        result += f"📞 Mobile: {record.get('mobile', 'N/A')}\n" 
        result += f"👨‍👧 Father: {record.get('fname', 'N/A')}\n"
        result += f"🏠 Address: {record.get('address', 'N/A').replace('!', ' ')}\n"
        result += f"📱 Alt Mobile: {record.get('alt', 'N/A')}\n"
        result += f"📡 Circle: {record.get('circle', 'N/A')}\n"
        result += f"🆔 Aadhar: {record.get('id', 'N/A')}\n\n"
    
    result += "────────────────────\n"
    result += f"🔥 Powered by 👑yaduvanshi👑 networks\n"
    result += f"👑 Admin: {ADMIN_USERNAME}\n"
    result += f"🎉 **Unlimited Searches - Free Forever!** 🎉"
    
    return result

def format_aadhar_result(data, aadhar):
    if not data:
        return "❌ No Aadhar data found\n\n💡 Check Aadhar number or try again"
    
    result = f"🆔 🦁Yadav🦁 - Aadhar Info\n"
    result += "────────────────────\n"
    result += f"📄 Aadhar Number: {aadhar}\n"
    
    if 'name' in data:
        result += f"👤 Name: {data.get('name', 'N/A')}\n"
    if 'dob' in data:
        result += f"🎂 Date of Birth: {data.get('dob', 'N/A')}\n"
    if 'gender' in data:
        result += f"⚧ Gender: {data.get('gender', 'N/A')}\n"
    if 'address' in data:
        result += f"🏠 Address: {data.get('address', 'N/A')}\n"
    if 'phone' in data:
        result += f"📞 Phone: {data.get('phone', 'N/A')}\n"
    if 'email' in data:
        result += f"📧 Email: {data.get('email', 'N/A')}\n"
    
    result += "\n────────────────────\n"
    result += f"🔥 Powered by 👑yaduvanshi👑 networks\n"
    result += f"👑 Admin: {ADMIN_USERNAME}\n"
    result += f"🎉 **Unlimited Searches - Free Forever!** 🎉"
    
    return result

def format_gst_result(data, gst_number):
    if not data:
        return "❌ No GST data found\n\n💡 Check GST number or try again"
    
    result = f"🏢 🦁Yadav🦁 - GST Info\n"
    result += "────────────────────\n"
    result += f"📊 GST Number: {gst_number}\n"
    
    if 'businessName' in data:
        result += f"🏢 Business Name: {data.get('businessName', 'N/A')}\n"
    if 'legalName' in data:
        result += f"⚖️ Legal Name: {data.get('legalName', 'N/A')}\n"
    if 'registrationDate' in data:
        result += f"📅 Registration Date: {data.get('registrationDate', 'N/A')}\n"
    if 'status' in data:
        result += f"📈 Status: {data.get('status', 'N/A')}\n"
    if 'businessType' in data:
        result += f"🏭 Business Type: {data.get('businessType', 'N/A')}\n"
    if 'address' in data:
        result += f"🏠 Address: {data.get('address', 'N/A')}\n"
    if 'state' in data:
        result += f"📍 State: {data.get('state', 'N/A')}\n"
    if 'pincode' in data:
        result += f"📮 Pincode: {data.get('pincode', 'N/A')}\n"
    
    result += "\n────────────────────\n"
    result += f"🔥 Powered by 👑yaduvanshi👑 networks\n"
    result += f"👑 Admin: {ADMIN_USERNAME}\n"
    result += f"🎉 **Unlimited Searches - Free Forever!** 🎉"
    
    return result

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        group_id = str(update.message.chat.id)
        group_name = update.message.chat.title or "Unknown Group"
        add_group(group_id, group_name)
        
        await update.message.reply_text(
            f"👑 **yaduvanshi Bot Group Mein Add Ho Gaya!** 👑\n\n"
            f"🦁 Ab aap group mein bhi searches kar sakte hain!\n\n"
            f"⚡ **Available Commands in Group:**\n"
            f"• /num <number> - Search mobile number\n"
            f"• /aadhar <aadhar> - Search Aadhar details\n"
            f"• /gst <gst_number> - Search GST details\n\n"
            f"🔥 **Yadav ji ka system ab groups mein bhi!** 🚀"
        )
    else:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Unknown"
        create_user(user_id, username)
        
        if user_id in ADMIN_IDS:
            await update.message.reply_text(
                f"👑 **yaduvanshi Admin Panel** 👑\n\n"
                f"❤️ **radhe-radhe** ❤️\n"
                f"✨ **Your Power: UNLIMITED**\n\n"
                f"⚡ **Available Commands:**\n"
                f"• /num <number> - Search mobile number\n"
                f"• /aadhar <aadhar> - Search Aadhar details\n"
                f"• /gst <gst_number> - Search GST details\n"
                f"• /protect number response - Protect numbers\n"
                f"• /protected - View protected numbers\n"
                f"• /users - View all users and groups\n"
                f"• /stats - System statistics\n"
                f"• /broadcast - Send message to all users and groups\n\n"
                f"🔥 **Yadav ji ka system full power pe!** 🚀"
            )
        else:
            await update.message.reply_text(
                f"🌌 **Welcome to 👑yaduvanshi👑 OSINT Service** 🌌\n\n"
                f"🎉 **UNLIMITED FREE SEARCHES** 🎉\n\n"
                f"🎯 **Available Commands:**\n"
                f"• /num <number> - Search mobile number\n"
                f"• /aadhar <aadhar> - Search Aadhar details\n"
                f"• /gst <gst_number> - Search GST details\n"
                f"• /history - Search history\n"
                f"• /mystats - Your statistics\n\n"
                f"⚡ **No credits needed - Search as much as you want!**\n"
                f"🦁 **Yadav ji ke system me aapka swagat hai!** 👑"
            )

async def num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        group_id = str(update.message.chat.id)
        group_name = update.message.chat.title or "Unknown Group"
        add_group(group_id, group_name)
        user_id = f"group_{update.message.chat.id}"
        username = update.message.chat.title or "Group"
    else:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Unknown"
        create_user(user_id, username)
    
    print(f"🔍 Mobile search request from: {user_id} (@{username})")
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /num 1234567890")
        return
    
    number = context.args[0]
    if len(number) != 10 or not number.isdigit():
        await update.message.reply_text("❌ Invalid 10-digit number")
        return
    
    if not user_id.startswith('group_'):
        add_search_history(user_id, "mobile", number)
        update_search_count(user_id)
    
    msg = await update.message.reply_text("🔍 Scanning mobile databases...")
    data = search_number(number)
    
    result = format_phone_result(data, number)
    await msg.edit_text(result)

async def aadhar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        group_id = str(update.message.chat.id)
        group_name = update.message.chat.title or "Unknown Group"
        add_group(group_id, group_name)
        user_id = f"group_{update.message.chat.id}"
        username = update.message.chat.title or "Group"
    else:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Unknown"
        create_user(user_id, username)
    
    print(f"🆔 Aadhar search request from: {user_id} (@{username})")
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /aadhar 123456789012")
        return
    
    aadhar_number = context.args[0]
    if len(aadhar_number) != 12 or not aadhar_number.isdigit():
        await update.message.reply_text("❌ Invalid 12-digit Aadhar number")
        return
    
    if not user_id.startswith('group_'):
        add_search_history(user_id, "aadhar", aadhar_number)
        update_search_count(user_id)
    
    msg = await update.message.reply_text("🆔 Fetching Aadhar details...")
    data = search_aadhar(aadhar_number)
    
    result = format_aadhar_result(data, aadhar_number)
    await msg.edit_text(result)

async def gst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        group_id = str(update.message.chat.id)
        group_name = update.message.chat.title or "Unknown Group"
        add_group(group_id, group_name)
        user_id = f"group_{update.message.chat.id}"
        username = update.message.chat.title or "Group"
    else:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Unknown"
        create_user(user_id, username)
    
    print(f"🏢 GST search request from: {user_id} (@{username})")
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /gst 07AABCU9603R1ZM")
        return
    
    gst_number = context.args[0].upper()
    
    if not user_id.startswith('group_'):
        add_search_history(user_id, "gst", gst_number)
        update_search_count(user_id)
    
    msg = await update.message.reply_text("🏢 Looking up GST details...")
    data = search_gst(gst_number)
    
    result = format_gst_result(data, gst_number)
    await msg.edit_text(result)

# Admin commands
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /protect number response_text")
        return
    
    number = context.args[0]
    response_text = ' '.join(context.args[1:])
    
    if len(number) != 10 or not number.isdigit():
        await update.message.reply_text("❌ Invalid 10-digit number")
        return
    
    add_protected_number(number, response_text, user_id)
    await update.message.reply_text(
        f"✅ **Number Protected!**\n\n"
        f"📞 Number: {number}\n"
        f"💬 Response: {response_text}"
    )

async def protected_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    protected_numbers = get_all_protected()
    
    if not protected_numbers:
        await update.message.reply_text("🔒 No protected numbers")
        return
    
    message = "🔒 **Protected Numbers:**\n\n"
    for number, response in protected_numbers:
        message += f"📞 {number}\n💬 {response}\n\n"
    
    await update.message.reply_text(message)

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, total_searches FROM users WHERE user_id NOT IN ({}) ORDER BY total_searches DESC'
              .format(','.join(['?']*len(ADMIN_IDS))), ADMIN_IDS)
    users_data = c.fetchall()
    
    c.execute('SELECT group_name FROM groups')
    groups_data = c.fetchall()
    
    conn.close()
    
    message = "📊 **All Users & Groups:**\n\n"
    
    message += "👥 **Users:**\n"
    if users_data:
        for username, searches in users_data:
            message += f"👤 @{username}\n"
            message += f"   🔍 Searches: {searches}\n\n"
    else:
        message += "   No users yet\n\n"
    
    message += "👥 **Groups:**\n"
    if groups_data:
        for group_name, in groups_data:
            message += f"💬 {group_name}\n"
    else:
        message += "   No groups yet\n"
    
    await update.message.reply_text(message)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users WHERE user_id NOT IN ({})'.format(','.join(['?']*len(ADMIN_IDS))), ADMIN_IDS)
    total_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM groups')
    total_groups = c.fetchone()[0]
    
    c.execute('SELECT SUM(total_searches) FROM users')
    total_searches = c.fetchone()[0] or 0
    
    c.execute('SELECT COUNT(*) FROM protected_numbers')
    protected_count = c.fetchone()[0]
    
    conn.close()
    
    await update.message.reply_text(
        f"📈 **🦁Yadav🦁 Statistics:**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"💬 Total Groups: {total_groups}\n"
        f"🔍 Total Searches: {total_searches}\n"
        f"🔒 Protected Numbers: {protected_count}\n\n"
        f"👑 Admin: {ADMIN_USERNAME}\n"
        f"🔥 **Yadav ji ka system chamak raha hai!** ✨"
    )

async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if update.message.chat.type in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command works only in private chat!")
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT total_searches, joined_date FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text("❌ User not found! Use /start first")
        return
    
    searches, joined_date = result
    
    await update.message.reply_text(
        f"📊 **Your Statistics:**\n\n"
        f"🔍 Total Searches: {searches}\n"
        f"📅 Member Since: {joined_date[:10]}\n\n"
        f"🎉 **Unlimited Free Searches!**\n"
        f"🦁 **Yadav ji ke saath aage badho!** 👑"
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if update.message.chat.type in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command works only in private chat!")
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT search_type, search_query, search_date FROM search_history WHERE user_id = ? ORDER BY search_date DESC LIMIT 10', (user_id,))
    history_data = c.fetchall()
    conn.close()
    
    if not history_data:
        await update.message.reply_text("📝 No search history yet")
        return
    
    message = "📋 **Recent Searches:**\n\n"
    for search_type, query, search_date in history_data:
        message += f"🔍 {search_type.upper()}: {query}\n"
        message += f"   ⏰ {search_date[:16]}\n\n"
    
    await update.message.reply_text(message)

async def register_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        group_id = str(update.message.chat.id)
        group_name = update.message.chat.title or "Unknown Group"
        add_group(group_id, group_name)
        
        await update.message.reply_text(
            f"✅ **Group Successfully Registered!**\n\n"
            f"💬 Group Name: {group_name}\n"
            f"🆔 Group ID: {group_id}\n\n"
            f"📢 Ab yeh group broadcast messages receive karega!\n"
            f"🔥 **Yadav ji ka system group mein activate!** 👑"
        )
    else:
        await update.message.reply_text("❌ Ye command sirf groups mein use karo!")

# BROADCAST FUNCTION
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Message Usage:**\n\n"
            "• /broadcast your message here\n\n"
            "📝 Example:\n"
            "/broadcast Hello users! New features added!\n\n"
            "💡 **Tip:** Groups ko register karne ke liye group mein `/register_group` use karo"
        )
        return
    
    message_text = ' '.join(context.args)
    all_chats = get_all_chats()
    
    if not all_chats:
        await update.message.reply_text("❌ No users or groups found to broadcast!")
        return
    
    total_chats = len(all_chats)
    success_count = 0
    fail_count = 0
    
    progress_msg = await update.message.reply_text(
        f"📢 **Broadcast Started**\n\n"
        f"💬 Total Chats: {total_chats}\n"
        f"✅ Successful: 0\n"
        f"❌ Failed: 0\n"
        f"📊 Progress: 0%"
    )
    
    broadcast_message = (
        f"📢 **👑yaduvanshi👑 Broadcast** 📢\n\n"
        f"{message_text}\n\n"
        f"────────────────────\n"
        f"🔥 Powered by 👑yaduvanshi👑 networks\n"
        f"👑 Admin: {ADMIN_USERNAME}"
    )
    
    for index, chat_id in enumerate(all_chats):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=broadcast_message
            )
            success_count += 1
            print(f"✅ Broadcast sent to: {chat_id}")
        except Exception as e:
            print(f"❌ Failed to send to {chat_id}: {e}")
            fail_count += 1
        
        if (index + 1) % 5 == 0 or (index + 1) == total_chats:
            progress_percent = int(((index + 1) / total_chats) * 100)
            await progress_msg.edit_text(
                f"📢 **Broadcast in Progress**\n\n"
                f"💬 Total Chats: {total_chats}\n"
                f"✅ Successful: {success_count}\n"
                f"❌ Failed: {fail_count}\n"
                f"📊 Progress: {progress_percent}% ({index + 1}/{total_chats})"
            )
        
        await asyncio.sleep(0.2)
    
    users_count = total_chats - len(get_all_groups())
    groups_count = len(get_all_groups())
    
    await progress_msg.edit_text(
        f"🎉 **Broadcast Completed!**\n\n"
        f"📊 **Final Statistics:**\n"
        f"👥 Total Users: {users_count}\n"
        f"💬 Total Groups: {groups_count}\n"
        f"💬 Total Chats: {total_chats}\n"
        f"✅ Successful: {success_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"📊 Success Rate: {int((success_count/total_chats)*100)}%\n\n"
        f"🔥 **Yadav ji ka message sabko pahunch gaya!** 👑"
    )

# Bot run karne wala function with PROPER error handling
def run_bot():
    print("🚀 Starting Yadav ji ka bot on Render...")
    
    # Setup database
    setup_db()
    
    try:
        # Bot application create kare with proper settings
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("num", num))
        application.add_handler(CommandHandler("aadhar", aadhar))
        application.add_handler(CommandHandler("gst", gst))
        application.add_handler(CommandHandler("protect", protect))
        application.add_handler(CommandHandler("protected", protected_list))
        application.add_handler(CommandHandler("users", users))
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CommandHandler("mystats", mystats))
        application.add_handler(CommandHandler("history", history))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(CommandHandler("register_group", register_group))
        
        print("🚀 Yadav ji ka system fire ho gaya! 🔥")
        print("📞 Dynamic Phone API - Har number ke liye alag call")
        print("💬 Groups support COMPLETELY FIXED!")
        print("📢 Broadcast to both users and groups ACTIVATED!")
        print("🎉 Unlimited free searches activated!")
        print("🌐 Render Hosting - 24/7 Online!")
        
        # Bot run karo with PROPER error handling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # IMPORTANT: Yeh conflict resolve karega
            close_loop=False
        )
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        print("🔄 Restarting bot in 30 seconds...")
        time.sleep(30)
        run_bot()  # Auto-restart

if __name__ == '__main__':
    run_bot()