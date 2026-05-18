## 🖥️ Frontend

### 기술 스택
- **React** + **TypeScript** (Vite)
- **react-router-dom** — 페이지 라우팅
- **Axios** — API 통신
- **Chart.js** / **react-chartjs-2** — 수위 그래프
- **Leaflet** / **react-leaflet** — 지도 (OpenStreetMap + Mapbox 위성)

---

### 프로젝트 구조
frontend/src/
├── api/
│   ├── axios.ts              # Axios 인스턴스 설정
│   └── dashboard.ts          # API 호출 함수 모음
├── assets/                   # 이미지, 로고 (AquaPaddy)
├── components/
│   ├── dashboard/            # 대시보드 컴포넌트
│   │   ├── AlarmSummaryCard.tsx
│   │   ├── MrvSummaryCard.tsx
│   │   ├── TrendChart.tsx
│   │   └── WaterLevelCard.tsx
│   ├── map/                  # 지도 관련 컴포넌트
│   │   ├── FieldMap.tsx      # Leaflet 지도
│   │   ├── FieldInfo.tsx     # 노드 상태 패널
│   │   └── MapPanel.tsx      # 왼쪽 슬라이드 패널
│   ├── mrv/                  # MRV 관련 컴포넌트
│   │   └── MrvReportList.tsx
│   └── sensor/               # 센서 데이터 컴포넌트
│       ├── SensorChart.tsx
│       └── SensorStats.tsx
├── data/
│   └── regions.ts            # 전라북도 시군 목록
├── pages/
│   ├── Home.tsx              # 대시보드
│   ├── MapPage.tsx           # 지도 (메인)
│   ├── SensorData.tsx        # 센서 데이터
│   ├── AlertPage.tsx         # 알림
│   ├── MrvPage.tsx           # MRV 보고서
│   └── ValidationPage.tsx    # 검증 사진
└── vite-env.d.ts

---

### 페이지 구성 및 주요 기능

| 페이지 | 경로 | 설명 |
|---|---|---|
| Map | `/map` | 메인 페이지. 전체화면 지도 + 왼쪽 패널 |
| Dashboard | `/dashboard` | 전체 현황 요약 |
| Sensor Data | `/sensor` | 노드별 수위 그래프 및 통계 |
| Alerts | `/alerts` | 수위 이상 알림 목록 및 해결 처리 |
| MRV | `/mrv` | 월별 MRV 보고서 조회 및 다운로드 |
| Validation | `/validation` | 현장 검증 사진 등록 및 AI 분석 |

#### Map 페이지 (메인)
- 전체화면 지도 + 왼쪽 슬라이드 패널 (토글 가능)
- 지도 / 스카이뷰(Mapbox 위성) 전환
- 지역 필터링 → 논 선택 → 노드 마커 표시
- 노드 클릭 시 우측 하단에 수위·상태 정보 카드 표시
- 논 추가(`POST /fields`), 노드 추가(`POST /nodes`) — 현재 UI 주석처리, 코드 유지
- 모바일: 패널 기본 닫힘, 논 선택 시 자동 닫힘

#### Dashboard 페이지
- 3열 그리드 레이아웃 (PC) / 1열 스크롤 (모바일)
- 전체 논·기기 수, 미해결 알람, 최근 측정 시간 요약 카드
- 논/노드 드롭다운 선택 시 현재 수위·그래프·알람·MRV 요약 연동
- 지도 미니맵 (Leaflet)
- 수위 추이 24시간 그래프

#### Sensor Data 페이지
- 논 선택 → 노드별 최신 측정 데이터 테이블 (수위, 배터리, 상태)
- 노드 클릭 시 그래프 표시
- 1시간 / 1일 / 1주 / 1개월 기간 선택
- 24시간 평균·최고·최저 통계 카드

#### Alerts 페이지
- 미해결 알람·24시간 발생·전체 알람 요약 카드
- 노드별 알람 집중도 바 차트
- 논별·알림 타입별 필터링
- 알림 해결 처리 (`PATCH /alerts/{id}/resolve`)

#### MRV 페이지
- 논 선택 + 월 선택 후 보고서 생성 (`POST /mrv-reports`)
- 월별 MRV 보고서 목록 조회 및 정렬
- PDF / Excel 다운로드
- 논 선택 시 AI 일치도 분석 요약 + 최근 검증 사진 슬라이드쇼

#### Validation 페이지
- **현장 테스트 탭**: 현장 사진 업로드 및 검증
  - 논·노드·촬영날짜·촬영시각·관찰상태 필수 입력
  - 촬영 각도, 높이, 빛/방해요소 선택 입력
  - 사진 제목 자동 생성 (상태\_각도\_높이 조합)
  - 최신 LoRa 센서값 카드 (Node 7 기준)
  - AI 분석 버튼 (OpenAI API 키 설정 시 작동)
- **자동 분석 탭**: MRV 보고서 생성 흐름 설명 + 검증 기록 목록
  - 상태·날짜 필터링
  - 사진 클릭 시 모달 확대 보기

---

### 반응형 지원
- PC (768px 이상): 그리드 레이아웃
- 모바일 (768px 이하): 1열 스크롤 레이아웃, 햄버거 메뉴

---

### 실행 방법
```bash
cd frontend
npm install
npm run dev
```

### 환경변수
`.env` 파일 생성 후 아래 내용 추가:
VITE_API_URL=https://capstone-project-54l6.onrender.com

---

### 미해결 / 개선 예정
- 카카오맵 API 연동 (한국어 지도, 구름 없는 스카이뷰)
- 검증 사진 영구 저장 (현재 Render 무료플랜 한계 → S3 등 외부 스토리지 필요)
- AI 분석 기능 (백엔드 OpenAI API 키 설정 필요)
- LoRa 웹훅 API 연동 후 Node 7 센서 데이터 자동 표시
추가로 넣으면 좋을 것들:

스크린샷 (각 페이지 화면 캡처)
배포 URL (Vercel 링크)