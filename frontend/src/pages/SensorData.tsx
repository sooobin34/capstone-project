import { useState, useEffect } from 'react'
import SensorChart from '../components/sensor/SensorChart'
import SensorStats from '../components/sensor/SensorStats'
import { getFields, getNodes, getSensorLogsRange, getSensorStats, Field, Node } from '../api/dashboard'

const periodMap: Record<string, '1h' | '1d' | '1w' | '1m'> = {
  '1시간': '1h', '1일': '1d', '1주': '1w', '1개월': '1m',
}
const timeRanges = ['1시간', '1일', '1주', '1개월']

export default function SensorData() {
  const [fields, setFields] = useState<Field[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)
  const [selectedTime, setSelectedTime] = useState('1일')
  const [chartData, setChartData] = useState<number[]>([])
  const [chartLabels, setChartLabels] = useState<string[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // 논 목록 로드
  useEffect(() => {
    getFields().then(setFields).catch(console.error)
  }, [])

  // 논 선택 시 노드 목록 로드
  useEffect(() => {
    if (!selectedFieldId) return
    setSelectedNodeId(null)
    getNodes(selectedFieldId).then(setNodes).catch(console.error)
  }, [selectedFieldId])

  // 노드 + 기간 선택 시 그래프 데이터 로드
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

  const singleMode = selectedNodeId !== null
  const datasets = singleMode && chartData.length > 0
    ? [{ nodeId: selectedNodeId, label: `Node ${selectedNodeId}`, data: chartData }]
    : []

  return (
    <div style={{ padding: '24px', maxWidth: '960px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>센서 데이터</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={selectedFieldId ?? ''}
          onChange={(e) => {
            setSelectedFieldId(e.target.value ? Number(e.target.value) : null)
            setNodes([])
            setChartData([])
            setStats(null)
          }}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
        >
          <option value="">논 선택</option>
          {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
        </select>

        <select
          value={selectedNodeId ?? ''}
          onChange={(e) => setSelectedNodeId(e.target.value ? Number(e.target.value) : null)}
          disabled={!selectedFieldId}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: selectedFieldId ? 'pointer' : 'not-allowed', opacity: selectedFieldId ? 1 : 0.5 }}
        >
          <option value="">노드 선택</option>
          {nodes.map((n) => <option key={n.id} value={n.id}>Node {n.id} · {n.location_desc}</option>)}
        </select>

        <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
          {timeRanges.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedTime(t)}
              style={{
                fontSize: '12px', padding: '5px 12px', borderRadius: '20px',
                border: '0.5px solid #ccc', cursor: 'pointer',
                background: selectedTime === t ? '#1D9E75' : 'white',
                color: selectedTime === t ? 'white' : '#888',
                fontWeight: selectedTime === t ? 500 : 400,
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {!selectedFieldId ? (
        <div style={{ textAlign: 'center', padding: '80px', color: '#aaa', fontSize: '14px', background: 'white', borderRadius: '12px', border: '0.5px solid #e0e0e0' }}>
          논을 선택하면 수위 데이터가 표시됩니다
        </div>
      ) : !selectedNodeId ? (
        <div style={{ textAlign: 'center', padding: '80px', color: '#aaa', fontSize: '14px', background: 'white', borderRadius: '12px', border: '0.5px solid #e0e0e0' }}>
          노드를 선택하면 그래프가 표시됩니다
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '80px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '12px' }}>
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