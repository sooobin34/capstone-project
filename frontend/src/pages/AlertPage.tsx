import { useState, useEffect } from 'react'
import { getAlerts, resolveAlert, Alert } from '../api/dashboard'

export default function AlertPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)
  const [selectedType, setSelectedType] = useState('')

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      const data = await getAlerts()
      setAlerts(data)
    } catch (e) {
      console.error('알람 조회 실패', e)
    } finally {
      setLoading(false)
    }
  }

  const handleResolve = async (id: number) => {
    try {
      await resolveAlert(id)
      setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, is_resolved: true } : a))
    } catch (e) {
      console.error('알람 해결 실패', e)
    }
  }

  const filtered = alerts
    .filter((a) => showAll ? true : !a.is_resolved)
    .filter((a) => selectedType ? a.alert_type === selectedType : true)

  const grouped = filtered.reduce<Record<number, Alert[]>>((acc, alert) => {
    if (!acc[alert.node_id]) acc[alert.node_id] = []
    acc[alert.node_id].push(alert)
    return acc
  }, {})

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>알람</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
        >
          <option value="">알람 타입</option>
          <option value="LOW_WATER">LOW_WATER</option>
          <option value="HIGH_WATER">HIGH_WATER</option>
        </select>
        <button
          onClick={() => setShowAll(!showAll)}
          style={{
            fontSize: '12px', padding: '6px 14px', borderRadius: '20px',
            border: '0.5px solid #ccc', background: showAll ? '#f0f0f0' : 'white',
            cursor: 'pointer', marginLeft: 'auto', fontWeight: showAll ? 500 : 400,
          }}
        >
          {showAll ? '미해결만 보기' : '전체 알람 보기'}
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : Object.keys(grouped).length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>현재 알람 없음</div>
      ) : (
        Object.entries(grouped).map(([nodeId, nodeAlerts]) => (
          <div key={nodeId} style={{ marginBottom: '16px' }}>
            <p style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px', color: '#555' }}>Node {nodeId}</p>
            {nodeAlerts.map((alert) => (
              <div key={alert.id} style={{
                background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px',
                padding: '14px 16px', marginBottom: '8px', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 500 }}>Node {alert.node_id}</span>
                    <span style={{
                      fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
                      background: alert.alert_type === 'LOW_WATER' ? '#fce4ec' : '#fff8e1',
                      color: alert.alert_type === 'LOW_WATER' ? '#c62828' : '#f57f17',
                    }}>
                      {alert.alert_type === 'LOW_WATER' ? '재관개 필요' : '수위 높음'}
                    </span>
                    {alert.is_resolved && (
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '20px', background: '#e8f5e9', color: '#2e7d32', fontWeight: 500 }}>해결됨</span>
                    )}
                  </div>
                  <p style={{ fontSize: '12px', color: '#888', marginBottom: '2px' }}>{alert.message}</p>
                  <p style={{ fontSize: '12px', color: '#888' }}>{new Date(alert.created_at).toLocaleString('ko-KR')}</p>
                </div>
                {!alert.is_resolved && (
                  <button
                    onClick={() => handleResolve(alert.id)}
                    style={{
                      fontSize: '12px', padding: '6px 14px', borderRadius: '8px',
                      border: '0.5px solid #1D9E75', background: 'white',
                      color: '#1D9E75', cursor: 'pointer', flexShrink: 0,
                    }}
                  >
                    해결
                  </button>
                )}
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  )
}

/* 아래는 api 연결 전까지
import { useState } from 'react'

interface Alert {
  id: number
  fieldName: string
  nodeId: number
  alertType: 'LOW_WATER' | 'HIGH_WATER'
  message: string
  innerLevel: number
  createdAt: string
  isResolved: boolean
}

const mockAlerts: Alert[] = [
  { id: 1, fieldName: '1번 논', nodeId: 1, alertType: 'LOW_WATER', message: '수위가 임계치 이하로 떨어졌습니다', innerLevel: -17.2, createdAt: '2026-03-23 10:00', isResolved: false },
  { id: 2, fieldName: '1번 논', nodeId: 2, alertType: 'HIGH_WATER', message: '수위가 너무 높습니다', innerLevel: 6.3, createdAt: '2026-03-23 09:40', isResolved: false },
  { id: 3, fieldName: '2번 논', nodeId: 3, alertType: 'LOW_WATER', message: '수위가 임계치 이하로 떨어졌습니다', innerLevel: -15.8, createdAt: '2026-03-22 14:20', isResolved: false },
]

export default function AlertPage() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts)
  const [showAll, setShowAll] = useState(false)
  const [selectedField, setSelectedField] = useState('')
  const [selectedType, setSelectedType] = useState('')

  const handleResolve = (id: number) => {
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, isResolved: true } : a))
  }

  const filtered = alerts
    .filter((a) => showAll ? true : !a.isResolved)
    .filter((a) => selectedField ? a.fieldName === selectedField : true)
    .filter((a) => selectedType ? a.alertType === selectedType : true)

  const grouped = filtered.reduce<Record<string, Alert[]>>((acc, alert) => {
    if (!acc[alert.fieldName]) acc[alert.fieldName] = []
    acc[alert.fieldName].push(alert)
    return acc
  }, {})

  const fields = [...new Set(mockAlerts.map((a) => a.fieldName))]

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>알람</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={selectedField}
          onChange={(e) => setSelectedField(e.target.value)}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
        >
          <option value="">논 선택</option>
          {fields.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
        >
          <option value="">알람 타입</option>
          <option value="LOW_WATER">LOW_WATER</option>
          <option value="HIGH_WATER">HIGH_WATER</option>
        </select>
        <button
          onClick={() => setShowAll(!showAll)}
          style={{
            fontSize: '12px',
            padding: '6px 14px',
            borderRadius: '20px',
            border: '0.5px solid #ccc',
            background: showAll ? '#f0f0f0' : 'white',
            cursor: 'pointer',
            marginLeft: 'auto',
            fontWeight: showAll ? 500 : 400,
          }}
        >
          {showAll ? '미해결만 보기' : '전체 알람 보기'}
        </button>
      </div>

      {Object.keys(grouped).length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>
          현재 알람 없음
        </div>
      ) : (
        Object.entries(grouped).map(([fieldName, fieldAlerts]) => (
          <div key={fieldName} style={{ marginBottom: '16px' }}>
            <p style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px', color: '#555' }}>{fieldName}</p>
            {fieldAlerts.map((alert) => (
              <div key={alert.id} style={{
                background: 'white',
                border: '0.5px solid #e0e0e0',
                borderRadius: '12px',
                padding: '14px 16px',
                marginBottom: '8px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 500 }}>Node {alert.nodeId}</span>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '20px',
                      fontWeight: 500,
                      background: alert.alertType === 'LOW_WATER' ? '#fce4ec' : '#fff8e1',
                      color: alert.alertType === 'LOW_WATER' ? '#c62828' : '#f57f17',
                    }}>
                      {alert.alertType === 'LOW_WATER' ? '🔴 재관개 필요' : '🟡 수위 높음'}
                    </span>
                    {alert.isResolved && (
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '20px', background: '#e8f5e9', color: '#2e7d32', fontWeight: 500 }}>해결됨</span>
                    )}
                  </div>
                  <p style={{ fontSize: '12px', color: '#888', marginBottom: '2px' }}>{alert.message}</p>
                  <p style={{ fontSize: '12px', color: '#888' }}>
                    내부 수위: {alert.innerLevel}cm · {alert.createdAt}
                  </p>
                </div>
                {!alert.isResolved && (
                  <button
                    onClick={() => handleResolve(alert.id)}
                    style={{
                      fontSize: '12px',
                      padding: '6px 14px',
                      borderRadius: '8px',
                      border: '0.5px solid #1D9E75',
                      background: 'white',
                      color: '#1D9E75',
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                  >
                    해결
                  </button>
                )}
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  )
}
*/