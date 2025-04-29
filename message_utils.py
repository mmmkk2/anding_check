import os
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

CATEGORY_FILES = {
    "payment": os.path.join(LOG_DIR, "dashboard_payment.log"),
    "seat": os.path.join(LOG_DIR, "dashboard_seat.log"),
    "time": os.path.join(LOG_DIR, "dashboard_time.log"),
}

def send_broadcast_message(msg, category="payment"):
    print(f"[Broadcast] {msg}")
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"[텔레그램 실패] {e}")

def update_dashboard(category, msg):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = CATEGORY_FILES.get(category)
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{now_str}] {msg}\n")
    else:
        print(f"[경고] 알 수 없는 카테고리: {category}")