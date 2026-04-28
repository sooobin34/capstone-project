# AWD Water Management Backend

논 AWD(Alternate Wetting and Drying) 물관리 데이터를 기반으로  
수위 데이터 저장, 알림 생성, 일일 요약, MRV 보고서 생성 및 검증을 수행하는 백엔드 API 서버입니다.

---

## 1. 기술 스택

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Uvicorn
- ReportLab (PDF 생성)
- OpenPyXL (Excel 생성)

---

## 2. 주요 기능

- IoT 센서 노드 등록 및 상태 조회
- 센서 수위 데이터 저장 및 조회
- 24시간 수위 통계 집계 (평균/최대/최소)
- 임계 수위 기반 알림 자동 생성
- 알림 필터링 및 24시간 알람 건수 조회
- 일일 수위 상태 요약 생성
- 월별 MRV 보고서 생성
- MRV 상태 관리 (작성중 / 완료)
- MRV 검증(V) 데이터 관리
- MRV PDF / Excel 다운로드
- 월간 수위 운영 요약, 검증(V) 데이터, 대표 이미지 URL 기반 보고서 출력 지원
- 대시보드 통합 데이터 조회
- Mock Sensor Data 테스트 지원

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
 ┃ ┃ ┣ fields.py
 ┃ ┃ ┣ validations.py
 ┃ ┃ ┗ dashboard.py
 ┃ ┣ core
 ┃ ┃ ┣ config.py
 ┃ ┃ ┗ database.py
 ┃ ┣ fonts
 ┃ ┃ ┣ NanumGothic.ttf
 ┃ ┃ ┣ NanumMyeongjo.ttf
 ┃ ┃ ┗ NanumMyeongjoBold.ttf
 ┃ ┣ models
 ┃ ┃ ┣ iot_node.py
 ┃ ┃ ┣ sensor_log.py
 ┃ ┃ ┣ alert.py
 ┃ ┃ ┣ awd_daily_summary.py
 ┃ ┃ ┣ field.py
 ┃ ┃ ┣ validation_record.py
 ┃ ┃ ┗ mrv_report.py
 ┃ ┣ schemas
 ┃ ┃ ┣ iot_node.py
 ┃ ┃ ┣ sensor_log.py
 ┃ ┃ ┣ alert.py
 ┃ ┃ ┣ awd_daily_summary.py
 ┃ ┃ ┣ dashboard.py
 ┃ ┃ ┣ field.py
 ┃ ┃ ┣ validation_record.py
 ┃ ┃ ┗ mrv_report.py
 ┃ ┣ utils
 ┃ ┃ ┗ response.py
 ┃ ┗ main.py
 ┣ mock_sensor_sender.py
 ┗ README.md
