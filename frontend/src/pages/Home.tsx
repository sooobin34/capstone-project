import WaterLevelCard from '../components/dashboard/WaterLevelCard'
import TrendChart from '../components/dashboard/TrendChart'
import MapPreview from '../components/dashboard/MapPreview'
import AlarmSummaryCard from '../components/dashboard/AlarmSummaryCard'
import MrvSummaryCard from '../components/dashboard/MrvSummaryCard'

const mockAlerts = [
  { id: 1, fieldName: '1번 논', nodeId: 1, alertType: 'LOW_WATER' as const, message: '수위 낮음', createdAt: '2026-03-23 10:00' },
  { id: 2, fieldName: '2번 논', nodeId: 2, alertType: 'HIGH_WATER' as const, message: '수위 높음', createdAt: '2026-03-23 09:40' },
]

const mockMrvReport = {
  id: 1,
  fieldName: '1번 논 (전주 A)',
  reportMonth: '2026-03',
  awdCount: 3,
  carbonReduction: 183,
}

const mockLabels = Array.from({ length: 24 }, (_, i) => `${i}시`)
const mockData = [3, 2.8, 2.5, 2.2, 1.8, 1.2, 0.5, -1, -3, -6, -9, -12, -14, -15.2, -14, -11, -7, -4, -1, 1, 2, 2.8, 3.2, 3.2]

interface HomeProps {
  onNavigate: (page: string) => void
}

export default function Home({ onNavigate }: HomeProps) {
  return (
    <div style={{ padding: '16px 24px', maxWidth: '1200px', margin: '0 auto', height: 'calc(100vh - 48px)', display: 'flex', flexDirection: 'column', gap: '12px' }}>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '10px' }}>
        {[
          { label: '전체 논', value: '3개' },
          { label: '전체 기기', value: '5대' },
          { label: '미해결 알람', value: '2건', danger: true },
          { label: '최근 측정', value: '2분 전' },
        ].map((card) => (
          <div key={card.label} style={{
            background: 'white',
            border: '0.5px solid #e0e0e0',
            borderRadius: '10px',
            padding: '10px 16px',
          }}>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{card.label}</p>
            <p style={{ fontSize: '20px', fontWeight: 500, color: card.danger ? '#c62828' : '#222' }}>{card.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', flex: 1, minHeight: 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <WaterLevelCard level={3.2} status="담수" fieldName="1번 논" />
          <MapPreview />
        </div>
        <TrendChart data={mockData} labels={mockLabels} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <AlarmSummaryCard
            totalCount={5}
            unresolvedCount={2}
            recentAlerts={mockAlerts}
          />
          <MrvSummaryCard
            report={mockMrvReport}
            onNavigate={() => onNavigate('MRV')}
          />
        </div>
      </div>

    </div>
  )
}

/* 아래는 대시보드를 메뉴와 분리하기 전
import WaterLevelCard from '../components/dashboard/WaterLevelCard'
import TrendChart from '../components/dashboard/TrendChart'
import MapPreview from '../components/dashboard/MapPreview'
import SensorStatusCard from '../components/dashboard/SensorStatusCard'
import AlarmSummaryCard from '../components/dashboard/AlarmSummaryCard'
import MrvSummaryCard from '../components/dashboard/MrvSummaryCard'

const mockAlerts = [
  { id: 1, fieldName: '1번 논', nodeId: 1, alertType: 'LOW_WATER' as const, message: '수위 낮음', createdAt: '2026-03-23 10:00' },
  { id: 2, fieldName: '2번 논', nodeId: 2, alertType: 'HIGH_WATER' as const, message: '수위 높음', createdAt: '2026-03-23 09:40' },
]

const mockMrvReport = {
  id: 1,
  fieldName: '1번 논 (전주 A)',
  reportMonth: '2026-03',
  awdCount: 3,
  carbonReduction: 183,
}

const mockLabels = Array.from({ length: 24 }, (_, i) => `${i}시`)
const mockData = [3, 2.8, 2.5, 2.2, 1.8, 1.2, 0.5, -1, -3, -6, -9, -12, -14, -15.2, -14, -11, -7, -4, -1, 1, 2, 2.8, 3.2, 3.2]

const mockSensors = [
  { name: '1번 논 · 센서 A', status: '정상' as const },
  { name: '2번 논 · 센서 B', status: '수위 이상' as const },
  { name: '3번 논 · 센서 C', status: '센서 오류' as const },
]

interface HomeProps {
  onNavigate: (page: string) => void
}

export default function Home({ onNavigate }: HomeProps) {
  return (
    <div style={{ padding: '24px', maxWidth: '960px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>대시보드</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '12px', marginBottom: '12px' }}>
        {[
          { label: '전체 논', value: '3개' },
          { label: '전체 기기', value: '5대' },
          { label: '미해결 알람', value: '2건', danger: true },
          { label: '최근 측정', value: '2분 전' },
        ].map((card) => (
          <div key={card.label} style={{
            background: '#f5f5f5',
            borderRadius: '8px',
            padding: '12px 16px',
          }}>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{card.label}</p>
            <p style={{ fontSize: '20px', fontWeight: 500, color: card.danger ? '#c62828' : '#222' }}>{card.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <WaterLevelCard level={3.2} status="담수" fieldName="1번 논" />
        <TrendChart data={mockData} labels={mockLabels} />
        <AlarmSummaryCard
          totalCount={5}
          unresolvedCount={2}
          recentAlerts={mockAlerts}
        />
        <MrvSummaryCard
          report={mockMrvReport}
          onNavigate={() => onNavigate('MRV')}
        />
        <MapPreview />
        <SensorStatusCard sensors={mockSensors} alarmCount={2} />
      </div>
    </div>
  )
}
*/