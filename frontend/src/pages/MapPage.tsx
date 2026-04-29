import { useState, useEffect } from 'react'
import FieldMap from '../components/map/FieldMap'
import FieldInfo from '../components/map/FieldInfo'
import { getFields, getNodes, getNodeStatus, Field, Node } from '../api/dashboard'

export default function MapPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [nodeStatuses, setNodeStatuses] = useState<Record<number, any>>({})
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getFields()
      .then(data => {
        setFields(data)
        if (data.length > 0) setSelectedFieldId(data[0].id)
      })
      .catch(e => console.error('논 조회 실패', e))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedFieldId) return
    getNodes(selectedFieldId).then(async (data) => {
      setNodes(data)
      // 각 노드 상태 조회
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
    return {
      id: n.id,
      name: `Node ${n.id}`,
      is_active: n.is_active,
      current_status: status?.current_status ?? 'NO_DATA',
      latest_level: status?.latest_log?.inner_water_level ?? null,
    }
  })

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>지도</h2>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : (
        <>
          <select
            value={selectedFieldId ?? ''}
            onChange={(e) => setSelectedFieldId(Number(e.target.value))}
            style={{
              fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
              border: '0.5px solid #ccc', background: 'white', cursor: 'pointer', marginBottom: '16px',
            }}
          >
            {fields.map((f) => (
              <option key={f.id} value={f.id}>{f.field_name}</option>
            ))}
          </select>

          {selectedField && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '12px' }}>
              <FieldMap
                sensors={mapSensors}
                center={[selectedField.latitude, selectedField.longitude]}
              />
              <FieldInfo
                fieldName={selectedField.field_name}
                sensors={fieldInfoSensors}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}