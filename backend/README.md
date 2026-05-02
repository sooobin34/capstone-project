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
- LoRaWAN 게이트웨이 uplink payload 수신 및 sensor_logs 자동 저장
- 24시간 수위 통계 집계 (평균/최대/최소)
- 임계 수위 기반 알림 자동 생성
- 알림 필터링 및 24시간 알람 건수 조회
- 일일 수위 상태 요약 생성
- 월별 MRV 보고서 생성
- MRV 상태 관리 (작성중 / 완료)
- 사진 기반 검증 기록 저장 및 센서 상태와의 일치율 계산
- OpenAI Vision API 기반 검증 사진 자동 분석 (선택 기능)
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
 ┃ ┃ ┣ lora_webhook.py
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
 ┃ ┣ uploads
 ┃ ┃ ┗ validation_records
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
- verification_image_url: 일일 단위 대표 이미지 URL (현재는 보조 정보로 사용되며, 실제 검증은 validation_records 기준으로 수행됨)

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

### 6) validation_records
현장 사진 기반 검증 이력 데이터입니다.
센서가 예측한 상태와 사진 관찰 상태를 비교하여 검증 정확도를 계산합니다.

- id
- field_id
- node_id
- record_date
- captured_at
- image_url
- image_title
- camera_height_cm
- actual_water_level_cm
- sensor_predicted_status
- observed_surface_status
- ai_predicted_status
- ai_confidence
- ai_sensor_match
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

- POST /lora-webhook : LoRaWAN 게이트웨이 JSON 수신 후 Base64 payload를 센서 로그로 변환 저장

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

### 검증 사진

- POST /validations : 검증 사진 기록 저장

- POST /validations/upload : 검증 사진 파일 업로드 및 기록 저장

- GET /validations : 검증 사진 기록 조회

- GET /validations/summary : 검증 표본 수, 일치 수, 정확도 조회

- GET /validations/{validation_id} : 검증 사진 기록 단건 조회

- PATCH /validations/{validation_id} : 검증 사진 기록 수정

- GET /validations/{validation_id}/download : 검증 사진 다운로드 또는 URL 이동

- POST /validations/{validation_id}/analyze : OpenAI Vision 기반 사진 상태 분석

---

## 6. 검증 로직 (Validation Logic)

검증은 센서 데이터, 사람 관찰값, AI 분석 결과를 활용하여 2단계로 수행됩니다.

---

### 1단계: 센서 vs 사람 관찰값

- captured_at 기준 가장 가까운 sensor_log 조회
- inner_water_level(cm)을 WATER_VISIBLE / NO_WATER_VISIBLE로 변환
- observed_surface_status와 비교하여 is_match 계산

센서 상태 변환 기준:

- cm >= 0 → WATER_VISIBLE
- cm < 0 → NO_WATER_VISIBLE

비교 규칙:

- observed_surface_status = UNKNOWN → 비교 제외 (is_match = None)

센서값 조회 우선순위:

1. captured_at 기준 sensor_log
2. daily_summary (fallback)

---

### 2단계: 센서 vs AI 분석값

- is_match == True인 경우만 수행
- ai_predicted_status와 센서 상태 비교

```text
ai_sensor_match = (sensor == ai_predicted_status)
```

예외:

- AI 결과 = UNKNOWN → ai_sensor_match = None (비교 제외)

---

### 3단계: MRV 검증 데이터 활용

MRV 보고서 생성 시 다음 값을 사용한다.

- is_match → 센서 vs 사람 검증 결과
- ai_sensor_match → 센서 vs AI 검증 결과

정확도 계산 방식:

```text
sensor_observed_accuracy =
  is_match(True) / is_match(True + False)

ai_sensor_accuracy =
  ai_sensor_match(True) / ai_sensor_match(True + False)
```

※ None 값은 모두 제외  
※ AI가 UNKNOWN으로 판정된 데이터는 정확도 산정에서 제외

---

## 7. 서버 로직 기준

### 수위 알림 기준

- LOW_WATER: inner_water_level <= -15
- HIGH_WATER: inner_water_level >= 5

---

### 일일 상태 판정 기준

- avg_inner_level >= 5 → OVERFLOODED
- 0 <= avg_inner_level < 5 → FLOODED
- -15 < avg_inner_level < 0 → DRYING
- avg_inner_level <= -15 → DRY

---

### MRV 계산식

- carbon_reduction = total_awd_cycles × 15.25

---

### MRV 집계 기준

- 일일 대표 상태는 노드별 일일 요약 데이터를 평균하여 산정합니다.
- total_awd_cycles: DRY 이후 DRYING, FLOODED 또는 OVERFLOODED 상태로 전환되는 경우를 1회로 정의합니다.
- flood_days: FLOODED 또는 OVERFLOODED 상태인 날짜 수

---

### 검증 사진 상태 정의

- sensor_predicted_status  
  → 백엔드에서 자동 계산  
  → 우선순위:
  1. captured_at 기준 sensor_log
  2. daily_summary fallback

- observed_surface_status  
  → 사용자 입력  
  → WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN

- ai_predicted_status  
  → OpenAI Vision 분석 결과  
  → WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN

---

### 검증 입력 및 자동 생성 필드

프론트 입력:

- field_id
- node_id
- record_date
- captured_at
- image_title
- camera_height_cm
- actual_water_level_cm
- observed_surface_status
- note
- file

백엔드 자동 생성:

- image_url
- sensor_predicted_status
- ai_predicted_status
- ai_confidence
- is_match
- ai_sensor_match

---

