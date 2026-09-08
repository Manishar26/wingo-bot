import requests
import time
import threading
import os
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = "8026538280:AAHOo3pCnTDB_Oy9DuNPYjb09Kqm2UfM7Os"
CHAT_ID = "1181622773"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=10&gameId=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

PATTERN_TARGETS = {
    "BBBSS": ("B", "BET ON BIG 🟡"),
    "SSSBB": ("S", "BET ON SMALL 🔵"),
    "GGGRR": ("G", "BET ON GREEN 🟢"),
    "RRRGG": ("R", "BET ON RED 🔴")
}

state = {
    "last_period": "",
    "wins": 0,
    "losses": 0,
    "level": 1,
    "pending": None,
    "last_check": "Not Started Yet",
    "error_log": "None"
}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print("Telegram Error:", e)

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
        state["last_check"] = f"Period: {period[-5:]} | Time: {time.strftime('%H:%M:%S')}"

        if period == state["last_period"]: return
        state["last_period"] = period

        latest_num = int(latest["number"])
        actual_size, actual_color = get_outcome(latest_num)

        # 1. WIN / LOSS VERIFICATION
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

            send_telegram(
                f"📊 *RESULT FOR {period[-5:]}*\n"
                f"Result: `{latest_num}` | Status: {status}\n"
                f"Wins: `{state['wins']}` | Losses: `{state['losses']}`\n"
                f"Next Level: `Level {state['level']}`"
            )
            state["pending"] = None

        # 2. PATTERN CHECKING
        last_5 = list_data[:5][::-1]
        size_pat = "".join([get_outcome(d["number"])[0] for d in last_5])
        color_pat = "".join([get_outcome(d["number"])[1] for d in last_5])

        matched, p_type = None, ""
        if size_pat in PATTERN_TARGETS:
            matched, p_type = size_pat, "SIZE"
        elif color_pat in PATTERN_TARGETS:
            matched, p_type = color_pat, "COLOR"

        if matched:
            next_code, alert_txt = PATTERN_TARGETS[matched]
            target_period = str(int(period) + 1)

            state["pending"] = {
                "target": target_period,
                "bet": next_code,
                "type": p_type
            }

            send_telegram(
                f"🚀 *WINGO PATTERN ALERT*\n"
                f"Pattern: `{matched}` ({p_type})\n"
                f"Target: `{target_period[-5:]}`\n"
                f"Signal: *{alert_txt}*\n"
                f"Level: `Level {state['level']}`"
            )

    except Exception as e:
        state["error_log"] = str(e)
        print("Market Check Error:", e)

def bot_loop():
    time.sleep(3)
    send_telegram("🚀 *WinGo Bot Started via Render + UptimeRobot!*")
    while True:
        check_market()
        time.sleep(3)

# Background Thread
threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return f"""
    <h2>🚀 WinGo 30S Bot Status</h2>
    <p><b>Last API Check:</b> {state['last_check']}</p>
    <p><b>Wins:</b> {state['wins']} | <b>Losses:</b> {state['losses']} | <b>Current Level:</b> {state['level']}</p>
    <p><b>Error Status:</b> {state['error_log']}</p>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
