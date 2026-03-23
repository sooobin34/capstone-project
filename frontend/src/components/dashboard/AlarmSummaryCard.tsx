interface Alert {
  id: number
  fieldName: string
  nodeId: number
  alertType: 'LOW_WATER' | 'HIGH_WATER'
  message: string
  createdAt: string
}

interface AlarmSummaryCardProps {
  totalCount: number
  unresolvedCount: number
  recentAlerts: Alert[]
}

export default function AlarmSummaryCard({ totalCount, unresolvedCount, recentAlerts }: AlarmSummaryCardProps) {
  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px', fontWeight: 500 }}>알람 요약</p>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
        <div style={{ background: '#f5f5f5', borderRadius: '8px', padding: '10px 14px', flex: 1 }}>
          <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>전체 알람</p>
          <p style={{ fontSize: '20px', fontWeight: 500 }}>{totalCount}건</p>
        </div>
        <div style={{
          background: unresolvedCount > 0 ? '#fce4ec' : '#e8f5e9',
          borderRadius: '8px',
          padding: '10px 14px',
          flex: 1,
        }}>
          <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>미해결</p>
          <p style={{ fontSize: '20px', fontWeight: 500, color: unresolvedCount > 0 ? '#c62828' : '#2e7d32' }}>{unresolvedCount}건</p>
        </div>
      </div>
      {recentAlerts.length === 0 ? (
        <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '8px 0' }}>현재 알람 없음</p>
      ) : (
        recentAlerts.slice(0, 3).map((alert) => (
          <div key={alert.id} style={{
            padding: '8px 0',
            borderTop: '0.5px solid #f0f0f0',
            fontSize: '12px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
              <span style={{ fontWeight: 500 }}>{alert.fieldName} · Node {alert.nodeId}</span>
              <span style={{
                fontSize: '11px',
                padding: '1px 6px',
                borderRadius: '20px',
                background: alert.alertType === 'LOW_WATER' ? '#fce4ec' : '#fff8e1',
                color: alert.alertType === 'LOW_WATER' ? '#c62828' : '#f57f17',
              }}>{alert.alertType === 'LOW_WATER' ? '재관개 필요' : '수위 높음'}</span>
            </div>
            <p style={{ color: '#888' }}>{alert.createdAt}</p>
          </div>
        ))
      )}
    </div>
  )
}