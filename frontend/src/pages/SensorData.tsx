import { useState, useEffect } from 'react'
import SensorChart from '../components/sensor/SensorChart'
import SensorStats from '../components/sensor/SensorStats'
import { getFields, getNodes, getSensorLogsRange, getSensorStats, getNodeStatus, Field, Node } from '../api/dashboard'
import { useFieldContext } from '../App'

const periodMap: Record<string, '1h' | '1d' | '1w' | '1m'> = {
  '1시간': '1h', '1일': '1d', '1주': '1w', '1개월': '1m',
}
const timeRanges = ['1시간', '1일', '1주', '1개월']

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

export default function SensorData() {
  const { selectedFieldId, setSelectedFieldId, setSelectedRegion } = useFieldContext()
  const [fields, setFields] = useState<Field[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [nodeStatuses, setNodeStatuses] = useState<Record<number, any>>({})
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)
  const [selectedTime, setSelectedTime] = useState('1일')
  const [chartData, setChartData] = useState<number[]>([])
  const [chartLabels, setChartLabels] = useState<string[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [tableLoading, setTableLoading] = useState(false)

  useEffect(() => {
    getFields().then(setFields).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedFieldId) return
    setSelectedNodeId(null)
    setNodeStatuses({})
    setTableLoading(true)
    getNodes(selectedFieldId)
      .then(async (data) => {
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
      })
      .catch(console.error)
      .finally(() => setTableLoading(false))
  }, [selectedFieldId])

  useEffect(() => {
    if (!selectedNodeId) return
    fetchChartData(selectedNodeId, periodMap[selectedTime])
  }, [selectedNodeId, selectedTime])

  const fetchChartData = async (nodeId: number, period: '1h' | '1d' | '1w' | '1m') => {
    try {
      setLoading(true)
      const [logs, statsData] = await Promise.all([
        getSensorLogsRange(nodeId, period),
        getSensorStats(nodeId),
      ])
      setChartData(logs.map((l: any) => l.inner_water_level))
      setChartLabels(logs.map((l: any) => {
        const date = new Date(l.measured_at)
        if (period === '1h' || period === '1d') {
          return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
        } else {
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
      }))
      setStats(statsData)
    } catch (e) {
      console.error('센서 데이터 조회 실패', e)
    } finally {
      setLoading(false)
    }
  }

  // 논 선택 시 지역도 자동 업데이트
  const handleFieldSelect = (fieldId: number | null) => {
    setSelectedFieldId(fieldId)
    setNodes([])
    setChartData([])
    setStats(null)
    if (fieldId) {
      const field = fields.find(f => f.id === fieldId)
      if (field?.location_desc) setSelectedRegion(field.location_desc)
    }
  }

  const singleMode = selectedNodeId !== null
  const datasets = singleMode && chartData.length > 0
    ? [{ nodeId: selectedNodeId, label: `Node ${selectedNodeId}`, data: chartData }]
    : []

  return (
    <div style={{ padding: '16px', maxWidth: '1200px', margin: '0 auto', boxSizing: 'border-box' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '16px' }}>센서 데이터</h2>

      {/* 필터 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={selectedFieldId ?? ''}
          onChange={(e) => handleFieldSelect(e.target.value ? Number(e.target.value) : null)}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer', flex: '1 1 120px' }}
        >
          <option value="">논 선택</option>
          {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
        </select>

        <select
          value={selectedNodeId ?? ''}
          onChange={(e) => setSelectedNodeId(e.target.value ? Number(e.target.value) : null)}
          disabled={!selectedFieldId}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: selectedFieldId ? 'pointer' : 'not-allowed', opacity: selectedFieldId ? 1 : 0.5, flex: '1 1 120px' }}
        >
          <option value="">노드 선택</option>
          {nodes.map((n) => <option key={n.id} value={n.id}>Node {n.id} · {n.location_desc}</option>)}
        </select>

        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {timeRanges.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedTime(t)}
              style={{
                fontSize: '12px', padding: '5px 10px', borderRadius: '20px',
                border: '0.5px solid #ccc', cursor: 'pointer',
                background: selectedTime === t ? '#1D9E75' : 'white',
                color: selectedTime === t ? 'white' : '#888',
                fontWeight: selectedTime === t ? 500 : 400,
                whiteSpace: 'nowrap',
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* 노드별 최신 측정 데이터 테이블 */}
      {selectedFieldId && (
        <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px', overflowX: 'auto' }}>
          <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>노드별 최신 측정 데이터</p>
          {tableLoading ? (
            <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '12px 0' }}>불러오는 중...</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', minWidth: '400px' }}>
              <thead>
                <tr style={{ borderBottom: '0.5px solid #e0e0e0' }}>
                  {['노드', '수위', '배터리', '최근 측정', '상태'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '8px 10px', fontSize: '11px', color: '#888', fontWeight: 500, whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {nodes.map((node) => {
                  const status = nodeStatuses[node.id]
                  const log = status?.latest_log
                  const currentStatus = status?.current_status ?? 'NO_DATA'
                  return (
                    <tr
                      key={node.id}
                      onClick={() => setSelectedNodeId(node.id)}
                      style={{
                        borderBottom: '0.5px solid #f0f0f0',
                        cursor: 'pointer',
                        background: selectedNodeId === node.id ? '#f0faf6' : 'white',
                      }}
                    >
                      <td style={{ padding: '10px', fontWeight: 500, whiteSpace: 'nowrap' }}>Node {node.id}</td>
                      <td style={{ padding: '10px', whiteSpace: 'nowrap' }}>{log ? `${log.inner_water_level}cm` : '-'}</td>
                      <td style={{ padding: '10px', whiteSpace: 'nowrap' }}>{log ? `${log.battery_voltage}V` : '-'}</td>
                      <td style={{ padding: '10px', color: '#888', fontSize: '12px', whiteSpace: 'nowrap' }}>
                        {log ? new Date(log.measured_at).toLocaleString('ko-KR') : '-'}
                      </td>
                      <td style={{ padding: '10px' }}>
                        <span style={{
                          fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
                          background: statusColor(currentStatus) + '20',
                          color: statusColor(currentStatus),
                          whiteSpace: 'nowrap',
                        }}>
                          {statusLabel(currentStatus)}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* 그래프 + 통계 */}
      {!selectedFieldId ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px', background: 'white', borderRadius: '12px', border: '0.5px solid #e0e0e0' }}>
          논을 선택하면 수위 데이터가 표시됩니다
        </div>
      ) : !selectedNodeId ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px', background: 'white', borderRadius: '12px', border: '0.5px solid #e0e0e0' }}>
          노드를 선택하면 그래프가 표시됩니다
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '12px'
        }}>
          <SensorChart datasets={datasets} labels={chartLabels} singleMode={singleMode} />
          {stats && (
            <SensorStats
              currentLevel={chartData[chartData.length - 1] ?? 0}
              sensorStatus="정상"
              avg={stats.avg_inner ?? 0}
              max={stats.max_inner ?? 0}
              min={stats.min_inner ?? 0}
              alarmCount={stats?.alarm_count ?? 0}
            />
          )}
        </div>
      )}
    </div>
  )
}