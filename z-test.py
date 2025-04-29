import os

def update_dashboard(category, msg, append=False):
    os.makedirs("dashboard_log", exist_ok=True)
    file_path = f"dashboard_log/{category}_dashboard.txt"
    mode = "a" if append else "w"
    with open(file_path, mode, encoding="utf-8") as f:
        f.write(msg + "\n\n")


msg1 = "1"
update_dashboard("payment", msg1)

msg2 = "2"
update_dashboard("payment", msg2, append=True)