import WaterLevelCard from '../components/dashboard/WaterLevelCard'
import TrendChart from '../components/dashboard/TrendChart'
import MapPreview from '../components/dashboard/MapPreview'
import SensorStatusCard from '../components/dashboard/SensorStatusCard'

const mockSensors = [
  { name: '1번 논 · 센서 A', status: '정상' as const },
  { name: '2번 논 · 센서 B', status: '수위 이상' as const, level: -16 },
  { name: '3번 논 · 센서 C', status: '센서 오류' as const },
]

const mockLabels = Array.from({ length: 24 }, (_, i) => `${i}시`)
const mockData = [3, 2.8, 2.5, 2.2, 1.8, 1.2, 0.5, -1, -3, -6, -9, -12, -14, -15.2, -14, -11, -7, -4, -1, 1, 2, 2.8, 3.2, 3.2]

export default function Home() {
  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>대시보드</h2>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
      }}>
        <WaterLevelCard level={3.2} status="담수" fieldName="1번 논" />
        <TrendChart data={mockData} labels={mockLabels} />
        <MapPreview />
        <SensorStatusCard sensors={mockSensors} alarmCount={3} />
      </div>
    </div>
  )
}