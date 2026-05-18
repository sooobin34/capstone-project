# AWD Water Management Frontend

논 AWD(Alternate Wetting and Drying) 물관리 데이터를 시각화하고  
수위 모니터링, 알림 확인, MRV 보고서 관리, 현장 검증을 수행하는 프론트엔드 웹 애플리케이션입니다.

## 1. 기술 스택

- React + TypeScript (Vite)
- react-router-dom
- Axios
- Chart.js / react-chartjs-2
- Leaflet / react-leaflet

---

## 2. 주요 기능

- 전체화면 지도 기반 메인 페이지 (지도 / 스카이뷰 전환)
- 논·노드 등록 및 전라북도 지역별 필터링
- 노드별 실시간 수위 조회 및 기간별 그래프
- 수위 이상 알림 목록 조회 및 해결 처리
- 월별 MRV 보고서 생성 및 PDF / Excel 다운로드
- 현장 검증 사진 업로드 및 AI 분석
- 반응형 UI (PC / 모바일)

---

## 3. 프로젝트 구조

```text
frontend/src/
 ┣ api/
 ┃ ┣ axios.ts              # Axios 인스턴스 설정
 ┃ ┗ dashboard.ts          # API 호출 함수 모음
 ┣ assets/                 # 이미지, 로고 (AquaPaddy)
 ┣ components/
 ┃ ┣ dashboard/            # 대시보드 컴포넌트
 ┃ ┣ map/                  # 지도 관련 컴포넌트
 ┃ ┃ ┣ FieldMap.tsx        # Leaflet 지도
 ┃ ┃ ┣ FieldInfo.tsx       # 노드 상태 패널
 ┃ ┃ ┗ MapPanel.tsx        # 왼쪽 슬라이드 패널
 ┃ ┣ mrv/                  # MRV 관련 컴포넌트
 ┃ ┗ sensor/               # 센서 데이터 컴포넌트
 ┣ data/
 ┃ ┗ regions.ts            # 전라북도 시군 목록
 ┣ pages/
 ┃ ┣ Home.tsx              # 대시보드
 ┃ ┣ MapPage.tsx           # 지도 (메인)
 ┃ ┣ SensorData.tsx        # 센서 데이터
 ┃ ┣ AlertPage.tsx         # 알림
 ┃ ┣ MrvPage.tsx           # MRV 보고서
 ┃ ┗ ValidationPage.tsx    # 검증 사진
 ┗ vite-env.d.ts
```

---

## 4. 페이지 구성 및 주요 기능

| 페이지 | 경로 | 설명 |
|---|---|---|
| Map | `/map` | 메인 페이지. 전체화면 지도 + 왼쪽 패널 |
| Dashboard | `/dashboard` | 전체 현황 요약 |
| Sensor Data | `/sensor` | 노드별 수위 그래프 및 통계 |
| Alerts | `/alerts` | 수위 이상 알림 목록 및 해결 처리 |
| MRV | `/mrv` | 월별 MRV 보고서 조회 및 다운로드 |
| Validation | `/validation` | 현장 검증 사진 등록 및 AI 분석 |

### 1) Map 페이지 (메인)
- 전체화면 지도 + 왼쪽 슬라이드 패널 (토글 가능)
- 지도 / 스카이뷰 전환
- 지역 필터링 → 논 선택 → 노드 마커 표시
- 노드 클릭 시 수위·상태 정보 카드 표시
- 모바일: 패널 기본 닫힘, 논 선택 시 자동 닫힘

### 2) Dashboard 페이지
- 전체 논·기기 수, 미해결 알람, 최근 측정 시간 요약 카드
- 논/노드 선택 시 현재 수위·그래프·알람·MRV 요약 연동
- 지도 미니맵, 수위 추이 24시간 그래프

### 3) Sensor Data 페이지
- 논 선택 → 노드별 최신 측정 데이터 테이블
- 1시간 / 1일 / 1주 / 1개월 기간 선택
- 24시간 평균·최고·최저 통계 카드

### 4) Alerts 페이지
- 미해결 알람·24시간 발생·전체 알람 요약 카드
- 논별·알림 타입별 필터링
- 알림 해결 처리 (PATCH /alerts/{id}/resolve)

### 5) MRV 페이지
- 논 선택 + 월 선택 후 보고서 생성 (POST /mrv-reports)
- 월별 MRV 보고서 목록 조회 및 정렬
- PDF / Excel 다운로드

### 6) Validation 페이지
- 현장 테스트 탭: 현장 사진 업로드 및 검증, AI 분석 버튼
- 자동 분석 탭: 검증 기록 목록, 상태·날짜 필터링, 사진 모달 확대 보기

---

## 5. 실행 방법

```bash
cd frontend
npm install
npm run dev
```

---

## 6. 환경변수

```text
VITE_API_URL=https://capstone-project-54l6.onrender.com
```

---

## 7. 미해결 / 개선 예정

- 카카오맵 API 연동 (한국어 지도, 구름 없는 스카이뷰)
- 검증 사진 영구 저장 (현재 Render 무료플랜 한계 → S3 등 외부 스토리지 필요)
- AI 분석 기능 (백엔드 OpenAI API 키 설정 필요)
- LoRa 웹훅 API 연동 후 노드 센서 데이터 자동 표시