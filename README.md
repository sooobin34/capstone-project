# 🌾 AI 기반 AWD 논 수위 모니터링 및 MRV 자동화 시스템

LoRaWAN 기반 실시간 수위 센서와 AI 이미지 분석을 활용한 스마트 논 관리 플랫폼

---

# 🌐 IoT + AI 기반 스마트 AWD 통합 솔루션

📆 2026.03 ~ 진행중
🏫 전북대학교 컴퓨터공학부 캡스톤 디자인 프로젝트
🌱 스마트 농업 및 MRV 자동화 연구 프로젝트

---

# 🌟 프로젝트 소개

본 프로젝트는 AWD(Alternate Wetting and Drying) 농법을 위한 실시간 논 수위 모니터링 및 MRV(Measurement, Reporting, Verification) 자동화 시스템입니다.

LoRaWAN 기반 IoT 센서와 AI 이미지 분석 기술을 활용하여 논의 상태를 실시간으로 수집·분석하고, 자동으로 AWD 상태를 판별하여 MRV 보고서를 생성하는 통합 플랫폼을 구축하였습니다.

기존의 수작업 중심 농업 관리 방식에서 벗어나:

* 실시간 센서 데이터 수집
* AI 기반 이미지 검증
* 자동 상태 분석
* 클라우드 기반 대시보드 시각화
* 자동 MRV 보고서 생성

을 통해 스마트 농업 자동화를 목표로 합니다.

---

# 🙋‍♀️ 프로젝트 팀

## 👨‍💻 캡스톤 프로젝트 팀

##### 여기 내용 채워야함.

---

# 📦 프로젝트 구성 (여기 수정해야됨)

| 폴더                     | 설명                        |
| ---------------------- | ------------------------- |
| backend/               | FastAPI 기반 백엔드 서버         |
| frontend/              | React 기반 프론트엔드            |
| iot/                   | STM32 + LoRaWAN 펌웨어       |
| data/                  | AI 학습용 논 수위 이미지 데이터셋      |
| data_boundary_low_mid/ | LOW-MID 경계 전용 데이터셋        |
| ml/                    | PyTorch 기반 AI 학습 및 추론 시스템 |

---

# 🛠 기술 스택

## Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* Alembic
* Pydantic

## AI

* OpenAI Vision API
* 이미지 기반 논 상태 분석

## Frontend

* React
* Vite
* Vercel

## Embedded / IoT

* STM32WL55JC1
* LoRaWAN
* ChirpStack
* Ultrasonic Sensor (A02YYUW)
* UART Communication

## Infrastructure

* Render
* GitHub
* GitHub Actions

---

# 📌 주요 기능

| 기능               | 설명                           |
| ---------------- | ---------------------------- |
| 🌊 실시간 수위 모니터링   | 초음파 센서를 이용한 논 수위 측정          |
| 📡 LoRaWAN 통신    | 장거리 저전력 데이터 송신               |
| 🛰 게이트웨이 연동      | ChirpStack 기반 센서 데이터 수집      |
| 🤖 AI 이미지 검증     | OpenAI Vision API 기반 논 상태 분석 |
| 📊 MRV 보고서 자동 생성 | AWD 상태 기반 자동 보고서 생성          |
| 📈 일일 상태 분석      | DRY / DRYING / FLOODED 상태 판별 |
| 🖥 실시간 대시보드      | 센서 데이터 및 검증 결과 시각화           |
| ☁ 클라우드 배포        | Render + Vercel 기반 운영        |

---

# 🔄 시스템 아키텍처

```text
Ultrasonic Sensor
        ↓
STM32WL55JC1
        ↓
LoRaWAN Gateway
        ↓
ChirpStack
        ↓
FastAPI Backend
        ↓
PostgreSQL Database
        ↓
Frontend Dashboard
```

---

# 📁 프로젝트 구조

```text
project/
 ┣ backend/
 ┃ ┣ app/
 ┃ ┃ ┣ api/
 ┃ ┃ ┣ models/
 ┃ ┃ ┣ core/
 ┃ ┃ ┣ services/
 ┃ ┃ ┣ utils/
 ┃ ┃ ┗ schemas/
 ┃ ┣ uploads/
 ┃ ┣ alembic/
 ┃ ┗ requirements.txt
 ┃
 ┣ frontend/
 ┃ ┣ src/
 ┃ ┣ pages/
 ┃ ┣ components/
 ┃ ┣ public/
 ┃ ┗ package.json
 ┃
 ┣ embedded/
 ┃ ┣ Core/
 ┃ ┣ LoRaWAN/
 ┃ ┣ Drivers/
 ┃ ┗ Sensors/
 ┃
 ┗ README.md
```

