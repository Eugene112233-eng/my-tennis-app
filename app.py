import requests
import time

# ========================================================
# ⚙️ НАСТРОЙКИ: ПОДСТАВЬ СВОИ ДАННЫЕ МЕЖДУ КАВЫЧКАМИ
# ========================================================
TELEGRAM_TOKEN = "8982756029:AAH5hKWM0K-n1JPCyMvC3DEMieU_qWK0jI4"
CHAT_ID = "6065347238"
# ========================================================

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
SENT_SIGNALS = set()

def send_telegram_message(text):
    """Отправка сообщения тебе в Telegram"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def get_live_matches():
    """Получаем текущие live-матчи"""
    url = "https://sofascore.com"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        return response.json().get("events", [])
    except: return []

def get_prematch_odds(event_id):
    """Проверяем котировки букмекеров до начала матча"""
    url_odds = f"https://sofascore.com{event_id}/odds/1/all"
    try:
        res = requests.get(url_odds, headers=HEADERS, timeout=3).json()
        choices = res.get("odds", {}).get("choices", [])
        odds_home, odds_away = None, None
        for choice in choices:
            if choice.get("name") == "1": odds_home = float(choice.get("value"))
            elif choice.get("name") == "2": odds_away = float(choice.get("value"))
        return odds_home, odds_away
    except: return None, None

def check_medical_timeout(event_id, target_player_side):
    """Проверяем, брал ли игрок медицинский тайм-аут в первом сете"""
    url_incidents = f"https://sofascore.com{event_id}/incidents"
    try:
        res = requests.get(url_incidents, headers=HEADERS, timeout=3).json()
        incidents = res.get("incidents", [])
        for i in incidents:
            incident_type = i.get("incidentType", "").lower()
            incident_class = i.get("incidentClass", "").lower()
            if "medical" in incident_type or "medical" in incident_class or "injury" in incident_type:
                is_home = i.get("isHome", False)
                if target_player_side == "home" and is_home: return True
                if target_player_side == "away" and not is_home: return True
        return False
    except: return False

print("🚀 Фоновый сканер успешно запущен...")
send_telegram_message("🤖 Бот-сканер успешно запущен и начал работу!")

while True:
    try:
        live_matches = get_live_matches()
        for m in live_matches:
            event_id = m.get("id")
            if event_id in SENT_SIGNALS: continue
            if m.get("status", {}).get("type") != "inprogress": continue
                
            home_score = m.get("homeScore", {})
            away_score = m.get("awayScore", {})
            p1_set1, p2_set1 = home_score.get("period1"), away_score.get("period1")
            p1_set2, p2_set2 = home_score.get("period2", 0), away_score.get("period2", 0)
            
            # Условие: первый сет завершен, во втором 0:0 по геймам
            if p1_set1 is not None and p2_set1 is not None and p1_set2 == 0 and p2_set2 == 0:
                home_won_set1 = p1_set1 > p2_set1
                odds_home, odds_away = get_prematch_odds(event_id)
                
                if odds_home and odds_away:
                    is_signal = False
                    fav_name, fav_odds, fav_side = "", 0.0, ""
                    score_str = f"{p1_set1}:{p2_set1}"
                    
                    if odds_home <= 1.30 and not home_won_set1:
                        is_signal, fav_name, fav_odds, fav_side = True, m.get("homeTeam", {}).get("name", "Игрок 1"), odds_home, "home"
                    elif odds_away <= 1.30 and home_won_set1:
                        is_signal, fav_name, fav_odds, fav_side = True, m.get("awayTeam", {}).get("name", "Игрок 2"), odds_away, "away"
                    
                    if is_signal:
                        has_medical = check_medical_timeout(event_id, fav_side)
                        p1_full = m.get("homeTeam", {}).get("name")
                        p2_full = m.get("awayTeam", {}).get("name")
                        tournament = m.get("tournament", {}).get("name", "Турнир")
                        
                        if has_medical:
                            text_msg = f"⚠️ *ВНИМАНИЕ: ФАВОРИТ С ТАЙМ-АУТОМ*\n🏆 {tournament}\n🎾 {p1_full} — {p2_full}\n📊 1-й сет: {score_str}\n👤 Фаворит: {fav_name} (кф {fav_odds:.2f})\n🚨 *Врач на корте! Опасно ставить на камбэк!*"
                        else:
                            text_msg = f"🚨 *НАЙДЕН СИГНАЛ (Камбэк Фаворита)* 🚨\n\n🏆 {tournament}\n🎾 {p1_full} — {p2_full}\n📊 1-й сет: {score_str}\n👤 Проигравший фаворит: {fav_name} (кф {fav_odds:.2f})\n\n⚡ *1-й сет сыгран БЕЗ медицинских перерывов. Пора заходить!*"
                        
                        send_telegram_message(text_msg)
                        SENT_SIGNALS.add(event_id)
    except: pass
    
    # ⏱️ Спим ровно 15 секунд перед повторной проверкой live-матчей
    time.sleep(15)
