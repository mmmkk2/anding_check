import os
import time
import pickle
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# === 설정 ===
import os
# load_dotenv(".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOGIN_ID = os.getenv("LOGIN_ID")
LOGIN_PWD = os.getenv("LOGIN_PWD")

COOKIE_FILE = os.getenv("COOKIE_FILE", "last_payment_id.pkl")
SEAT_CACHE_FILE = os.getenv("SEAT_CACHE_FILE", "last_seat_state.pkl")
FIX_SEATS = int(os.getenv("FIX_SEATS", 5))
LAPTOP_SEATS = int(os.getenv("LAPTOP_SEATS", 6))
THRESHOLD = int(os.getenv("THRESHOLD", 8))

BASE_URL = "https://partner.cobopay.co.kr"
PAYMENT_URL = f"{BASE_URL}/pay/payHist"
SEAT_URL = f"{BASE_URL}/use/seatUse"

TOTAL_FREE_SEATS = 39 - FIX_SEATS - LAPTOP_SEATS

# === 옵션 ===
import sys
HEADLESS = "--no-headless" not in sys.argv
PUSH_MODE = "--push" in sys.argv


# === 텔레그램 및 로그 출력 ===
def send_telegram_and_log(msg):
    print(msg)
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"[텔레그램 전송 실패] {e}")

# === 로그인 함수 ===
def login(driver):
    print("로그인 시도 중...")
    driver.get(BASE_URL)
    time.sleep(2)
    try:
        driver.find_element(By.ID, "account_id").send_keys(LOGIN_ID)
        driver.find_element(By.ID, "account_pwd").send_keys(LOGIN_PWD)
        driver.find_element(By.CLASS_NAME, "btn_login").click()
        time.sleep(3)
    except Exception as e:
        send_telegram_and_log(f"[로그인 실패] ID/PWD 입력 중 오류 발생: {e}")
        return False

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swal2-html-container"))
        )
        alert_text = driver.find_element(By.CLASS_NAME, "swal2-html-container").text
        if "휴대폰 인증번호" in alert_text:
            print("인증번호 입력 대기 중...")
            send_telegram_and_log("인증번호 입력이 필요합니다. 카카오톡 확인 후 auth_code.txt에 입력해주세요.")
            driver.find_element(By.CLASS_NAME, "swal2-confirm").click()
            for _ in range(60):
                try:
                    with open("auth_code.txt", "r") as f:
                        auth_code = f.read().strip()
                    if auth_code and auth_code.isdigit():
                        driver.find_element(By.ID, "auth_no").send_keys(auth_code)
                        driver.find_element(By.CLASS_NAME, "btn-primary").click()
                        driver.find_element(By.CSS_SELECTOR, 'button.btn.btn-primary[type="submit"]').click()
                        driver.find_element(By.ID, "auth_no").send_keys(auth_code)
                        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
                        send_telegram_and_log("인증번호 자동 입력 완료")
                        print("인증번호 자동 입력 성공")
                        return True
                except:
                    pass
                time.sleep(2)
            send_telegram_and_log("인증번호 입력 시간 초과. 수동 인증이 필요합니다.")
            return False
    except:
        print("인증 없이 로그인 완료")
        return True

    if not driver.find_elements(By.ID, "auth_no"):
        send_telegram_and_log("인증번호 입력 화면이 닫히거나 종료되었습니다. 수동 확인 바랍니다.")
        return False
    

# === 드라이버 설정 ===
def create_driver():
    options = Options()
    options.add_argument("--headless=new") if HEADLESS else None
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    return webdriver.Chrome(options=options)

