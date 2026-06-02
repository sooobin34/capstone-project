interface Sensor {
  name: string
  status: '정상' | '수위 이상' | '센서 오류'
  level?: number
}

interface SensorStatusCardProps {
  sensors: Sensor[]
  alarmCount: number
}

export default function SensorStatusCard({ sensors, alarmCount }: SensorStatusCardProps) {
  const badgeStyle = (status: Sensor['status']) => {
    const styles = {
      '정상': { background: '#e8f5e9', color: '#2e7d32' },
      '수위 이상': { background: '#fce4ec', color: '#c62828' },
      '센서 오류': { background: '#fff8e1', color: '#f57f17' },
    }
    return styles[status]
  }

  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px', fontWeight: 500 }}>센서 상태</p>
      {sensors.map((sensor, i) => (
        <div key={i} style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 0',
          borderBottom: i < sensors.length - 1 ? '0.5px solid #f0f0f0' : 'none',
          fontSize: '13px',
        }}>
          <span>{sensor.name}</span>
          <span style={{
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '20px',
            fontWeight: 500,
            ...badgeStyle(sensor.status),
          }}>{sensor.status}</span>
        </div>
      ))}
      <div style={{
        marginTop: '10px',
        paddingTop: '8px',
        borderTop: '0.5px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '12px',
        color: '#888',
      }}>
        <span>24시간 내 알람</span>
        <span style={{ fontWeight: 500, color: '#222' }}>{alarmCount}건</span>
      </div>
    </div>
  )
}