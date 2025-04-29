#!/bin/bash

while true
do
    echo "===== 시작: $(date) ====="

    /usr/local/bin/python3 /Users/mikyungshim/mk_documents/앤딩스터디_상도점/anding-study-bot/main_monitoring.py

    echo "===== 완료: $(date) ====="
    echo "다음 실행까지 5분 대기..."
    sleep 60*5
done