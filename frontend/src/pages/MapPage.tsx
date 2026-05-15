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
  const [selectedNode, setSelectedNode] = useState<any>(null)

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
    setSelectedNode(null)
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
    level: nodeStatuses[n.id]?.latest_log?.inner_water_level ?? null,
    status: nodeStatuses[n.id]?.current_status ?? 'NO_DATA',
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

  const statusLabel = (status: string) => {
    const map: Record<string, string> = {
      OVERFLOODED: '과담수', FLOODED: '담수', DRYING: '건조중', DRY: '건조', NO_DATA: '데이터 없음'
    }
    return map[status] ?? status
  }

  const statusColor = (status: string) => {
    const map: Record<string, string> = {
      OVERFLOODED: '#1565c0', FLOODED: '#1D9E75', DRYING: '#BA7517', DRY: '#E24B4A', NO_DATA: '#aaa'
    }
    return map[status] ?? '#aaa'
  }

  return (
    <div style={{ position: 'fixed', top: '48px', left: 0, right: 0, bottom: 0 }}>
      {/* 지도 */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1 }}>
        {selectedField ? (
          <FieldMap
            sensors={mapSensors}
            center={[selectedField.latitude, selectedField.longitude]}
            onNodeClick={setSelectedNode}
            selectedNodeId={selectedNode?.id ?? null}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#aaa', fontSize: '14px' }}>
            논을 선택해주세요
          </div>
        )}
      </div>

      {/* 왼쪽 패널 */}
      <div style={{
        position: 'absolute', top: 0, left: 0, bottom: 0,
        width: isPanelOpen ? '360px' : '0px',
        background: 'white',
        borderRight: isPanelOpen ? '0.5px solid #e0e0e0' : 'none',
        overflowY: 'auto', overflowX: 'hidden',
        transition: 'width 0.3s ease', zIndex: 10,
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
          left: isPanelOpen ? '360px' : '0px',
          top: '50%', transform: 'translateY(-50%)',
          zIndex: 1000, background: 'white',
          border: '0.5px solid #e0e0e0', borderLeft: 'none',
          borderRadius: '0 8px 8px 0', width: '20px', height: '48px',
          cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '14px', color: '#555', transition: 'left 0.3s ease',
          boxShadow: '2px 0 6px rgba(0,0,0,0.15)', padding: 0,
        }}
      >
        {isPanelOpen ? '‹' : '›'}
      </button>

      {/* 노드 클릭 시 우측 하단 정보 카드 */}
      {selectedNode && (
        <div style={{
          position: 'absolute', bottom: '24px', right: '24px',
          zIndex: 1000, background: 'white', borderRadius: '12px',
          border: '0.5px solid #e0e0e0', padding: '16px', minWidth: '220px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <p style={{ fontSize: '14px', fontWeight: 600 }}>Node {selectedNode.id}</p>
            <button
              onClick={() => setSelectedNode(null)}
              style={{ fontSize: '16px', border: 'none', background: 'none', cursor: 'pointer', color: '#aaa', padding: 0 }}
            >✕</button>
          </div>
          <p style={{ fontSize: '11px', color: '#888', marginBottom: '10px' }}>{selectedNode.name}</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div style={{ background: '#f5f5f5', borderRadius: '8px', padding: '8px 12px' }}>
              <p style={{ fontSize: '10px', color: '#888', marginBottom: '2px' }}>수위</p>
              <p style={{ fontSize: '16px', fontWeight: 500 }}>
                {selectedNode.level !== null && selectedNode.level !== undefined
                  ? `${selectedNode.level > 0 ? '+' : ''}${selectedNode.level}cm`
                  : '-'}
              </p>
            </div>
            <div style={{ background: '#f5f5f5', borderRadius: '8px', padding: '8px 12px' }}>
              <p style={{ fontSize: '10px', color: '#888', marginBottom: '2px' }}>상태</p>
              <p style={{ fontSize: '13px', fontWeight: 500, color: statusColor(selectedNode.status ?? 'NO_DATA') }}>
                {statusLabel(selectedNode.status ?? 'NO_DATA')}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}