import os
import time
import requests
import socket
import platform
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === 환경변수 로드 ===
try:
    load_dotenv(".env")
except Exception as e:
    print(f"[.env 로드 실패] {e}")

# === 필수 환경변수 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOGIN_ID = os.getenv("LOGIN_ID")
LOGIN_PWD = os.getenv("LOGIN_PWD")
EMERGENCY_CHAT_ID = os.getenv("EMERGENCY_CHAT_ID")


import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_telegram_and_log(msg, broadcast=False):
    print(msg)

    chat_id = os.getenv("CHAT_ID")

    # If broadcast is requested, also send to EMERGENCY_CHAT_ID
    if broadcast:
        chat_id = os.getenv("EMERGENCY_CHAT_ID")
        
    if not chat_id:
        print("[텔레그램 오류] CHAT_ID 설정이 없습니다.")
        return

    try:
        # Always send to the main chat
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": msg}
        )

    except Exception as e:
        print(f"[텔레그램 전송 실패] {e}")
        

# === 로그인 함수 ===
def login(driver):
    BASE_URL = "https://partner.cobopay.co.kr"
    
    if not LOGIN_ID or not LOGIN_PWD:
        send_telegram_and_log("[로그인 실패] ID/PWD 누락")
        return False

    print("로그인 시도 중...")
    driver.get(BASE_URL)
    time.sleep(2)
    try:
        driver.find_element(By.ID, "account_id").send_keys(LOGIN_ID)
        driver.find_element(By.ID, "account_pwd").send_keys(LOGIN_PWD)
        driver.find_element(By.CLASS_NAME, "btn_login").click()
        time.sleep(3)
    except Exception as e:
        send_telegram_and_log(f"[로그인 실패] ID/PWD 입력 오류: {e}")
        return False

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swal2-html-container"))
        )
        alert_text = driver.find_element(By.CLASS_NAME, "swal2-html-container").text
        if "휴대폰 인증번호" in alert_text:
            print("인증번호 입력 대기 중...")
            send_telegram_and_log("인증번호 필요. auth_code.txt 확인해주세요.")
            driver.find_element(By.CLASS_NAME, "swal2-confirm").click()

            for _ in range(60):
                try:
                    with open("auth_code.txt", "r") as f:
                        auth_code = f.read().strip()
                    if auth_code and auth_code.isdigit():
                        driver.find_element(By.ID, "auth_no").send_keys(auth_code)
                        driver.find_element(By.CLASS_NAME, "btn-primary").click()
                        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
                        send_telegram_and_log("인증번호 자동 입력 완료")
                        print("인증번호 자동 입력 성공")
                        return True
                except:
                    pass
                time.sleep(2)
            send_telegram_and_log("⏰ 인증번호 입력 시간 초과. 수동 인증 필요", broadcast=True)
            return False
    except:
        print("인증 없이 로그인 완료")
        return True

    if not driver.find_elements(By.ID, "auth_no"):
        send_telegram_and_log("인증 입력 화면이 닫혔습니다. 수동 확인 필요", broadcast=True)
        return False


# === 드라이버 생성 ===
def create_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    
    driver = webdriver.Chrome(options=options)
    return driver


# === 실행 위치 판별 ===
def find_location():
    try:
        hostname = socket.gethostname()
        if hostname == 'Mikyungs-MacBook-Air.local':
            _location = "(Mac)"
        else:
            _location = "(Server)"
    except Exception:
        _location = "(unknown)"
    
    return _location



def send_broadcast_message(msg):
    """진짜 중요한 알림만 텔레그램으로 보내기"""
    print(f"[Broadcast] {msg}")
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"[텔레그램 전송 실패] {e}")

from datetime import datetime      

def update_dashboard(category, msg, append=False):
    os.makedirs("dashboard_log", exist_ok=True)
    file_path = f"dashboard_log/{category}_dashboard.txt"
    mode = "a" if append else "w"
    with open(file_path, mode, encoding="utf-8") as f:
        f.write(msg + "\n\n")

def send_broadcast_and_update(msg, broadcast=True, category="seat"):
    send_telegram_and_log(msg, broadcast=broadcast)
    update_dashboard(category, msg)


import os
import pickle

FLAGS_FILE = "log/broadcast_flags.pkl"

def load_flags():
    if os.path.exists(FLAGS_FILE):
        with open(FLAGS_FILE, "rb") as f:
            data = pickle.load(f)
    else:
        data = {"date": "", "warn_6": False, "warn_4": False, "recovery": False, "fixed_missing": False}
    return data

def save_flags(flags):
    os.makedirs("log", exist_ok=True)
    with open(FLAGS_FILE, "wb") as f:
        pickle.dump(flags, f)




# def broadcast_message(msg, category="payment"):
#     send_telegram_and_log(msg)
#     update_dashboard(category, msg)