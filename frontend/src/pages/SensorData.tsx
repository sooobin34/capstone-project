import { useState } from 'react'
import SensorChart from '../components/sensor/SensorChart'
import SensorStats from '../components/sensor/SensorStats'

const mockFields = [
  { id: 1, name: '1번 논 (전주 A)' },
  { id: 2, name: '2번 논 (전주 B)' },
  { id: 3, name: '3번 논 (전주 C)' },
]

const mockNodes: Record<number, { id: number; label: string }[]> = {
  1: [{ id: 1, label: 'Node 1' }, { id: 2, label: 'Node 2' }, { id: 3, label: 'Node 3' }],
  2: [{ id: 4, label: 'Node 4' }, { id: 5, label: 'Node 5' }],
  3: [{ id: 6, label: 'Node 6' }],
}

const mockData = [3, 2.8, 2.5, 2.2, 1.8, 1.2, 0.5, -1, -3, -6, -9, -12, -14, -15.2, -14, -11, -7, -4, -1, 1, 2, 2.8, 3.2, 3.2]
const mockLabels = Array.from({ length: 24 }, (_, i) => `${i}시`)

const timeRanges = ['1시간', '1일', '1주', '1개월']

export default function SensorData() {
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)
  const [selectedTime, setSelectedTime] = useState('1일')

  const nodes = selectedFieldId ? mockNodes[selectedFieldId] ?? [] : []
  const singleMode = selectedNodeId !== null

  const datasets = !selectedFieldId
  ? []
  : singleMode
    ? [{ nodeId: selectedNodeId!, label: nodes.find(n => n.id === selectedNodeId)?.label ?? '', data: mockData }]
    : nodes.length > 0
      ? nodes.map((node, i) => ({
          nodeId: node.id,
          label: node.label,
          data: mockData.map(v => +(v + i * 0.5).toFixed(1)),
        }))
      : []

  return (
    <div style={{ padding: '24px', maxWidth: '960px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>센서 데이터</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={selectedFieldId ?? ''}
          onChange={(e) => {
            setSelectedFieldId(e.target.value ? Number(e.target.value) : null)
            setSelectedNodeId(null)
          }}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
        >
          <option value="">논 선택</option>
          {mockFields.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>

        <select
          value={selectedNodeId ?? ''}
          onChange={(e) => setSelectedNodeId(e.target.value ? Number(e.target.value) : null)}
          disabled={!selectedFieldId}
          style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: selectedFieldId ? 'pointer' : 'not-allowed', opacity: selectedFieldId ? 1 : 0.5 }}
        >
          <option value="">전체 기기</option>
          {nodes.map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}
        </select>

        <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
          {timeRanges.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedTime(t)}
              style={{
                fontSize: '12px',
                padding: '5px 12px',
                borderRadius: '20px',
                border: '0.5px solid #ccc',
                cursor: 'pointer',
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
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '12px' }}>
          <SensorChart datasets={datasets} labels={mockLabels} singleMode={singleMode} />
          {singleMode && (
            <SensorStats
              currentLevel={3.2}
              sensorStatus="정상"
              avg={-2.1}
              max={5.0}
              min={-15.2}
              alarmCount={1}
            />
          )}
        </div>
      )}
    </div>
  )
}