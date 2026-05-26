import random
import time
import requests
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

BASE_URL = "https://capstone-project-54l6.onrender.com"
ENDPOINT = f"{BASE_URL}/sensor-logs"

NODE_IDS = [1,2,3,4,5,6,7]

START_DATE = datetime(2026, 5, 1, 0, 0, tzinfo=KST)
END_DATE = datetime(2026, 6, 1, 0, 0, tzinfo=KST)

INTERVAL_MINUTES = 60
REQUEST_DELAY_SECONDS = 0.5


def generate_inner_water_level(measured_at: datetime) -> float:
    day = measured_at.day

    # 월간 AWD 흐름 테스트용 패턴
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


def generate_mock_payload(node_id: int, measured_at: datetime):
    inner_water_level = generate_inner_water_level(measured_at)
    outer_water_level = round(random.uniform(-2.0, 8.0), 2)
    battery_voltage = round(random.uniform(3.55, 3.75), 2)

    return {
        "node_id": node_id,
        "inner_water_level": inner_water_level,
        "outer_water_level": outer_water_level,
        "battery_voltage": battery_voltage,
        "measured_at": measured_at.isoformat()
    }


def send_mock_data(node_id: int, measured_at: datetime):
    payload = generate_mock_payload(node_id, measured_at)

    try:
        response = requests.post(ENDPOINT, json=payload, timeout=30)

        if response.status_code not in (200, 201):
            print("=" * 60)
            print(f"node_id: {node_id}")
            print("보낸 데이터:", payload)
            print("status_code:", response.status_code)
            print("response:", response.text)
            raise SystemExit("전송 실패로 중단합니다.")

        return True

    except requests.RequestException as e:
        print("=" * 60)
        print(f"node_id: {node_id}")
        print("전송 실패:", e)
        raise SystemExit("요청 오류로 중단합니다.")


if __name__ == "__main__":
    current = START_DATE
    total = 0

    while current < END_DATE:
        for node_id in NODE_IDS:
            send_mock_data(node_id, current)
            total += 1

            if total % 300 == 0:
                print(f"{total}건 전송 완료 / 현재 시각: {current.isoformat()}")

            time.sleep(REQUEST_DELAY_SECONDS)

        current += timedelta(minutes=INTERVAL_MINUTES)

    print(f"전체 전송 완료: {total}건")