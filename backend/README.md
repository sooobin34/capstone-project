# AWD Water Management Backend

논 AWD(Alternate Wetting and Drying) 물관리 데이터를 기반으로  
수위 데이터 저장, 알림 생성, 일일 요약, MRV 보고서 생성을 수행하는 백엔드 API 서버입니다.

## 1. 기술 스택

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Uvicorn

---

## 2. 주요 기능

- IoT 센서 노드 등록 및 조회
- 센서 수위 데이터 저장
- 임계 수위 기준 알림 자동 생성
- 기간별 센서 로그 조회
- 일일 수위 상태 요약 생성
- 월별 MRV 보고서 생성
- 대시보드 요약 데이터 조회
- Mock Sensor Data 자동 전송 테스트 지원

---

## 3. 프로젝트 구조

```text
backend
 ┣ app
 ┃ ┣ api
 ┃ ┃ ┣ nodes.py
 ┃ ┃ ┣ sensor_logs.py
 ┃ ┃ ┣ alerts.py
 ┃ ┃ ┣ daily_summaries.py
 ┃ ┃ ┣ mrv_reports.py
 ┃ ┃ ┣ deps.py
 ┃ ┃ ┗ dashboard.py
 ┃ ┣ core
 ┃ ┃ ┣ config.py
 ┃ ┃ ┗ database.py
 ┃ ┣ models
 ┃ ┃ ┣ iot_node.py
 ┃ ┃ ┣ sensor_log.py
 ┃ ┃ ┣ alert.py
 ┃ ┃ ┣ awd_daily_summary.py
 ┃ ┃ ┗ mrv_report.py
 ┃ ┣ schemas
 ┃ ┃ ┣ iot_node.py
 ┃ ┃ ┣ sensor_log.py
 ┃ ┃ ┣ alert.py
 ┃ ┃ ┣ awd_daily_summary.py
 ┃ ┃ ┣ dashboard.py
 ┃ ┃ ┗ mrv_report.py
 ┃ ┣ utils
 ┃ ┃ ┗ response.py
 ┃ ┗ main.py
 ┣ mock_sensor_sender.py
 ┗ README.md

```

---

## 4. 데이터베이스 테이블
### 1) iot_nodes
센서 장치 정보 및 지도 표시용 위치 데이터

- id
- mac_address
- latitude
- longitude
- location_desc
- is_active
- created_at

### 2) sensor_logs
15분 단위 수위 및 배터리 원천 데이터

- id
- node_id
- inner_water_level
- outer_water_level
- battery_voltage
- measured_at

### 3) alerts
수위 이상 발생 시 생성되는 알림 이력

- id
- node_id
- alert_type
- message
- is_resolved
- created_at

### 4) awd_daily_summaries
일 단위 수위 평균 및 상태 요약

- id
- node_id
- record_date
- daily_status
- avg_inner_level

### 5) mrv_reports
월 단위 AWD 수행 횟수 및 탄소 감축 결과

- id
- report_month
- total_awd_cycles
- carbon_reduction
- created_at

---

## 5. 주요 API 목록

### 노드
- GET /nodes : 노드 목록 조회
- POST /nodes : 노드 등록

### 센서 로그

- POST /sensor-logs : 센서 로그 저장

- GET /sensor-logs/node/{node_id} : 특정 노드 로그 조회

- GET /sensor-logs/node/{node_id}?start=YYYY-MM-DD&end=YYYY-MM-DD : 기간별 로그 조회

### 알림

- GET /alerts : 알림 목록 조회

- PATCH /alerts/{alert_id}/resolve : 알림 해결 처리

### 일일 요약

- POST /daily-summaries : 일일 요약 생성

- GET /daily-summaries : 일일 요약 조회

### MRV 보고서

- POST /mrv-reports : MRV 보고서 생성

- GET /mrv-reports : MRV 보고서 조회

### 대시보드

- GET /dashboard : 대시보드 요약 조회

---

## 6. 공통 응답 구조
정상 응답은 아래 구조를 사용합니다.

```bash
{
  "success": true,
  "message": "설명 메시지",
  "data": {},
  "error": null
}
```

오류 응답은 일부 API에서 FastAPI 기본 detail 구조를 사용할 수 있습니다.

---

## 7. 서버 로직 기준
### 수위 알림 기준

- LOW_WATER: inner_water_level <= -15

- HIGH_WATER: inner_water_level >= 5

### 일일 상태 판정 기준

- avg_inner_level >= 0 → FLOODED

- -15 < avg_inner_level < 0 → DRYING

- avg_inner_level <= -15 → DRY

### MRV 계산식

- carbon_reduction = total_awd_cycles * 15.25

---

## 8. 실행 방법
### 1) 가상환경 활성화

Git Bash 기준:
```bash
source venv/Scripts/activate
```

Windows CMD 기준:
```bash
venv\Scripts\activate
```

### 2) 패키지 설치
```bash
pip install -r requirements.txt
```

### 3) 서버 실행
```bash
uvicorn app.main:app --reload
```

### 4) Swagger 접속
```text
http://127.0.0.1:8000/docs
```

### 5) DB 연결 테스트
```text
http://127.0.0.1:8000/db-test
```

---

## 9. Mock Sensor 테스트

테스트용 센서 데이터를 자동으로 서버에 전송하는 스크립트입니다.

### 실행 파일
- mock_sensor_sender.py

### 실행 방법
```bash
python mock_sensor_sender.py
```

### 설명

- 현재는 테스트용으로 5초 간격 전송
- POST /sensor-logs로 자동 데이터 저장
- LOW_WATER / HIGH_WATER 알림 테스트 가능

---

### 10. 테스트 완료 항목

- Swagger API 테스트 완료
- Postman 정상 응답 테스트 완료
- Postman 오류 응답 테스트 완료
    - 400
    - 404
    - 422
- Mock Sensor 연동 테스트 완료
- 알림 자동 생성 테스트 완료

- 기간별 로그 조회 테스트 완료

- 일일 요약 생성/조회 테스트 완료

- MRV 보고서 생성/조회 테스트 완료

- 대시보드 조회 테스트 완료

---

## 11. 현재 개발 상태

현재 백엔드 핵심 기능 구현 및 테스트는 거의 완료되었으며,
남은 작업은 아래와 같습니다.

- Render 배포 준비
- Render 시험 배포 및 테스트
- 프론트엔드 연동
- README 보완 및 발표 자료 정리

---

## 12. 참고 사항

- node_id는 초음파 센서 개수가 아니라 IoT 장치 1대 단위입니다.

- 현재 서버 로직은 inner_water_level 기준으로 상태 판정 및 알림을 생성합니다.

- outer_water_level은 현재 보조 데이터로 저장만 하고 있습니다.