import multiprocessing
import argparse
from main_seat_check import main_check_seat
from main_payment_check import main_check_payment
from module.set import send_telegram_and_log, find_location

def main(headless=True):
    
    processes = []

    # 좌석 체크 프로세스
    p1 = multiprocessing.Process(target=main_check_payment, kwargs={"headless": headless})
    processes.append(p1)

    # 결제 체크 프로세스
    p2 = multiprocessing.Process(target=main_check_seat, kwargs={"headless": headless})
    processes.append(p2)

    # 프로세스 시작
    for p in processes:
        p.start()

    # 프로세스 대기
    for p in processes:
        p.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--open', action='store_true', help='브라우저를 띄운 상태로 실행')
    args = parser.parse_args()

    # open 옵션 없으면 기본 headless
    headless = not args.open

    main(headless=headless)