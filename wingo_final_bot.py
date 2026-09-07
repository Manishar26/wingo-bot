import requests
import time
import threading
from flask import Flask

# Render App தூங்காமல் இருக்க ஒரு dummy Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return "WinGo Bot is Running!"

BOT_TOKEN = "8026538280:AAHOo3pCnTDB_Oy9DuNPYjb09Kqm2UfM7Os" 
CHAT_ID = "1181622773"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=10&gameId=1"

PATTERN_TARGETS = {
    "BBBSS": ("B", "BET ON BIG 🟡"),
    "SSSBB": ("S", "BET ON SMALL 🔵"),
    "GGGRR": ("G", "BET ON GREEN 🟢"),
    "RRRGG": ("R", "BET ON RED 🔴")
}

state = {"last_period": "", "win_count": 0, "loss_count": 0, "current_level": 1, "pending": None}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        print("Telegram Status:", res.status_code)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_outcome(num):
    num = int(num)
    size = "B" if num >= 5 else "S"
    color = "G" if num in [1, 3, 5, 7, 9] else "R"
    return size, color

def check_market():
    try:
        res = requests.get(API_URL, timeout=5)
        data = res.json()
        list_data = data.get("data", {}).get("list", [])
        if not list_data or len(list_data) < 6: return

        latest = list_data[0]
        latest_period = str(latest["issueNumber"])
        latest_num = int(latest["number"])
        actual_size, actual_color = get_outcome(latest_num)

        if state["pending"] and latest_period == state["pending"]["target"]:
            pred = state["pending"]
            win = (pred["type"] == "SIZE" and pred["bet"] == actual_size) or (pred["type"] == "COLOR" and pred["bet"] == actual_color)
            if win:
                state["win_count"] += 1
                state["current_level"] = 1
                status = "✅ *WIN!*"
            else:
                state["loss_count"] += 1
                state["current_level"] += 1
                status = "❌ *LOSS!*"

            send_telegram(f"📊 *RESULT FOR {latest_period[-5:]}*\nResult: `{latest_num}` | Status: {status}\nWins: `{state['win_count']}` | Losses: `{state['loss_count']}`\nNext Level: `Level {state['current_level']}`")
            state["pending"] = None

        if latest_period == state["last_period"]: return
        state["last_period"] = latest_period

        last_5 = list_data[1:6][::-1]
        size_pat = "".join([get_outcome(d["number"])[0] for d in last_5])
        color_pat = "".join([get_outcome(d["number"])[1] for d in last_5])
        
        target_period = str(int(latest_period) + 1)

        matched, p_type = None, None
        if size_pat in PATTERN_TARGETS: matched, p_type = size_pat, "SIZE"
        elif color_pat in PATTERN_TARGETS: matched, p_type = color_pat, "COLOR"

        if matched:
            next_code, alert_txt = PATTERN_TARGETS[matched]
            state["pending"] = {"target": target_period, "bet": next_code, "type": p_type}
            send_telegram(f"🚀 *WINGO PATTERN ALERT*\nPattern: `{matched}` ({p_type})\nTarget: `{target_period[-5:]}`\nSignal: *{alert_txt}*\nLevel: `Level {state['current_level']}`")

    except Exception as e:
        print(f"Error: {e}")

def bot_loop():
    send_telegram("🚀 *WinGo Bot Active 24/7 Free Cloud!*")
    while True:
        check_market()
        time.sleep(3)

if __name__ == "__main__":
    # Bot Loop-ஐ பின்னணியில் தனியாக ஓட வைக்கிறது
    t = threading.Thread(target=bot_loop)
    t.daemon = True
    t.start()
    
    # Render-ன் இலவச Web Service-க்கான Port
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
