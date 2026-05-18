## 🖥️ Frontend

### 기술 스택
- **React** + **TypeScript** (Vite)
- **react-router-dom** — 페이지 라우팅
- **Axios** — API 통신
- **Chart.js** / **react-chartjs-2** — 수위 그래프
- **Leaflet** / **react-leaflet** — 지도

---

### 프로젝트 구조
frontend/src/
├── api/
│   ├── axios.ts          # Axios 인스턴스 설정
│   └── dashboard.ts      # API 호출 함수 모음
├── assets/               # 이미지, 로고
├── components/
│   ├── dashboard/        # 대시보드 컴포넌트
│   ├── map/              # 지도 관련 컴포넌트
│   ├── mrv/              # MRV 관련 컴포넌트
│   └── sensor/           # 센서 데이터 컴포넌트
├── data/
│   └── regions.ts        # 전라북도 시군 목록
├── hooks/                # 커스텀 훅
├── pages/
│   ├── Home.tsx          # 대시보드
│   ├── MapPage.tsx       # 지도 (메인)
│   ├── SensorData.tsx    # 센서 데이터
│   ├── AlertPage.tsx     # 알림
│   ├── MrvPage.tsx       # MRV 보고서
│   └── ValidationPage.tsx # 검증 사진
└── styles/
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
- 전체화면 지도 + 왼쪽 슬라이드 패널
- 지도 / 스카이뷰 전환
- 논 추가 (`POST /fields`), 노드 추가 (`POST /nodes`)
- 전라북도 14개 시군 기준 지역 필터링
- 논 선택 시 해당 노드 마커 표시 및 상태 조회

#### Sensor Data 페이지
- 논 → 노드 선택 후 수위 그래프 표시
- 1시간 / 1일 / 1주 / 1개월 기간 선택
- 24시간 평균·최고·최저 통계 카드

#### Alerts 페이지
- 미해결 / 전체 알림 필터
- 논별, 알림 타입별 필터링
- 알림 해결 처리 (`PATCH /alerts/{id}/resolve`)

#### MRV 페이지
- 월별 MRV 보고서 목록 조회
- 논 선택 + 월 선택 후 보고서 생성 (`POST /mrv-reports`)
- PDF / Excel 다운로드

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