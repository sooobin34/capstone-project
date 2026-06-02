# 🌾 AI 기반 AWD 논 수위 모니터링 및 MRV 자동화 시스템

Gold Standard AWD 기반 논 물관리 데이터 수집·검증·보고 자동화를 위한 IoT + AI 통합 플랫폼


---

## 🌐 IoT · AI · Web 기반 AWD MRV 플랫폼

📅 2026.03 ~ 2026.06
🏫 전북대학교 컴퓨터인공지능학부 캡스톤디자인 프로젝트
🌱 AWD 관리 자동화 및 탄소감축 데이터 기반 구축 연구
📊 MRV(Measurement · Reporting · Verification) 체계 구현 및 탄소배출권 제도 연계를 위한 기반 플랫폼 구축

---

## 1. 프로젝트 소개

### 🌱 배경
벼농사는 전 세계 메탄(CH₄) 배출의 주요 발생원 중 하나이며, 논을 지속적으로 담수 상태로 유지할 경우 메탄 배출량이 증가합니다. Gold Standard AWD(Alternate Wetting and Drying)는 논을 주기적으로 담수와 배수 상태로 관리하여 메탄 배출을 줄이는 대표적인 물 관리 기법입니다.

### ⚠️ 기존 한계
그러나 실제 농가에서는 수위 측정, AWD 수행 여부 확인, 데이터 기록 및 보고 과정이 대부분 수작업으로 이루어져 관리 부담이 크고 지속적인 운영이 어렵습니다.

### 🎯 프로젝트 목표
본 프로젝트는 IoT 수위 센서, AI 기반 이미지 검증, 웹 기반 MRV(Measurement · Reporting · Verification) 시스템을 활용하여 AWD 관리 과정을 자동화하고 데이터 수집·검증·보고 체계를 구축하는 것을 목표로 합니다. 또한 향후 탄소감축량 산정 및 탄소배출권 제도 연계를 위한 MRV 기반 플랫폼 구축 가능성을 제시합니다.

---

## 2. 프로젝트 팀

### 팀 소개

(추후 작성)

### 담당 역할

(추후 작성)

### 지도교수 및 자문

(추후 작성)

---

# 3. 시스템 개요

## 3-1. MRV 프로세스

```text
Measure
↓
Report
↓
Verify
```

## 3-2. 시스템 아키텍처

(PPT 시스템 구조도 삽입)

## 3-3. 데이터 처리 흐름

```text
센서 데이터 수집
↓
일일 상태 분석
↓
AI 검증
↓
MRV 보고서 생성
```

---

# 4. 주요 기능

## 4-1. 실시간 수위 모니터링

* 초음파 센서를 이용한 논 수위 측정
* 시간별 수위 데이터 저장 및 조회
* 웹 대시보드를 통한 실시간 모니터링

## 4-2. LoRaWAN 기반 데이터 수집

* STM32WL55JC1 기반 센서 노드
* LoRaWAN 무선 통신
* Gateway를 통한 서버 데이터 전송

## 4-3. AI 기반 이미지 검증

* 논 사진 업로드
* LOW / MID / HIGH 상태 분류
* 센서 데이터와 AI 예측 결과 비교 검증

## 4-4. AWD 상태 분석

* OVERFLOODED : 과도한 침수 상태 감지
* FLOODED : 물이 충분히 존재하는 상태
* DRYING : AWD 수행을 위한 배수 진행 상태
* DRY : 재관개가 필요한 건조 상태

## 4-5. MRV 보고서 자동 생성

* PDF 보고서 생성
* Excel 보고서 생성
* 센서 데이터 및 검증 결과 통합

## 4-6. 통합 웹 서비스

* Dashboard
* Sensor Data
* Validation
* MRV Reports

---

# 5. 서비스 화면

## 5-1. Dashboard

(스크린샷 삽입)

## 5-2. Sensor Data

(스크린샷 삽입)

## 5-3. Validation

(스크린샷 삽입)

## 5-4. MRV Reports

(스크린샷 삽입)

---

# 6. 프로젝트 구조

## 6-1. 전체 프로젝트 구조

