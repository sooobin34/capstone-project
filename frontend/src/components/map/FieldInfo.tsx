import { mapWaterStatus } from '../../api/dashboard'

interface Sensor {
  id: number
  name: string
  is_active: boolean
  current_status: string
  latest_level: number | null
}

interface FieldInfoProps {
  fieldName: string
  sensors: Sensor[]
}

export default function FieldInfo({ fieldName, sensors }: FieldInfoProps) {
  const statusLabel = (status: string) => {
    if (!status || status === 'NO_DATA') return '데이터 없음'
    if (status === 'FLOODED') return '담수'
    if (status === 'DRYING') return '건조중'
    if (status === 'DRY') return '건조'
    return status
  }

  const badgeStyle = (status: string) => {
    if (status === 'FLOODED') return { background: '#e8f5e9', color: '#2e7d32' }
    if (status === 'DRYING') return { background: '#fff8e1', color: '#f57f17' }
    if (status === 'DRY') return { background: '#fce4ec', color: '#c62828' }
    return { background: '#f5f5f5', color: '#888' }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{
        background: 'white', border: '0.5px solid #e0e0e0',
        borderRadius: '12px', padding: '16px',
      }}>
        <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px', fontWeight: 500 }}>센서 상태 · {fieldName}</p>
        {sensors.length === 0 ? (
          <p style={{ fontSize: '13px', color: '#aaa' }}>센서 없음</p>
        ) : sensors.map((sensor, i) => (
          <div key={sensor.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '8px 0', borderBottom: i < sensors.length - 1 ? '0.5px solid #f0f0f0' : 'none',
          }}>
            <div>
              <p style={{ fontSize: '13px', fontWeight: 500 }}>{sensor.name}</p>
              <p style={{ fontSize: '11px', color: '#888' }}>
                {sensor.latest_level !== null
                  ? `${sensor.latest_level > 0 ? '+' : ''}${sensor.latest_level}cm`
                  : '데이터 없음'}
              </p>
            </div>
            <span style={{
              fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
              ...badgeStyle(sensor.current_status),
            }}>{statusLabel(sensor.current_status)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}