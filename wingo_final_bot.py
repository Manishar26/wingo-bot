import requests
import time

# Telegram Configuration
BOT_TOKEN = "AAERkhSNXSoHvcn5fNu0NYLtka1YmFZ-_eM" 
CHAT_ID = "8818440313"

# WinGo 30S API
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=10&gameId=1"

# ONLY YOUR EXACT 4 PATTERNS (Oldest -> Newest)
PATTERN_TARGETS = {
    # Size Patterns
    "BBBSS": ("B", "BET ON BIG 🟡"),
    "SSSBB": ("S", "BET ON SMALL 🔵"),
    
    # Color Patterns
    "GGGRR": ("G", "BET ON GREEN 🟢"),
    "RRRGG": ("R", "BET ON RED 🔴")
}

# State Variables
state = {
    "last_notified_period": "",
    "pending_period": None,
    "pending_bet": None,
    "pending_type": None,  # "SIZE" or "COLOR"
    "win_count": 0,
    "loss_count": 0,
    "current_level": 1
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_outcome(num):
    num = int(num)
    size = "B" if num >= 5 else "S"
    
    # Standard WinGo Colour Logic
    if num in [1, 3, 7, 9, 5]:
        color = "G"
    elif num in [2, 4, 6, 8, 0]:
        color = "R"
    else:
        color = "MIX"
        
    return size, color

def check_market():
    try:
        res = requests.get(API_URL, timeout=5)
        data = res.json()
        list_data = data.get("data", {}).get("list", [])
        
        if not list_data or len(list_data) < 6:
            return

        latest = list_data[0]
        latest_period = str(latest["issueNumber"])
        latest_num = int(latest["number"])
        actual_size, actual_color = get_outcome(latest_num)

        # 1. Check Result for Pending Prediction
        if state["pending_period"] and latest_period == state["pending_period"]:
            predicted = state["pending_bet"]
            is_win = False

            if state["pending_type"] == "SIZE" and predicted == actual_size:
                is_win = True
            elif state["pending_type"] == "COLOR" and predicted == actual_color:
                is_win = True

            if is_win:
                state["win_count"] += 1
                result_text = "✅ *WIN!*"
                state["current_level"] = 1
            else:
                state["loss_count"] += 1
                result_text = "❌ *LOSS!*"
                state["current_level"] += 1

            res_msg = (
                f"📊 *RESULT FOR PERIOD {latest_period[-5:]}*\n"
                f"Draw Result: `{latest_num}` | Size: `{actual_size}` | Color: `{actual_color}`\n"
                f"Status: {result_text}\n\n"
                f"📈 *TOTAL STATS:*\n"
                f"• Wins: `{state['win_count']}` | Losses: `{state['loss_count']}`\n"
                f"• Next Bet Level: `Level {state['current_level']}`"
            )
            send_telegram(res_msg)
            state["pending_period"] = None
            state["pending_bet"] = None
            state["pending_type"] = None

        # Avoid repeat checks for same period
        if latest_period == state["last_notified_period"]:
            return
            
        state["last_notified_period"] = latest_period

        # 2. Extract Last 5 Rounds (Oldest -> Newest)
        last_5 = list_data[:5][::-1]
        
        size_pattern = "".join([get_outcome(d["number"])[0] for d in last_5])
        color_pattern = "".join([get_outcome(d["number"])[1] for d in last_5])

        target_period = str(int(latest_period) + 1)

        # Match Pattern
        matched_pattern = None
        p_type = None

        if size_pattern in PATTERN_TARGETS:
            matched_pattern = size_pattern
            p_type = "SIZE"
        elif color_pattern in PATTERN_TARGETS:
            matched_pattern = color_pattern
            p_type = "COLOR"

        if matched_pattern:
            next_bet_code, alert_text = PATTERN_TARGETS[matched_pattern]
            
            # Store for pending result check
            state["pending_period"] = target_period
            state["pending_bet"] = next_bet_code
            state["pending_type"] = p_type

            alert_msg = (
                f"🚀 *WINGO PATTERN ALERT*\n\n"
                f"• Pattern Found (Old->New): `{matched_pattern}` ({p_type})\n"
                f"• Target Period: `{target_period[-5:]}`\n"
                f"• Signal: *{alert_text}*\n\n"
                f"🎯 *BET DETAILS:*\n"
                f"• Current Level: `Level {state['current_level']}`\n"
                f"• Total Wins: `{state['win_count']}` | Losses: `{state['loss_count']}`"
            )
            send_telegram(alert_msg)

    except Exception as e:
        print(f"Error: {e}")

print("Exact 4 Pattern Engine Active...")
send_telegram("✅ *WinGo Exact 4-Pattern Bot Active! Tracking BBBSS, SSSBB, GGGRR, RRRGG...*")

while True:
    check_market()
    time.sleep(3)
              
