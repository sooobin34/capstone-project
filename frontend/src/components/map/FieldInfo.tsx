interface Sensor {
  id: number
  name: string
  status: '정상' | '수위 이상' | '센서 오류'
  level: number
}

interface FieldInfoProps {
  fieldName: string
  currentLevel: number
  sensors: Sensor[]
}

export default function FieldInfo({ fieldName, currentLevel, sensors }: FieldInfoProps) {
  const badgeStyle = (status: Sensor['status']) => {
    const styles = {
      '정상': { background: '#e8f5e9', color: '#2e7d32' },
      '수위 이상': { background: '#fce4ec', color: '#c62828' },
      '센서 오류': { background: '#fff8e1', color: '#f57f17' },
    }
    return styles[status]
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{
        background: 'white',
        border: '0.5px solid #e0e0e0',
        borderRadius: '12px',
        padding: '16px',
      }}>
        <p style={{ fontSize: '12px', color: '#888', marginBottom: '6px', fontWeight: 500 }}>{fieldName} 현재 수위</p>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '8px' }}>
          <span style={{ fontSize: '26px', fontWeight: 500 }}>{currentLevel > 0 ? `+${currentLevel}` : currentLevel}</span>
          <span style={{ fontSize: '13px', color: '#888' }}>cm</span>
        </div>
        <span style={{
          fontSize: '11px',
          padding: '2px 8px',
          borderRadius: '20px',
          background: '#e8f5e9',
          color: '#2e7d32',
          fontWeight: 500,
        }}>담수 정상</span>
      </div>

      <div style={{
        background: 'white',
        border: '0.5px solid #e0e0e0',
        borderRadius: '12px',
        padding: '16px',
      }}>
        <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px', fontWeight: 500 }}>센서 상태</p>
        {sensors.map((sensor, i) => (
          <div key={sensor.id} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 0',
            borderBottom: i < sensors.length - 1 ? '0.5px solid #f0f0f0' : 'none',
          }}>
            <div>
              <p style={{ fontSize: '13px', fontWeight: 500 }}>{sensor.name}</p>
              <p style={{ fontSize: '11px', color: '#888' }}>{sensor.level > 0 ? `+${sensor.level}` : sensor.level}cm</p>
            </div>
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '20px',
              fontWeight: 500,
              ...badgeStyle(sensor.status),
            }}>{sensor.status}</span>
          </div>
        ))}
        <p style={{ fontSize: '12px', color: '#888', marginTop: '10px', paddingTop: '8px', borderTop: '0.5px solid #f0f0f0' }}>마지막 업데이트 2분 전</p>
      </div>
    </div>
  )
}