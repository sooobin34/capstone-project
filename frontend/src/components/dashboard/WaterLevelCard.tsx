interface WaterLevelCardProps {
  level: number
  status: '담수' | '습윤' | '건조'
  fieldName: string
}

export default function WaterLevelCard({ level, status, fieldName }: WaterLevelCardProps) {
  const statusColor = {
    담수: '#1D9E75',
    습윤: '#BA7517',
    건조: '#E24B4A',
  }

  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>현재 수위 · {fieldName}</p>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span style={{ fontSize: '28px', fontWeight: 500 }}>{level > 0 ? `+${level}` : level}</span>
        <span style={{ fontSize: '13px', color: '#888' }}>cm</span>
      </div>
      <span style={{
        display: 'inline-block',
        marginTop: '8px',
        fontSize: '11px',
        padding: '2px 8px',
        borderRadius: '20px',
        background: statusColor[status] + '20',
        color: statusColor[status],
        fontWeight: 500,
      }}>{status}</span>
    </div>
  )
}