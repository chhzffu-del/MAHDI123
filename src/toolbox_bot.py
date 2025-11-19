# ==============================================================================
#  MAHDI'S TOOLBOX - v5.2 (Geographic Camouflage Edition)
# ==============================================================================
# ... (كل الكود السابق يبقى كما هو) ...

# --- دوال أداة فحص الحسابات (Hunter) ---
def hunter_worker():
    # ...
    try:
        target_url = 'https://i.instagram.com/api/v1/accounts/login/'
        # إضافة التمويه الجغرافي هنا أيضاً
        payload = {
            'api_key': SCRAPER_API_KEY,
            'url': target_url,
            'country_code': 'us', # <-- الإضافة الجديدة
            'method': 'POST',
            # ...
        }
        response = requests.post('http://api.scraperapi.com', json=payload, timeout=90)
        # ...
    except Exception as e:
        # ...

# --- دوال أداة رشق المتابعين (Rusher) - The Double Agent ---
def rusher_worker(target_username):
    global hits, fails, last_event
    while is_running:
        try:
            agent_session = requests.Session()
            agent_session.headers.update(create_double_agent_fingerprint())

            last_event = f"Scouting {target_username} from US..."
            page_url = "https://superviral.io/free-instagram-followers/"
            
            # *** التعديل الأول هنا: إضافة country_code=us ***
            scraper_url = f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={page_url}&country_code=us'
            response_page = agent_session.get(scraper_url, timeout=90)
            
            # ... (باقي منطق التحليل يبقى كما هو) ...
            
            nonce_ticket = nonce_input.get('value')
            last_event = "Nonce ticket acquired. Attacking from US..."

            api_url = "https://superviral.io/wp-admin/admin-ajax.php"
            
            payload = {
                'action': 'get_free_followers',
                'username': target_username,
                'email': random_email,
                '_wpnonce': nonce_ticket
            }
            
            # *** التعديل الثاني هنا: إضافة country_code=us ***
            # ملاحظة: لإرسال طلب POST مع country_code، يجب أن يكون جزءاً من الرابط
            post_scraper_url = f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={api_url}&country_code=us'
            response_rush = agent_session.post(post_scraper_url, data=payload, timeout=90)

            # ... (باقي منطق التحقق من النجاح يبقى كما هو) ...

        except Exception as e:
            # ...

# ... (باقي الكود يبقى كما هو تماماً) ...
