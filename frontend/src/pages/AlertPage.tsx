import { useState, useEffect } from 'react'
import { getAlerts, getFields, resolveAlert, Alert, Field } from '../api/dashboard'

export default function AlertPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [fields, setFields] = useState<Field[]>([])
  const [loading, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [selectedType, setSelectedType] = useState('')

  useEffect(() => {
    fetchFields()
    fetchAlerts()
  }, [])

  useEffect(() => {
    fetchAlerts(selectedFieldId ?? undefined)
  }, [selectedFieldId])

  const fetchFields = async () => {
    try {
      const data = await getFields()
      setFields(data)
    } catch (e) {
      console.error('논 조회 실패', e)
    }
  }

  const fetchAlerts = async (fieldId?: number) => {
    try {
      setLoading(true)
      const data = await getAlerts(fieldId)
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

  const now = new Date()
  const last24h = alerts.filter(a => (now.getTime() - new Date(a.created_at).getTime()) < 24 * 60 * 60 * 1000)
  const unresolvedAlerts = alerts.filter(a => !a.is_resolved)

  const nodeAlertCount: Record<number, number> = {}
  last24h.forEach(a => {
    nodeAlertCount[a.node_id] = (nodeAlertCount[a.node_id] ?? 0) + 1
  })
  const maxCount = Math.max(...Object.values(nodeAlertCount), 1)

  const filtered = alerts
    .filter((a) => showAll ? true : !a.is_resolved)
    .filter((a) => selectedType ? a.alert_type === selectedType : true)

  const grouped = filtered.reduce<Record<number, Alert[]>>((acc, alert) => {
    if (!acc[alert.node_id]) acc[alert.node_id] = []
    acc[alert.node_id].push(alert)
    return acc
  }, {})

  return (
    <div style={{ padding: '16px', maxWidth: '1200px', margin: '0 auto', boxSizing: 'border-box' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '16px' }}>알람</h2>

      {/* 요약 카드 - 모바일: 1열, PC: 3열 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '10px', marginBottom: '16px'
      }}>
        {[
          { label: '미해결 알람', value: `${unresolvedAlerts.length}건`, danger: unresolvedAlerts.length > 0 },
          { label: '24시간 내 발생', value: `${last24h.length}건`, danger: false },
          { label: '전체 알람', value: `${alerts.length}건`, danger: false },
        ].map((card) => (
          <div key={card.label} style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '10px', padding: '12px 16px' }}>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{card.label}</p>
            <p style={{ fontSize: '20px', fontWeight: 500, color: card.danger ? '#c62828' : '#222' }}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* 노드별 알람 집중도 */}
      {Object.keys(nodeAlertCount).length > 0 && (
        <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
          <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>노드별 알람 집중도 (24시간)</p>
          {Object.entries(nodeAlertCount).map(([nodeId, count]) => (
            <div key={nodeId} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: '#555', width: '60px', flexShrink: 0 }}>Node {nodeId}</span>
              <div style={{ flex: 1, background: '#f5f5f5', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
                <div style={{ width: `${(count / maxCount) * 100}%`, background: '#1D9E75', height: '100%', borderRadius: '4px' }} />
              </div>
              <span style={{ fontSize: '12px', color: '#888', width: '30px', textAlign: 'right', flexShrink: 0 }}>{count}건</span>
            </div>
          ))}
        </div>
      )}

      {/* 필터 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={selectedFieldId ?? ''}
          onChange={(e) => setSelectedFieldId(e.target.value ? Number(e.target.value) : null)}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer', flex: '1 1 120px' }}
        >
          <option value="">논 선택</option>
          {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
        </select>

        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer', flex: '1 1 120px' }}
        >
          <option value="">알람 타입</option>
          <option value="LOW_WATER">재관개 필요</option>
          <option value="HIGH_WATER">수위 높음</option>
        </select>

        <button
          onClick={() => setShowAll(!showAll)}
          style={{
            fontSize: '12px', padding: '6px 14px', borderRadius: '20px',
            border: '0.5px solid #ccc', background: showAll ? '#f0f0f0' : 'white',
            cursor: 'pointer', fontWeight: showAll ? 500 : 400, whiteSpace: 'nowrap',
          }}
        >
          {showAll ? '미해결만 보기' : '전체 알람 보기'}
        </button>
      </div>

      {/* 알람 목록 */}
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
                padding: '12px 14px', marginBottom: '8px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px',
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', flexWrap: 'wrap' }}>
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
                  <p style={{ fontSize: '12px', color: '#888', marginBottom: '2px', wordBreak: 'break-word' }}>{alert.message}</p>
                  <p style={{ fontSize: '12px', color: '#888' }}>{new Date(alert.created_at).toLocaleString('ko-KR')}</p>
                </div>
                {!alert.is_resolved && (
                  <button
                    onClick={() => handleResolve(alert.id)}
                    style={{
                      fontSize: '12px', padding: '6px 12px', borderRadius: '8px',
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