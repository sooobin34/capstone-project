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
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)

  const BOTTOM_PANEL_HEIGHT = 350  // 패널 높이 (화면의 약 절반)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const fetchFields = useCallback(() => {
    setLoading(true)
    getFields()
      .then(data => {
        setFields(data)
        setIsPanelOpen(window.innerWidth > 768)
      })
      .catch(e => console.error('논 조회 실패', e))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchFields()
  }, [fetchFields])

  useEffect(() => {
    setSelectedNode(null)
    getNodes(selectedFieldId ?? undefined).then(async (data) => {
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
      {/* 지도 - 모바일에서 패널이 열리면 위쪽으로 올라가도록 bottom 조정 */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        bottom: isMobile && isPanelOpen ? `${BOTTOM_PANEL_HEIGHT}px` : 0,
        zIndex: 1,
        transition: 'bottom 0.3s ease',
      }}>
        <FieldMap
          sensors={mapSensors}
          center={selectedField
            ? [selectedField.latitude, selectedField.longitude]
            : [35.8468, 127.1294]
          }
          onNodeClick={(node) => {
            setSelectedNode(node)
          }}
          selectedNodeId={selectedNode?.id ?? null}
        />
      </div>

      {/* PC: 왼쪽 패널 */}
      {!isMobile && (
        <>
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
          <button
            onClick={() => setIsPanelOpen(!isPanelOpen)}
            style={{
              position: 'absolute',
              left: isPanelOpen ? '360px' : '0px',
              top: '50%', transform: 'translateY(-50%)',
              zIndex: 1000, background: 'white',
              border: '0.5px solid #e0e0e0', borderLeft: 'none',
              borderRadius: '0 8px 8px 0', width: '24px', height: '48px',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '14px', color: '#555', transition: 'left 0.3s ease',
              boxShadow: '2px 0 6px rgba(0,0,0,0.15)', padding: 0,
            }}
          >
            {isPanelOpen ? '‹' : '›'}
          </button>
        </>
      )}

      {/* 모바일: 하단에서 올라오는 패널 */}
      {isMobile && (
        <>
          {/* 드래그 핸들 겸 토글 버튼 */}
          <button
            onClick={() => setIsPanelOpen(!isPanelOpen)}
            style={{
              position: 'absolute',
              bottom: isPanelOpen ? `${BOTTOM_PANEL_HEIGHT}px` : '0px',
              left: '50%', transform: 'translateX(-50%)',
              zIndex: 1000, background: 'white',
              border: '0.5px solid #e0e0e0', borderBottom: 'none',
              borderRadius: '8px 8px 0 0', width: '60px', height: '24px',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '12px', color: '#555', transition: 'bottom 0.3s ease',
              boxShadow: '0 -2px 6px rgba(0,0,0,0.1)', padding: 0,
            }}
          >
            {isPanelOpen ? '∨' : '∧'}
          </button>

          {/* 하단 슬라이드 패널 */}
          <div style={{
            position: 'absolute',
            bottom: 0, left: 0, right: 0,
            height: isPanelOpen ? `${BOTTOM_PANEL_HEIGHT}px` : '0px',
            background: 'white',
            borderTop: '0.5px solid #e0e0e0',
            overflowY: 'auto',
            overflowX: 'hidden',
            transition: 'height 0.3s ease',
            zIndex: 10,
            boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
          }}>
            <MapPanel
              fields={fields}
              selectedFieldId={selectedFieldId}
              onFieldSelect={(id) => {
                setSelectedFieldId(id)
                setIsPanelOpen(false)
              }}
              onFieldsRefresh={fetchFields}
              sensors={fieldInfoSensors}
              fieldName={selectedField?.field_name ?? ''}
              loading={loading}
            />
          </div>
        </>
      )}

      {/* 노드 클릭 시 정보 카드 */}
      {selectedNode && (
        <div style={{
          position: 'absolute',
          bottom: isMobile ? (isPanelOpen ? `${BOTTOM_PANEL_HEIGHT + 8}px` : '36px') : '24px',
          right: isMobile ? '8px' : '24px',
          zIndex: 1000, background: 'white',
          borderRadius: '12px',
          border: '0.5px solid #e0e0e0', padding: '16px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
          minWidth: '200px',
          transition: 'bottom 0.3s ease',
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