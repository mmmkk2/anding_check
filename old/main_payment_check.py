import csv
import os
from datetime import datetime

PAYMENT_LOG_FILE = "dashboard_log/payment_log.csv"  # 최종경로 반영

def get_today_payment_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    total_amount = 0
    total_count = 0
    payments = []

    if not os.path.exists(PAYMENT_LOG_FILE):
        print("[⚠️ 파일 없음] payment_log.csv")
        return total_count, total_amount, payments

    with open(PAYMENT_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # dict로 읽은 row 확인
            row_datetime = row.get("datetime", "").strip()
            if not row_datetime:
                continue

            if row_datetime.startswith(today):
                try:
                    amount = int(row.get("amount", "0").replace(",", "").replace("원", ""))
                except:
                    amount = 0

                payment_info = {
                    "datetime": row_datetime,
                    "payment_id": row.get("payment_id", ""),
                    "name": row.get("name", ""),
                    "amount": f"{amount:,}원",
                    "product": row.get("product", ""),
                    "date": row.get("date", "")
                }

                payments.append(payment_info)
                total_amount += amount
                total_count += 1

    # ✅ 결제번호 역순 정렬
    payments = sorted(payments, key=lambda x: int(x["payment_id"]), reverse=True)

    return total_count, total_amount, payments