---

# 🧠 AI 수위 분류 시스템

## 📁 AI 데이터셋 구조

```text
data/
 ┣ train/
 ┃ ┣ low/
 ┃ ┣ mid/
 ┃ ┗ high/
 ┃
 ┣ val/
 ┃ ┣ low/
 ┃ ┣ mid/
 ┃ ┗ high/
 ┃
 ┗ test/
   ┣ low/
   ┣ mid/
   ┗ high/
```

### 클래스 기준 (여기 기준 수정!!)

| 클래스  | 수위 기준         |
| ---- | ------------- |
| LOW  | 0cm ~ 1.1cm   |
| MID  | 2.1cm ~ 3.5cm |
| HIGH | 4.5cm ~ 5cm   |

### 데이터 분리 기준

| 구분         | 촬영 높이                      |
| ---------- | -------------------------- |
| train      | 10cm / 50cm / 80cm / 110cm |
| validation | 140cm                      |
| test       | 170cm                      |

촬영 높이 일반화 성능을 검증하기 위해 높이 기준으로 train / validation / test를 분리하였습니다.

---

# 🔍 LOW-MID 경계 전용 데이터셋

실제 논 환경에서는 LOW(1cm)와 MID(2~3cm) 구간이 시각적으로 매우 유사하게 나타나는 문제가 존재하였습니다.

이를 개선하기 위해 LOW ↔ MID 경계 구간 전용 Binary 분류 데이터셋을 추가 구축하였습니다.

```text
data_boundary_low_mid/
 ┣ train/
 ┣ val/
 ┗ test/
```

각 폴더 내부:

```text
low/
mid/
```

### 목적

* LOW ↔ MID 경계 오분류 감소
* 계층형(Hierarchical) AI 구조 실험
* 실제 논 환경 일반화 성능 개선

---

# 🤖 머신러닝 시스템

## 📁 ML 프로젝트 구조

```text
ml/
 ┣ train_water_classifier.py
 ┣ evaluate_water_classifier.py
 ┃
 ┣ train_boundary_low_mid.py
 ┣ evaluate_boundary_low_mid.py
 ┃
 ┣ evaluate_hierarchical_classifier.py
 ┣ inference.py
 ┃
 ┣ models/
 ┃ ┣ water_classifier_best.pth
 ┃ ┗ water_classifier_low_mid_best.pth
```

---

## 🧠 기본 모델

* PyTorch ResNet18 기반 CNN 사용
* LOW / MID / HIGH 3단계 수위 분류 수행
* 실제 논 환경 이미지 기반 학습

---

## 🧠 계층형(Hierarchical) 구조

```text
1차 모델:
LOW / MID / HIGH 분류

↓

MID로 판단된 경우

↓

2차 LOW-MID 경계 모델 재검사 수행
```

이를 통해 LOW ↔ MID 오분류를 일부 개선하였으며,
최종 test accuracy 87.67%를 달성하였습니다.

---

## 🔬 AI 추론 시스템

`inference.py`는 FastAPI와 연동되는 실제 추론 코드입니다.

업로드된 논 이미지를 입력받아:

* LOW
* MID
* HIGH

수위를 예측하고 confidence 값을 반환합니다.

예시:

```json
{
  "predicted_class": "LOW",
  "confidence": 0.54
}
```

---

# 🤖 AI 이미지 검증 시스템

## 📷 Validation 시스템

사용자가 업로드한 논 이미지를 OpenAI Vision API로 분석하여:

* 물 존재 여부
* 침수 상태
* 논 표면 상태
* AWD 상태 가능성

등을 자동 판별합니다.

## 🔍 분석 결과 예시

| 상태               | 설명           |
| ---------------- | ------------ |
| WATER_VISIBLE    | 논 표면에 물이 존재  |
| NO_WATER_VISIBLE | 물이 보이지 않는 상태 |
| UNKNOWN          | 판별 어려움       |

분석 결과는 validation_records 테이블에 저장되며, 이후 MRV 보고서 생성 시 활용됩니다.

---

# 📊 MRV 자동 생성 시스템

## 🌾 AWD 상태 분석