# === 좌석 상태 체크 ===
def check_seat_status(driver):
    driver.get(SEAT_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))

    used_free_seats = 0
    used_labtop_seats = 0
    used_free_seat_numbers = []

    while True:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 3:
                continue

            seat_type = cols[1].text.strip()
            seat_number_text = cols[2].text.strip().replace("번", "")
            try:
                seat_number = int(seat_number_text)
            except:
                continue

            if seat_type == "개인석" and seat_number <= 33 and seat_number not in range(19, 24):
                used_free_seats += 1
                used_free_seat_numbers.append(seat_number)
            elif seat_type == "개인석" and seat_number > 33:
                used_labtop_seats += 1

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'ul.pagination li.active + li a')
            if "javascript:;" in next_btn.get_attribute("href"):
                break
            next_btn.click()
            time.sleep(1)
        except:
            break

    if os.path.exists(SEAT_CACHE_FILE):
        with open(SEAT_CACHE_FILE, "rb") as f:
            last_state = pickle.load(f)
    else:
        last_state = {"used_free_seats": 0, "used_labtop_seats": 0}

    changed = (
        used_free_seats != last_state["used_free_seats"] or
        used_labtop_seats != last_state["used_labtop_seats"]
    )

    remaining_seats = TOTAL_FREE_SEATS - used_free_seats
    all_free_seat_numbers = [n for n in range(1, 34) if n not in range(19, 24)]
    available_free_seat_numbers = sorted(set(all_free_seat_numbers) - set(used_free_seat_numbers))

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = (
        f"[좌석 알림] ({now})\n"
        f"자유석 현재 입실: {used_free_seats}/{TOTAL_FREE_SEATS}\n"
        f"노트북석 현재 입실: {used_labtop_seats}/{LAPTOP_SEATS}\n"
        f"남은 자유석: {remaining_seats}석" 
    )
    # ✅ 1. 로그 파일에 무조건 기록
    with open("seat_status.log", "a", encoding="utf-8") as log_file:
        log_file.write(msg + "\n\n")

    if changed or PUSH_MODE:        
        if (remaining_seats <= THRESHOLD) & (remaining_seats > 0):
            msg += f" - ({', '.join(map(str, available_free_seat_numbers))})"

        send_telegram_and_log(msg)

        with open(SEAT_CACHE_FILE, "wb") as f:
            pickle.dump({
                "used_free_seats": used_free_seats,
                "used_labtop_seats": used_labtop_seats
            }, f)


def check_new_payment(driver):
    driver.get(PAYMENT_URL)
    time.sleep(2)

    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "rb") as f:
            last_seen_no = pickle.load(f)
    else:
        last_seen_no = None

    all_rows = []

    # 페이지 순회
    while True:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if not rows:
            break
        all_rows.extend(rows)

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'ul.pagination li.active + li a')
            if "javascript:;" in next_btn.get_attribute("href"):
                break
            next_btn.click()
            time.sleep(1.5)
        except:
            break

    all_rows.reverse()  # 과거부터 순서대로 전송

    push_started = last_seen_no is None
    new_last_payment_id = last_seen_no

    for row in all_rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 10:
            continue

        payment_id = cols[0].text.strip()
        name = cols[1].text.strip()
        amount = cols[6].text.strip()
        date = cols[7].text.strip()
        product = cols[9].text.strip()

        if payment_id == last_seen_no:
            push_started = True
            continue
        if not push_started:
            continue

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        msg = (
            f"[결제 발생] ({now_str})\n"
            f"결제번호: {payment_id}\n"
            f"결제일시: {date}\n"
            f"이름: {name}\n"
            f"금액: {amount}\n"
            f"결제상품: {product}"
        )
        send_telegram_and_log(msg)
        new_last_payment_id = payment_id

    # 마지막 결제번호 갱신
    if new_last_payment_id != last_seen_no:
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(new_last_payment_id, f)



from datetime import datetime, timedelta

def check_time_ticket_expiring(driver, remain_hour=5):
    TIME_URL = "https://partner.cobopay.co.kr/user/timePurchase"
    driver.get(TIME_URL)
    time.sleep(2)
    
    try:
        # 남은시간 정렬 클릭
        sort_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//th[contains(text(),'남은시간')]"))
        )
        sort_btn.click()
        time.sleep(2)
    except Exception as e:
        send_telegram_and_log(f"[시간권 정렬 실패] {e}")
        return

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    now = datetime.now()
    alerts = []

    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 10:
                continue

            name = cols[1].text.strip()
            product = cols[4].text.strip()
            end_str = cols[9].text.strip()
            end_time = datetime.strptime(end_str, "%Y.%m.%d %H:%M")

            remain = end_time - now
            if remain <= timedelta(hours=remain_hour):
                h = remain.seconds // 3600
                m = (remain.seconds % 3600) // 60
                alerts.append(f"{name} {product} - {h}시간 {m}분 남음")
        except:
            continue

    if alerts:
        send_telegram_and_log("[⏰ 시간권 종료 임박]\n" + "\n".join(alerts))

        
# === 메인 실행 ===
def main():
    print("자동화 시작")
    driver = create_driver()
    try:
        success = login(driver)
        if not success:
            print("로그인 실패로 종료")
            return
        check_seat_status(driver)
        check_new_payment(driver)
        # check_time_ticket_expiring(driver)
    except Exception as e:
        send_telegram_and_log(f"[오류 발생] {e}")
    finally:
        driver.quit()
        print("드라이버 종료 완료")

if __name__ == "__main__":
    main()
