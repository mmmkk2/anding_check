# dashboard.py
from flask import Flask, render_template_string
import os

app = Flask(__name__)

@app.route("/")
def index():
    seat_html = read_file_safe("dashboard_log/seat_dashboard.txt", "(좌석 데이터 없음)")
    payment_html = read_file_safe("dashboard_log/payment_dashboard.txt", "(결제 데이터 없음)")

    html_template = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>앤딩스터디 상도점 모니터링 대시보드</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f9f9f9; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .container {{ display: flex; justify-content: space-between; gap: 20px; }}
            .section {{ background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .seat-section {{ width: 35%; }}
            .payment-section {{ width: 63%; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 13px; }}
            th, td {{ border: 1px solid #ccc; padding: 6px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
            pre {{ font-size: 13px; white-space: pre-wrap; word-break: break-word; }}
        </style>
    </head>
    <body>
        <h1>앤딩스터디 상도점 모니터링 대시보드</h1>
        <div class="container">
            <div class="section seat-section">
                <h2>좌석 현황</h2>
                <pre>{seat_html}</pre>
            </div>
            <div class="section payment-section">
                <h2>결제 현황</h2>
                {payment_html}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

def read_file_safe(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return fallback

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)