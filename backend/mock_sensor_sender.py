import random
import time
import requests
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

BASE_URL = "https://capstone-project-54l6.onrender.com"
SENSOR_ENDPOINT = f"{BASE_URL}/sensor-logs"
SUMMARY_ENDPOINT = f"{BASE_URL}/daily-summaries"

NODE_IDS = [7, 11, 12, 13, 14, 15, 16]

START_DATE = datetime(2026, 5, 1, 0, 0, tzinfo=KST)
END_DATE = datetime(2026, 6, 1, 0, 0, tzinfo=KST)

INTERVAL_HOURS = 6
REQUEST_DELAY_SECONDS = 1.0


def generate_inner_water_level(measured_at: datetime) -> float:
    day = measured_at.day

    if 1 <= day <= 5:
        return round(random.uniform(1.0, 4.5), 2)       # FLOODED
    elif 6 <= day <= 10:
        return round(random.uniform(-10.0, -1.0), 2)    # DRYING
    elif 11 <= day <= 13:
        return round(random.uniform(-18.0, -15.5), 2)   # DRY
    elif 14 <= day <= 18:
        return round(random.uniform(0.5, 4.5), 2)       # FLOODED
    elif 19 <= day <= 21:
        return round(random.uniform(5.2, 7.5), 2)       # OVERFLOODED
    elif 22 <= day <= 26:
        return round(random.uniform(-10.0, -1.0), 2)    # DRYING
    else:
        return round(random.uniform(-18.0, -15.5), 2)   # DRY


def send_sensor_log(node_id: int, measured_at: datetime):
    inner = generate_inner_water_level(measured_at)

    payload = {
        "node_id": node_id,
        "inner_water_level": inner,
        "outer_water_level": round(inner + random.uniform(-0.8, 0.8), 2),
        "battery_voltage": round(random.uniform(3.55, 3.75), 2),
        "measured_at": measured_at.isoformat()
    }

    res = requests.post(SENSOR_ENDPOINT, json=payload, timeout=30)

    if res.status_code not in (200, 201):
        print("센서 로그 실패")
        print(payload)
        print(res.status_code, res.text)
        raise SystemExit

    return True


def create_daily_summary(node_id: int, record_date):
    payload = {
        "node_id": node_id,
        "record_date": record_date.isoformat(),
        "verification_image_url": None
    }

    res = requests.post(SUMMARY_ENDPOINT, json=payload, timeout=30)

    # 이미 생성된 경우 400이 나올 수 있으니 중단하지 않음
    if res.status_code in (200, 201):
        return True

    if res.status_code == 400 and "이미 존재" in res.text:
        print(f"이미 존재: node {node_id}, {record_date}")
        return False

    print("daily summary 실패")
    print(payload)
    print(res.status_code, res.text)
    raise SystemExit


if __name__ == "__main__":
    total = 0
    current = START_DATE

    print("1) sensor_logs mock 데이터 생성 시작")

    while current < END_DATE:
        for node_id in NODE_IDS:
            send_sensor_log(node_id, current)
            total += 1

            if total % 100 == 0:
                print(f"{total}건 전송 완료 / 현재: {current.isoformat()}")

            time.sleep(REQUEST_DELAY_SECONDS)

        current += timedelta(hours=INTERVAL_HOURS)

    print(f"sensor_logs 생성 완료: {total}건")

    print("2) daily_summaries 생성 시작")

    day = START_DATE.date()
    end_day = END_DATE.date()

    summary_total = 0
    while day < end_day:
        for node_id in NODE_IDS:
            create_daily_summary(node_id, day)
            summary_total += 1
            time.sleep(REQUEST_DELAY_SECONDS)

        day += timedelta(days=1)

    print(f"daily_summaries 생성 요청 완료: {summary_total}건")