```

---

## 4. 데이터베이스 테이블

### 1) fields (논/구역)
→ 농경지(논) 단위의 기본 위치 및 식별 정보를 저장하는 테이블

- id
- field_name
- latitude
- longitude
- location_desc
- created_at

### 2) iot_nodes
→ 논에 설치된 IoT 센서 장치의 위치 및 상태 정보를 저장하는 테이블

- id
- field_id
- mac_address
- latitude
- longitude
- location_desc
- is_active
- created_at

### 3) sensor_logs
→ 센서에서 측정된 수위 및 배터리 데이터를 시간 단위로 저장하는 테이블

- id
- node_id
- inner_water_level
- outer_water_level
- battery_voltage
- measured_at

### 4) alerts
→ 수위 이상 발생 시 생성되는 알림 이력 데이터를 저장하는 테이블

- id
- node_id
- alert_type
- message
- is_resolved
- created_at

### 5) awd_daily_summaries
→ 일 단위로 수위 평균 및 상태(OVERFLOODED / FLOODED / DRYING / DRY)를 요약한 테이블

- id
- node_id
- record_date
- daily_status
- avg_inner_level
- verification_image_url

### 6) mrv_reports
→ 월 단위 AWD 수행 결과 및 탄소 감축량을 저장하는 보고서 테이블

- id
- field_id
- report_month
- total_awd_cycles
- flood_days
- status
- carbon_reduction
- created_at

※ 검증 결과는 mrv_reports 테이블에 직접 저장하지 않고, validation_records를 조회하여 보고서 생성 시 자동 집계한다.

### 7) validation_records
→ 현장 촬영 이미지 기반 검증 데이터를 저장하는 테이블

- id
- field_id
- node_id
- record_date
- image_url
- image_title
- sensor_predicted_status
- observed_surface_status
- is_match
- note
- created_at

---

## 5. 주요 API 목록

### 노드
- GET /nodes : 노드 목록 조회
- POST /nodes : 노드 등록
- GET /nodes/{node_id}/status : 노드 현재 상태 및 최신 수위 조회


### 센서 로그

- POST /sensor-logs : 센서 로그 저장

- GET /sensor-logs/node/{node_id} : 특정 노드 로그 조회

- GET /sensor-logs/node/{node_id}?start=YYYY-MM-DD&end=YYYY-MM-DD : 기간별 로그 조회

- GET /sensor-logs/node/{node_id}/stats?hours=24 : 24시간 수위 통계 (평균/최대/최소) 조회

- GET /sensor-logs/node/{node_id}/range?period=1h|1d|1w|1m : 그래프용 기간별 로그 조회


### 알림

- GET /alerts : 알림 목록 조회

- GET /alerts?node_id=&alert_type=&is_resolved= : 알림 필터 조회

- GET /alerts/count?node_id=1&hours=24 : 24시간 알람 건수 조회

- PATCH /alerts/{alert_id}/resolve : 알림 해결 처리


### 일일 요약

- POST /daily-summaries : 일일 요약 생성

- GET /daily-summaries : 일일 요약 조회


### MRV 보고서

- POST /mrv-reports : MRV 보고서 생성

- GET /mrv-reports : MRV 보고서 조회

- PATCH /mrv-reports/{report_id}/status : MRV 상태 변경 (작성중 / 완료)

- GET /mrv-reports/{report_id}/download/pdf : MRV PDF 다운로드

- GET /mrv-reports/{report_id}/download/excel : MRV Excel 다운로드


### 대시보드

- GET /dashboard : 대시보드 요약 조회

### 검증 데이터

- POST /validations : 검증 사진/기록 등록
- GET /validations : 검증 기록 조회
- PATCH /validations/{validation_id} : 검증 기록 수정

---

## 6. 공통 응답 구조
정상 응답은 아래 구조를 사용합니다.

```json
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
※ 수위 기준(-15cm, +5cm)을 기반으로 일일 상태를 4단계로 세분화하여 분석 정확도를 향상시킴

- avg_inner_level >= 5 → OVERFLOODED
- 0 <= avg_inner_level < 5 → FLOODED
- -15 < avg_inner_level < 0 → DRYING
- avg_inner_level <= -15 → DRY

### MRV 계산식

- carbon_reduction = total_awd_cycles * 15.25

### MRV 집계 기준

- 일일 대표 상태는 같은 날짜의 노드별 일일 요약 데이터를 평균하여 산정한다.
- total_awd_cycles: 일일 대표 상태 기준으로 DRY → FLOODED 전환 횟수
- flood_days: 일일 대표 상태가 FLOODED 또는 OVERFLOODED인 날짜 수
- carbon_reduction: total_awd_cycles × 15.25

### 현장 검증(V) 기준

