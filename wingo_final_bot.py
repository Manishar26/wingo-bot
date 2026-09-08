import requests
import time
import threading
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = "8026538280:AAHOo3pCnTDB_Oy9DuNPYjb09Kqm2UfM7Os"
CHAT_ID = "1181622773"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=10&gameId=1"

# API Blocking-ஐத் தவிர்க்க Browser Header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

PATTERNS = {
    "BBBSS": {"bet": "B", "text": "BET ON BIG 🟡"},
    "SSSBB": {"bet": "S", "text": "BET ON SMALL 🔵"},
    "GGGRR": {"bet": "G", "text": "BET ON GREEN 🟢"},
    "RRRGG": {"bet": "R", "text": "BET ON RED 🔴"}
}

# Win/Loss Global State
state = {
    "last_period": "",
    "wins": 0,
    "losses": 0,
    "level": 1,
    "pending": None
}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

def get_outcome(num):
    num = int(num)
    size = "B" if num >= 5 else "S"
    color = "G" if num in [1, 3, 5, 7, 9] else "R"
    return size, color

def check_market():
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=5)
        data = res.json()
        list_data = data.get("data", {}).get("list", [])
        if not list_data or len(list_data) < 6: return

        latest = list_data[0]
        period = str(latest["issueNumber"])

        if period == state["last_period"]: return
        state["last_period"] = period

        latest_num = int(latest["number"])
        actual_size, actual_color = get_outcome(latest_num)

        # 1. RESULT VERIFICATION (Win/Loss)
        if state["pending"] and period == state["pending"]["target"]:
            pred = state["pending"]
            is_win = (pred["type"] == "SIZE" and pred["bet"] == actual_size) or \
                     (pred["type"] == "COLOR" and pred["bet"] == actual_color)

            if is_win:
                state["wins"] += 1
                state["level"] = 1
                status = "✅ *WIN!*"
            else:
                state["losses"] += 1
                state["level"] += 1
                status = "❌ *LOSS!*"

            result_msg = (
                f"📊 *RESULT FOR {period[-5:]}*\n"
                f"Result: `{latest_num}` | Status: {status}\n"
                f"Wins: `{state['wins']}` | Losses: `{state['losses']}`\n"
                f"Next Level: `Level {state['level']}`"
            )
            send_telegram(result_msg)
            state["pending"] = None

        # 2. PATTERN CHECKING
        last_5 = list_data[:5][::-1]
        size_pat = "".join([get_outcome(d["number"])[0] for d in last_5])
        color_pat = "".join([get_outcome(d["number"])[1] for d in last_5])

        matched, p_type = None, ""
        if size_pat in PATTERNS:
            matched, p_type = size_pat, "SIZE"
        elif color_pat in PATTERNS:
            matched, p_type = color_pat, "COLOR"

        if matched:
            pat_info = PATTERNS[matched]
            target_period = str(int(period) + 1)

            state["pending"] = {
                "target": target_period,
                "bet": pat_info["bet"],
                "type": p_type
            }

            alert_msg = (
                f"🚀 *WINGO PATTERN ALERT*\n"
                f"Pattern: `{matched}` ({p_type})\n"
                f"Target: `{target_period[-5:]}`\n"
                f"Signal: *{pat_info['text']}*\n"
                f"Level: `Level {state['level']}`"
            )
            send_telegram(alert_msg)

    except Exception as e:
        print("API Fetch Error:", e)

def bot_loop():
    time.sleep(2)
    send_telegram("🚀 *WinGo Python Bot Active with Win/Loss Tracker!*")
    while True:
        check_market()
        time.sleep(3)

# Background Loop Start
threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return f"WinGo Bot Live! Wins: {state['wins']} | Losses: {state['losses']} | Current Level: {state['level']}"
    