```text
backend/
frontend/
iot/
ml/
data/
data_boundary_low_mid/
```

## 6-2. Backend 구조

```text
backend/
 ┣ app/
 ┃ ┣ api/
 ┃ ┣ models/
 ┃ ┣ schemas/
 ┃ ┣ utils/
 ┃ ┗ core/
 ┣ uploads/
 ┗ requirements.txt
```

## 6-3. Frontend 구조

```text
frontend/
 ┣ src/
 ┣ public/
 ┣ assets/
 ┗ components/
```

## 6-4. IoT 구조

```text
iot/
 ┣ LoRaWAN_End_Node_LBM/
 ┣ Drivers/
 ┣ Core/
 ┗ Middleware/
```

## 6-5. AI 구조

```text
ml/
 ┣ train_water_classifier.py
 ┣ train_boundary_low_mid.py
 ┣ evaluate_hierarchical_classifier.py
 ┣ inference.py
 ┣ models/
 ┣ results/
 ┗ notebooks/
```

---

# 7. AI 수위 판별 시스템

## 7-1. 데이터 수집 환경

### 촬영 장비

* 스마트폰 카메라(iPhone)

### 촬영 조건

* 실제 논 환경 촬영
* 맑음 / 흐림 환경 포함

### 촬영 높이

* 10cm
* 50cm
* 80cm
* 110cm
* 140cm
* 170cm

## 7-2. 데이터 라벨링 기준

### LOW

* 0cm
* 1cm 수준

### MID

* 2~3cm 수준

### HIGH

* 4~5cm 수준

## 7-3. 데이터셋 구조

### Main Dataset

```text
train/
val/
test/
```

### LOW-MID Boundary Dataset

```text
data_boundary_low_mid/
 ┣ train/
 ┣ val/
 ┗ test/
```

## 7-4. 모델 구조

* ResNet18
* Transfer Learning
* Fine-tuning

## 7-5. 계층형(Hierarchical) 구조

```text
입력 이미지
      ↓
1차 ResNet18 모델
(LOW / MID / HIGH)
      ↓
MID 예측
      ↓
LOW-MID 경계 모델
      ↓
최종 결과 출력
```

## 7-6. 성능 평가

### Accuracy

* ResNet18 : 86.30%
* Hierarchical : 87.67%

### Confusion Matrix

(이미지 삽입)

### 모델 비교 결과

| Model           | Accuracy |
| --------------- | -------- |
| MobileNetV3     | 실험 결과    |
| EfficientNet-B0 | 실험 결과    |
| ResNet18        | 86.30%   |
| Hierarchical    | 87.67%   |

---

# 8. 기술 스택

## 8-1. Frontend

* React
* TypeScript
* Vite

## 8-2. Backend

* FastAPI
* SQLAlchemy
* PostgreSQL

## 8-3. AI

* PyTorch
* ResNet18

## 8-4. IoT

* STM32WL55JC1
* LoRaWAN
* A02YYUW Ultrasonic Sensor

## 8-5. Infrastructure

* Render
* Vercel
* GitHub

---

# 9. 주요 성과

## 9-1. 핵심 성과

* MRV 데이터 자동 수집·기록·관리 플랫폼 구축
* AI 기반 논 상태 검증 체계 구현
* IoT·AI·웹 통합 자동화 시스템 구현

## 9-2. 시스템 구현 결과

* 센서 데이터 수집 및 저장
* 웹 기반 모니터링 서비스 구현
* MRV 보고서 자동 생성 기능 구현

## 9-3. AI 모델 성능 결과

* ResNet18 기반 수위 분류 모델 구축
* 계층형 구조 적용을 통한 성능 개선

## 9-4. MRV 자동화 성과

* 데이터 수집 자동화
* 검증 자동화
* 보고 자동화

---

# 10. 향후 개선 방향

## 10-1. 실제 농가 실증 확대

## 10-2. AI 데이터셋 확장

## 10-3. AWD 자동 제어 시스템

## 10-4. 탄소감축량 산정 모델 연계

## 10-5. 탄소배출권 제도 연계

---

# 11. 배포 주소

## Frontend

(Frontend URL)

## Backend (Swagger)

(Backend URL)
