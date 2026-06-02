# AWD Water Management Frontend

논 AWD(Alternate Wetting and Drying) 물관리 데이터를 시각화하고  
수위 모니터링, 알림 확인, MRV 보고서 관리, 현장 검증을 수행하는 프론트엔드 웹 애플리케이션입니다.

## 1. 기술 스택

- React + TypeScript (Vite)
- react-router-dom
- Axios
- Chart.js / react-chartjs-2
- Leaflet / react-leaflet
- V-WORLD WMTS API (지도 타일)

---

## 2. 주요 기능

- 전체화면 지도 기반 메인 페이지 (지도 / 스카이뷰 전환, V-WORLD API)
- 논·노드 등록 및 전라북도 지역별 필터링
- 논/지역 선택 전역 연동 (한 번 선택 시 모든 페이지에 유지)
- 노드별 실시간 수위 조회 및 기간별 그래프
- 수위 이상 알림 목록 조회 및 해결 처리
- 월별 MRV 보고서 화면 표출 및 PDF / Excel 다운로드
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
 ┃ ┃ ┣ FieldMap.tsx        # Leaflet 지도 (V-WORLD WMTS)
 ┃ ┃ ┣ FieldInfo.tsx       # 노드 상태 패널
 ┃ ┃ ┗ MapPanel.tsx        # 슬라이드 패널 (PC: 왼쪽, 모바일: 하단)
 ┃ ┣ mrv/                  # MRV 관련 컴포넌트
 ┃ ┗ sensor/               # 센서 데이터 컴포넌트
 ┣ data/
 ┃ ┗ regions.ts            # 전라북도 시군 목록
 ┣ hooks/                  # 커스텀 훅
 ┣ pages/
 ┃ ┣ Home.tsx              # 대시보드
 ┃ ┣ MapPage.tsx           # 지도 (메인)
 ┃ ┣ SensorData.tsx        # 센서 데이터
 ┃ ┣ AlertPage.tsx         # 알림
 ┃ ┣ MrvPage.tsx           # MRV 보고서
 ┃ ┗ ValidationPage.tsx    # 검증 사진
 ┣ App.tsx                 # 라우터 + 전역 논/지역 Context
 ┗ vite-env.d.ts
```

---

## 4. 페이지 구성 및 주요 기능

| 페이지 | 경로 | 설명 |
|---|---|---|
| Map | `/map` | 메인 페이지. 전체화면 지도 + 슬라이드 패널 |
| Dashboard | `/dashboard` | 전체 현황 요약 |
| Sensor Data | `/sensor` | 노드별 수위 그래프 및 통계 |
| Alerts | `/alerts` | 수위 이상 알림 목록 및 해결 처리 |
| MRV | `/mrv` | 월별 MRV 보고서 조회 및 다운로드 |
| Validation | `/validations` | 현장 검증 사진 등록 및 AI 분석 |

### 1) Map 페이지 (메인)
- 전체화면 지도 + 슬라이드 패널 (토글 가능)
- V-WORLD WMTS 기반 지도 / 스카이뷰 전환
- 지역 필터링 → 논 선택 → 노드 마커 표시
- 노드 클릭 시 수위·상태 정보 카드 표시
- **PC**: 왼쪽 슬라이드 패널
- **모바일**: 하단에서 위로 올라오는 패널, 패널 열릴 시 지도 축소로 지도+패널 동시 확인 가능

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
- 보고서를 화면에 직접 표출 (1.개요 / 2.주요내용 / 3.결과분석 / 4.결론)
- 주차별 수위 변화 테이블, 현장 검증 결과, 대표 검증 사진 포함
- PDF / Excel 다운로드
- 반응형 레이아웃 (PC / 모바일)

### 6) Validation 페이지
- 현장 테스트 탭: 현장 사진 업로드 및 검증, AI 분석 버튼
- 자동 분석 탭: 검증 기록 목록, 상태·날짜 필터링, 사진 모달 확대 보기

---

## 5. 전역 논/지역 선택 연동

`App.tsx`의 `FieldContext`를 통해 `selectedFieldId`와 `selectedRegion`을 전역으로 관리합니다.  
어느 페이지에서 논 또는 지역을 선택해도 모든 페이지에 즉시 반영되며, 페이지 이동 후에도 선택값이 유지됩니다.  
논 선택 시 해당 논의 `location_desc`를 기반으로 지역도 자동 업데이트됩니다.

---

## 6. 실행 방법

```bash
cd frontend
npm install
npm run dev
```

---

## 7. 환경변수

```env
VITE_VWORLD_KEY=발급받은_V-WORLD_API_키
```

---

## 8. 배포

- Vercel 배포: `feature/happy-frontend-v5` 브랜치 기준 자동 배포
- 배포 URL: https://jeonbuk-mrv.vercel.app