- sensor_predicted_status는 센서 기반 상태값으로 OVERFLOODED / FLOODED / DRYING / DRY 중 하나를 사용한다.
- observed_surface_status는 현장 사진 기반 표면 상태값으로 WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN 중 하나를 사용한다.
- FLOODED 또는 OVERFLOODED 상태에서 WATER_VISIBLE이면 일치로 판단한다.
- DRYING 또는 DRY 상태에서 NO_WATER_VISIBLE이면 일치로 판단한다.
- UNKNOWN은 판별 불가 상태로 사용한다.
- 사진 검증은 수위 cm를 직접 검증하는 것이 아니라, 표면 담수 여부를 확인하는 보조 검증으로 사용한다.

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
로컬 실행 시:
```text
http://localhost:8000/docs
```

Render 배포 서버:
```text
https://capstone-project-54l6.onrender.com/docs
```

### 5) DB 연결 테스트
로컬 실행 시:
```text
http://localhost:8000/db-test
```
Render 배포 서버:
```text
https://capstone-project-54l6.onrender.com/db-test
```
- 데이터베이스 연결 상태 확인용

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

- 테스트용 센서 데이터를 일정 간격으로 자동 전송
- POST /sensor-logs 엔드포인트로 데이터 저장
- LOW_WATER / HIGH_WATER 알림 생성 테스트 가능
- node_id 기준으로 다중 노드(예: 1, 2, 3) 테스트 가능

---
## 10. MRV 보고서 구조

MRV 보고서는 다음 흐름으로 생성됩니다.
센서 로그 → 일일 요약 → 날짜별 대표 상태 집계 → validation_records 월별 집계 → MRV 보고서 생성

- MRV는 자동 생성이 아닌 수동 생성 방식
- POST /mrv-reports 호출 시 생성됨
- 생성 요청값은 field_id, report_month만 사용
- validation 데이터는 validation_records에서 월별로 자동 집계됨
- 동일한 월 데이터는 중복 생성 불가

### 포함 내용

- 월간 수위 운영 요약
- AWD 수행 횟수
- 담수 유지 일수
- 탄소감축 추정량
- 검증(V) 데이터
- 대표 이미지 URL

---


## 11. 테스트 완료 항목

### 1) 기본 API 테스트
- Swagger API 테스트 완료
- Postman 정상 응답 테스트 완료
- Postman 오류 응답 테스트 완료
  - 400
  - 404
  - 422


### 2) 센서 데이터 및 알림
- Mock Sensor 연동 테스트 완료
- 센서 로그 저장 및 조회 테스트 완료
- 기간별 로그 조회 테스트 완료
- 24시간 수위 통계 API 테스트 완료
- 알림 자동 생성 테스트 완료
- 알림 필터 및 24시간 알람 건수 조회 테스트 완료


### 3) 일일 요약
- 일일 요약 생성 테스트 완료
- 일일 요약 조회 테스트 완료


### 4) MRV 보고서
- MRV 보고서 생성/조회 로직 구현 완료
- MRV PDF / Excel 다운로드 기능 구현 완료
- validation_records DB 반영 후 최종 Swagger 테스트 예정


### 5) 대시보드
- 대시보드 요약 조회 테스트 완료
- 최근 알림 및 최신 센서 데이터 반영 확인 완료

---

## 12. 현재 개발 상태

- 백엔드 API 구현 진행 중
- Render 배포 서버 운영 중
- validation_records 테이블 추가 후 MRV 검증 데이터 연동 예정
- 프론트 연동 진행 중
- MRV PDF / Excel 보고서 형식 보강 완료

---

## 13. 참고 사항

- node_id는 초음파 센서 개수가 아니라 IoT 장치 1대 단위입니다.
- 현재 서버 로직은 inner_water_level 기준으로 상태 판정 및 알림을 생성합니다.
- outer_water_level은 현재 보조 데이터로 저장만 하고 있습니다.
- verification_image_url은 일일 요약 단위의 검증 이미지 URL 저장에 사용됩니다.
- MRV 보고서의 validation 데이터는 월간 검증 결과 요약에 사용됩니다.
- MRV PDF는 대표 검증 이미지 URL을 포함한 보고서형 출력이 가능하도록 구성하였습니다.