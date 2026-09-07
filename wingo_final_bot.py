import requests
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "AAERkhSNXSoHvcn5fNu0NYLtka1YmFZ-_eM" 
CHAT_ID = "8818440313"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=10&gameId=1"

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Active")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

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
        print("Telegram API Response:", res.status_code, res.text)
    except Exception as e:
        print(f"Telegram Exception: {e}")

def get_outcome(num):
    num = int(num)
    size = "B" if num >= 5 else "S"
    color = "G" if num in [1, 3, 7, 9, 5] else ("R" if num in [2, 4, 6, 8, 0] else "MIX")
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

        last_5 = list_data[:5][::-1]
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
        print(f"Error in check_market: {e}")

# Forced Startup Notification
time.sleep(1)
send_telegram("🔔 *WinGo Bot Started & Listening to Market...*")

while True:
    check_market()
    time.sleep(3)
        
