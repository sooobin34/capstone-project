import { useState, useEffect, useCallback } from 'react'
import FieldMap from '../components/map/FieldMap'
import MapPanel from '../components/map/MapPanel'
import { getFields, getNodes, getNodeStatus, Field, Node } from '../api/dashboard'

export default function MapPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [nodeStatuses, setNodeStatuses] = useState<Record<number, any>>({})
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [isPanelOpen, setIsPanelOpen] = useState(true)

  const fetchFields = useCallback(() => {
    setLoading(true)
    getFields()
      .then(data => {
        setFields(data)
        if (data.length > 0 && !selectedFieldId) setSelectedFieldId(data[0].id)
      })
      .catch(e => console.error('논 조회 실패', e))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchFields()
  }, [fetchFields])

  useEffect(() => {
    if (!selectedFieldId) return
    getNodes(selectedFieldId).then(async (data) => {
      setNodes(data)
      const statuses: Record<number, any> = {}
      await Promise.all(data.map(async (node) => {
        try {
          const status = await getNodeStatus(node.id)
          statuses[node.id] = status
        } catch {
          statuses[node.id] = null
        }
      }))
      setNodeStatuses(statuses)
    }).catch(e => console.error('기기 조회 실패', e))
  }, [selectedFieldId])

  const selectedField = fields.find((f) => f.id === selectedFieldId)

  const mapSensors = nodes.map((n) => ({
    id: n.id,
    lat: n.latitude,
    lng: n.longitude,
    name: `Node ${n.id} · ${n.location_desc}`,
  }))

  const fieldInfoSensors = nodes.map((n) => {
    const status = nodeStatuses[n.id]
    const currentStatus = status?.current_status ?? 'NO_DATA'
    return {
      id: n.id,
      name: `Node ${n.id}`,
      is_active: n.is_active,
      current_status: currentStatus,
      latest_level: status?.latest_log?.inner_water_level ?? null,
    }
  })

  return (
    <div style={{
      position: 'fixed',
      top: '60px',
      left: 0,
      right: 0,
      bottom: 0,
    }}>
      {/* 지도 — 항상 전체 화면 */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1 }}>
        {selectedField ? (
          <FieldMap
            sensors={mapSensors}
            center={[selectedField.latitude, selectedField.longitude]}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#aaa', fontSize: '14px' }}>
            논을 선택해주세요
          </div>
        )}
      </div>

      {/* 왼쪽 패널 — 지도 위에 띄움 */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        bottom: 0,
        width: isPanelOpen ? '380px' : '0px',
        background: 'white',
        borderRight: isPanelOpen ? '0.5px solid #e0e0e0' : 'none',
        overflowY: 'auto',
        overflowX: 'hidden',
        transition: 'width 0.3s ease',
        zIndex: 10,
        boxShadow: isPanelOpen ? '2px 0 8px rgba(0,0,0,0.1)' : 'none',
      }}>
        {isPanelOpen && (
          <MapPanel
            fields={fields}
            selectedFieldId={selectedFieldId}
            onFieldSelect={setSelectedFieldId}
            onFieldsRefresh={fetchFields}
            sensors={fieldInfoSensors}
            fieldName={selectedField?.field_name ?? ''}
            loading={loading}
          />
        )}
      </div>

      {/* 토글 버튼 */}
      <button
        onClick={() => setIsPanelOpen(!isPanelOpen)}
        style={{
          position: 'absolute',
          left: isPanelOpen ? '380px' : '0px',
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 1000,
          background: 'white',
          border: '0.5px solid #e0e0e0',
          borderLeft: 'none',
          borderRadius: '0 8px 8px 0',
          width: '20px',
          height: '48px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          color: '#555',
          transition: 'left 0.3s ease',
          boxShadow: '2px 0 6px rgba(0,0,0,0.15)',
          padding: 0,
        }}
      >
        {isPanelOpen ? '‹' : '›'}
      </button>
    </div>
  )
}