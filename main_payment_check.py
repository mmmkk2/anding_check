import os
import time
import pickle
import csv
import sys
from datetime import datetime
from module.set import create_driver, login, send_telegram_and_log, update_dashboard, find_location#, broadcast_message

PAYMENT_LOG_FILE = "dashboard_log/payment_log.csv"
COOKIE_FILE = "log/last_payment_id.pkl"
BASE_URL = "https://partner.cobopay.co.kr"
PAYMENT_URL = f"{BASE_URL}/pay/payHist"

import csv
from datetime import datetime
import os

def get_today_payment_summary():
    today = datetime.now().strftime("%Y.%m.%d")  # (수정!) 마침표 포맷
    # today = "2025.04.18"
    total_amount = 0
    total_count = 0
    payments = []

    if not os.path.exists(PAYMENT_LOG_FILE):
        return total_count, total_amount, payments

    with open(PAYMENT_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            
            date_field = row.get("date", "").strip()
            
            if not date_field.startswith(today):
                continue  # 오늘 결제가 아니면 건너뜀

            try:
                payment_id = row.get("payment_id", "").strip()
                name = row.get("name", "").strip()
                amount = int(row.get("amount", "0").replace(",", "").replace("원", ""))
                product = row.get("product", "").strip()
                date = row.get("date", "").strip()

                payments.append({
                    "datetime": row.get("datetime", "").strip(),
                    "payment_id": payment_id,
                    "name": name,
                    "amount": f"{amount:,}원",
                    "product": product,
                    "date": date,
                })

                total_amount += amount
                total_count += 1

            except Exception as e:
                print(f"[무시된 결제 데이터] {row} - {e}")
                continue

    return total_count, total_amount, payments
# -----

# 해당 함수를 main_payment_check.py에 import하고
# 현재 payment dashboard update 복구 때 적용해야 한다.

# (추가) 필요 시 generate_html_table(payments) 같은 함수도 같이 사용할 것.


def generate_html_table(payments):
    if not payments:
        return "<p>(결제 데이터 없음)</p>"

    payments_sorted = sorted(payments, key=lambda x: int(x['payment_id']), reverse=True)

    html = "<table border='1' cellspacing='0' cellpadding='5'><tr><th>날짜시간</th><th>결제번호</th><th>이름</th><th>금액</th><th>상품</th><th>결제일</th></tr>"
    for p in payments_sorted:
        html += f"<tr><td>{p['datetime']}</td><td>{p['payment_id']}</td><td>{p['name']}</td><td>{p['amount']}</td><td>{p['product']}</td><td>{p['date']}</td></tr>"
    html += "</table>"
    return html

def main_check_payment(headless=False):
    loop_min = 5
    total_loops = 1440 // loop_min
    now = datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute
    current_loop = (minutes_since_midnight // loop_min) + 1

    location_tag = find_location()

    send_telegram_and_log(f"{location_tag} 📢 [결제 - 모니터링] 시작합니다.")
    
    driver = create_driver(headless=headless)

    
    now_full_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    loop_msg = (
        f"\n\n🪑 결제 모니터링 정상 동작 중\n"
        f"Loop {current_loop}/{total_loops}\n"
        f"⏰ 날짜 + 실행 시각: {now_full_str}"
    )
    send_telegram_and_log(f"{loop_msg} \n\n")
    update_dashboard("payment", loop_msg)

    # send_broadcast_and_update(loop_msg + "\n\n", broadcast=False, category="payment")

    try:
        if not login(driver):
            send_telegram_and_log("[결제] 로그인 실패")
            return

        driver.get(PAYMENT_URL)
        time.sleep(2)

        rows = driver.find_elements("css selector", "table tbody tr")
        if not rows:
            update_dashboard("payment", "(결제 데이터 없음)")
            return

        payments_today = []
        new_payment_detected = False
        today_str = datetime.now().strftime("%Y.%m.%d")

        for row in rows:
            cols = row.find_elements("tag name", "td")
            if len(cols) < 8:
                continue
            payment_id = cols[0].text.strip()
            name = cols[1].text.strip()
            amount = cols[6].text.strip().replace(",", "").replace("원", "")
            date = cols[7].text.strip()
            product = cols[4].text.strip()

            if today_str in date:
                payments_today.append({
                    'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'payment_id': payment_id,
                    'name': name,
                    'amount': amount,
                    'product': product,
                    'date': date
                })
                new_payment_detected = True
                payment_message = f"[결제 발생] 결제번호: {payment_id} / 이름: {name} / 금액: {amount}원 / 상품: {product} / 시간: {date}"
                send_telegram_and_log(payment_message, broadcast=True)

        if payments_today:
            os.makedirs("dashboard_log", exist_ok=True)
            with open(PAYMENT_LOG_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=payments_today[0].keys())
                writer.writeheader()
                writer.writerows(payments_today)

        # 결제 전체 가져오기
        total_count, total_amount, payments = get_today_payment_summary()

        # HTML 테이블 생성
        now_full_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # dashboard에 보낼 최종 html
        summary_msg = f"""
        <h3>💳 오늘 결제 현황 (총 {total_count}건, {total_amount:,}원)</h3>
        <p>🟢 현재 정상 동작 중</p>
        <p>⏰ 실행 시각: {now_full_str}</p>
        <br/>
        """

        table_html = generate_html_table(payments)
        final_html = summary_msg + table_html

        update_dashboard("payment", final_html)

        # ✅ 무조건 broadcast (push 옵션 제거했기 때문에)
        if new_payment_detected:
            plain_summary = f"[오늘 결제] 총 {total_count}건, {total_amount:,}원"
            send_telegram_and_log(plain_summary, broadcast=True)

        send_telegram_and_log(f"{location_tag} ✅ [결제 - 모니터링] 정상 종료되었습니다.")

    except Exception as e:
        send_telegram_and_log(f"[payment_check 오류] {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main_check_payment(headless=True)