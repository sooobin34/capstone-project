import random
import time
import requests
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

BASE_URL = "https://capstone-project-54l6.onrender.com"
ENDPOINT = f"{BASE_URL}/sensor-logs"
SEND_INTERVAL_SECONDS = 5  # 데이터 보내는 주기(10분)
NODE_IDS = [1, 2, 3]


def generate_mock_payload(node_id: int):
    inner_water_level = round(random.uniform(-20.0, 8.0), 2)
    outer_water_level = round(random.uniform(-2.0, 8.0), 2)
    battery_voltage = round(random.uniform(3.55, 3.75), 2)

    return {
        "node_id": node_id,
        "inner_water_level": inner_water_level,
        "outer_water_level": outer_water_level,
        "battery_voltage": battery_voltage,
        "measured_at": datetime.now(KST).isoformat()
    }


def send_mock_data(node_id: int):
    payload = generate_mock_payload(node_id)

    try:
        response = requests.post(ENDPOINT, json=payload, timeout=5)

        print("=" * 60)
        print(f"node_id: {node_id}")
        print("보낸 데이터:", payload)
        print("status_code:", response.status_code)
        print("response:", response.json())

    except requests.RequestException as e:
        print("=" * 60)
        print(f"node_id: {node_id}")
        print("전송 실패:", e)


if __name__ == "__main__":
    while True:
        for node_id in NODE_IDS:
            send_mock_data(node_id)

        time.sleep(SEND_INTERVAL_SECONDS)