## 8. LoRaWAN 및 공통 응답 구조

### LoRaWAN webhook 처리

- POST /lora-webhook
- Base64 payload 디코딩 후 sensor_logs 저장
- devEUI → iot_nodes.mac_address 매핑

payload 해석:

- 첫 2바이트 → 수위(mm)
- cm 단위로 변환

LoRaWAN webhook 요청 예시:

```json
{
  "devEUI": "0080E115061BF02C",
  "fPort": 1,
  "data": "AHs=",
  "time": "2026-05-02T23:00:00+09:00"
}
```

---

### 공통 응답 구조

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

### OpenAI Vision 분석

- OpenAI 분석은 선택 기능입니다.
- OPENAI_API_KEY가 없어도 검증 사진 저장, 조회, 업로드, 정확도 계산은 동작합니다.
- OPENAI_API_KEY가 없을 경우 POST /validations/{validation_id}/analyze API만 사용할 수 없습니다.


---

## 9. 실행 방법
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

### 6) 환경변수
```text
DATABASE_URL=PostgreSQL 연결 문자열
OPENAI_API_KEY=OpenAI API 키
OPENAI_VISION_MODEL=gpt-4.1-mini
```

OPENAI_API_KEY는 검증 사진 자동 분석 API를 사용할 때만 필요합니다.
DATABASE_URL, OPENAI_API_KEY 등 민감정보는 GitHub에 커밋하지 않습니다.

---

## 10. Mock Sensor 테스트

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

## 11. MRV 보고서 구조

MRV 보고서는 다음 흐름으로 생성됩니다.

센서 로그 → 일일 요약 → 날짜별 대표 상태 집계  
→ validation_records 기반 검증 데이터 집계  
→ MRV 보고서 생성

※ MRV 보고서는 센서 기반 데이터(daily_summary)와 현장 검증 데이터(validation_records)를 함께 사용하여 생성된다.

- MRV는 자동 생성이 아닌 수동 생성 방식
- POST /mrv-reports 호출 시 생성됨
- 생성 요청값은 field_id, report_month만 사용
- validation 데이터는 validation_records에서 월별로 자동 집계됨
- 동일한 월 데이터는 중복 생성 불가

---

### 포함 내용

- 월간 수위 운영 요약
- AWD 수행 횟수
- 담수 유지 일수
- 탄소감축 추정량
- 검증(V) 데이터 (센서 vs 사람, 센서 vs AI 포함)
- 대표 이미지 URL

---

### MRV PDF 구성

- 표지: 보고서 제목, 대상 논, 기간, 작성일 정보
- 목차: 주요 항목 페이지 구성
- 결과 분석: 주차별 및 월간 수위 변화 분석
- AWD 수행 및 탄소 감축 분석: 수행 기준, 횟수 및 탄소 감축량 산정

검증 결과:
- 센서 vs 사람 관찰값 검증 결과 (is_match 기반)
- 센서 vs AI 분석 결과 검증 (ai_sensor_match 기반)
- AI-센서 일치율 및 판별 불가 데이터 포함
- 대표 이미지 및 분석 결과

- 향후 계획 및 결론

※ AI 분석 결과 중 UNKNOWN으로 판정된 데이터는 AI-센서 일치율 산정에서 제외한다.

---

### MRV Excel 구성

- 요약: 월간 결과 요약 (상태별 일수, AWD 횟수, 탄소 감축량)
- 날짜별 흐름 데이터: 날짜 기준으로 노드별 수위 및 상태를 한 행에서 비교 가능
- 노드별 상세 데이터: 날짜별 노드 단위 상세 데이터

검증 상세:
- validation_records 기반 데이터
- 사람 판단 (observed_surface_status)
- AI 판단 (ai_predicted_status)
- 센서-사람 일치 여부 (is_match)
- 센서-AI 일치 여부 (ai_sensor_match)

---

※ 상태 정의
- OVERFLOODED: 과다 담수 상태
- FLOODED: 적정 담수 상태
- DRYING: 건조 진행 상태
- DRY: 재관개 필요 상태

---

## 12. 테스트 완료 항목

### 1) 기본 API 테스트
- Swagger API 테스트 완료
- Postman 정상 응답 테스트 완료
- Postman 오류 응답 테스트 완료
  - 400 / 404 / 422

### 2) 센서 데이터 및 알림
- Mock Sensor 연동 테스트 완료
- 센서 로그 저장 및 조회 테스트 완료
- LoRaWAN webhook 수신 및 sensor_logs 저장 테스트 완료
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
- validation_records 기반 검증 로직 및 MRV 연동 테스트 완료

### 5) 대시보드
- 대시보드 요약 조회 테스트 완료
- 최근 알림 및 최신 센서 데이터 반영 확인 완료

---

## 13. 현재 개발 상태

- 백엔드 API 구현 진행 중
- Render 배포 서버 운영 중
- validation_records 기반 검증 로직 개선 완료
- ai_sensor_match 로직 추가 완료
- MRV 검증 데이터 연동 완료
- LoRaWAN webhook API 구현 및 DevEUI 기반 노드 매핑 완료
- 프론트 연동 진행 중
- MRV PDF / Excel 보고서 형식 보강 완료

---

## 14. 참고 사항

- node_id는 IoT 장치 1대 단위
- inner_water_level 기준으로 상태 판정 및 알림 생성
- outer_water_level은 보조 데이터
- MRV 보고서의 validation 데이터는 월간 검증 결과 요약에 사용
- AI 분석 결과는 보조 검증 데이터로 활용
