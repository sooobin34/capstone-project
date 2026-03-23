interface SensorStatsProps {
  currentLevel: number
  sensorStatus: '정상' | '수위 이상' | '센서 오류'
  avg: number
  max: number
  min: number
  alarmCount: number
}

export default function SensorStats({
  currentLevel,
  sensorStatus,
  avg,
  max,
  min,
  alarmCount,
}: SensorStatsProps) {
  const badgeStyle = (status: SensorStatsProps['sensorStatus']) => {
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
        <p style={{ fontSize: '11px', color: '#888', fontWeight: 500, marginBottom: '8px' }}>현재 상태</p>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '6px' }}>
          <span style={{ fontSize: '26px', fontWeight: 500 }}>{currentLevel > 0 ? `+${currentLevel}` : currentLevel}</span>
          <span style={{ fontSize: '13px', color: '#888' }}>cm</span>
        </div>
        <p style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>업데이트 2분 전</p>
        <span style={{
          fontSize: '11px',
          padding: '3px 9px',
          borderRadius: '20px',
          fontWeight: 500,
          ...badgeStyle(sensorStatus),
        }}>{sensorStatus}</span>
      </div>

      <div style={{
        background: 'white',
        border: '0.5px solid #e0e0e0',
        borderRadius: '12px',
        padding: '16px',
      }}>
        <p style={{ fontSize: '11px', color: '#888', fontWeight: 500, marginBottom: '10px' }}>24시간 통계</p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {[
            { label: '평균', value: avg, unit: 'cm' },
            { label: '최고', value: max, unit: 'cm' },
            { label: '최저', value: min, unit: 'cm', danger: min <= -15 },
            { label: '알람', value: alarmCount, unit: '건' },
          ].map((item) => (
            <div key={item.label} style={{
              background: '#f5f5f5',
              borderRadius: '8px',
              padding: '10px 12px',
            }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
              <span style={{
                fontSize: '18px',
                fontWeight: 500,
                color: item.danger ? '#E24B4A' : '#222',
              }}>
                {item.value > 0 && item.unit === 'cm' ? `+${item.value}` : item.value}
                <small style={{ fontSize: '12px', fontWeight: 400, color: '#888', marginLeft: '2px' }}>{item.unit}</small>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}