센서 로그와 AI 검증 데이터를 기반으로 논 상태를 자동 분석합니다.

| 상태      | 설명         |
| ------- | ---------- |
| FLOODED | 침수 상태      |
| DRYING  | 물이 감소하는 상태 |
| DRY     | 건조 상태      |

## 📈 자동 생성 기능

* 일일 요약 생성
* AWD 전환 횟수 계산
* 침수 지속 시간 계산
* 검증 결과 통합
* MRV 보고서 자동 생성

---

# 🗄 데이터베이스 구조

## 주요 테이블

| 테이블                 | 설명           |
| ------------------- | ------------ |
| fields              | 논 정보 저장      |
| iot_nodes           | 센서 노드 정보     |
| sensor_logs         | 수위 데이터 저장    |
| validation_records  | 이미지 검증 결과 저장 |
| awd_daily_summaries | 일일 AWD 상태 저장 |
| mrv_reports         | MRV 보고서 저장   |
| alerts              | 경고 정보 저장     |

---

# 🌐 API 구성

## 주요 API

| API              | 설명         |
| ---------------- | ---------- |
| /nodes           | 센서 노드 조회   |
| /sensor_logs     | 센서 데이터 조회  |
| /validations     | 이미지 검증 API |
| /daily_summaries | AWD 상태 요약  |
| /mrv_reports     | MRV 보고서 생성 |
| /dashboard       | 대시보드 통계    |
| /alerts          | 경고 시스템     |

---

# 📡 LoRaWAN 시스템 (여기 수정해야됨)

## 통신 구조

* STM32 → LoRaWAN 송신
* Gateway → ChirpStack 수신
* ChirpStack → Webhook 전송
* FastAPI → DB 저장

## 사용 기술

| 기술            | 설명                     |
| ------------- | ---------------------- |
| STM32WL55JC1  | LoRa 내장 MCU            |
| ChirpStack    | LoRaWAN Network Server |
| UART          | 초음파 센서 통신              |
| KR920 / AS923 | LoRaWAN Region 설정      |

---

# ☁ 클라우드 배포

## Backend

* Render 배포
* FastAPI 운영
* PostgreSQL 연결

## Frontend

* Vercel 배포
* React 기반 SPA 운영

## Swagger Docs

```text
https://your-render-url.onrender.com/docs
```

---

# ⚙ 실행 방법

## 1️⃣ Backend 실행

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## 2️⃣ Frontend 실행

```bash
cd frontend

npm install
npm run dev
```

---

## 3️⃣ STM32 펌웨어

```text
STM32CubeIDE 사용

주요 설정:
- LoRaWAN 활성화
- UART 활성화
- Region 설정
- AppKey / DevEUI 설정
```

---

# 🔬 주요 개발 내용

## 🌊 센서 데이터 처리

* 초음파 거리값 측정
* 논 수위 계산
* 배터리 전압 측정
* LoRa Payload 생성
* Gateway 전송

## 🤖 AI 이미지 분석

* 논 사진 업로드
* OpenAI Vision API 호출
* 물 존재 여부 판별
* DB 저장

## 📊 MRV 시스템

* 센서 로그 분석
* 상태 전환 감지
* AWD 횟수 계산
* 자동 보고서 생성

---

# 📈 주요 성과

## 🎯 핵심 성과

✅ LoRaWAN 기반 장거리 센서 통신 구현
✅ 실시간 논 수위 데이터 수집 성공
✅ OpenAI Vision 기반 이미지 검증 기능 구현
✅ MRV 자동 생성 시스템 구축
✅ FastAPI + PostgreSQL 기반 API 서버 구축
✅ Render + Vercel 클라우드 배포 완료
✅ 실시간 대시보드 구현

---

# 🚀 향후 개선 방향 (여기 수정해야됨)

* 실시간 이상 탐지 기능 추가
* AI 기반 수위 예측 모델 개발
* 다중 센서 통합
* 모바일 앱 연동
* MQTT 기반 실시간 스트리밍
* GIS 지도 시각화 기능 추가

---

# 📚 참고 기술

## AI

* OpenAI Vision API

## Backend

* FastAPI
* SQLAlchemy
* PostgreSQL

## Embedded

* STM32CubeIDE
* LoRaWAN
* ChirpStack

## Deployment

* Render
* Vercel

---

# 📄 라이선스

본 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

Copyright © 2026 Capstone Project Team