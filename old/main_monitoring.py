import time
import argparse
from multiprocessing import Process

from main_payment_check import check_payment_main
from main_seat_check import check_seat_main

def run_processes(headless):
    seat_process = Process(target=check_seat_main, kwargs={"headless": headless})
    payment_process = Process(target=check_payment_main, kwargs={"headless": headless})

    seat_process.start()
    payment_process.start()

    seat_process.join()
    payment_process.join()

    print("✅ 좌석 자동화 작업 완료")
    print("✅ 결제 자동화 작업 완료")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true", help="브라우저 오픈 모드 (headless 끔)")
    args = parser.parse_args()

    run_processes(headless=not args.open)