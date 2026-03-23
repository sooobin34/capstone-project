import { useState, useEffect } from 'react'
import FieldMap from '../components/map/FieldMap'
import FieldInfo from '../components/map/FieldInfo'
import { getFields, getNodes, Field, Node } from '../api/dashboard'

export default function MapPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchFields()
  }, [])

  useEffect(() => {
    if (selectedFieldId) fetchNodes(selectedFieldId)
  }, [selectedFieldId])

  const fetchFields = async () => {
    try {
      const data = await getFields()
      setFields(data)
      if (data.length > 0) setSelectedFieldId(data[0].id)
    } catch (e) {
      console.error('논 조회 실패', e)
    } finally {
      setLoading(false)
    }
  }

  const fetchNodes = async (fieldId: number) => {
    try {
      const data = await getNodes(fieldId)
      setNodes(data)
    } catch (e) {
      console.error('기기 조회 실패', e)
    }
  }

  const selectedField = fields.find((f) => f.id === selectedFieldId)

  const mapSensors = nodes.map((n) => ({
    id: n.id,
    lat: n.latitude,
    lng: n.longitude,
    name: `Node ${n.id} · ${n.location_desc}`,
  }))

  const fieldInfoSensors = nodes.map((n) => ({
    id: n.id,
    name: `Node ${n.id}`,
    status: n.is_active ? '정상' as const : '센서 오류' as const,
    level: 0,
  }))

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
                currentLevel={0}
                sensors={fieldInfoSensors}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}

/* 아래는 알람페이지api 연결까지 정상 작동
import { useState } from 'react'
import FieldMap from '../components/map/FieldMap'
import FieldInfo from '../components/map/FieldInfo'

const mockFields = [
  {
    id: 1,
    name: '1번 논 (전주 A)',
    center: [35.8242, 127.1480] as [number, number],
    currentLevel: 3.2,
    sensors: [
      { id: 1, name: '센서 A-1', status: '정상' as const, level: 3.2, lat: 35.8242, lng: 127.1480 },
      { id: 2, name: '센서 A-2', status: '정상' as const, level: 3.0, lat: 35.8245, lng: 127.1485 },
    ],
  },
  {
    id: 2,
    name: '2번 논 (전주 B)',
    center: [35.8260, 127.1500] as [number, number],
    currentLevel: -16,
    sensors: [
      { id: 3, name: '센서 B-1', status: '수위 이상' as const, level: -16, lat: 35.8260, lng: 127.1500 },
    ],
  },
  {
    id: 3,
    name: '3번 논 (전주 C)',
    center: [35.8230, 127.1460] as [number, number],
    currentLevel: 2.1,
    sensors: [
      { id: 4, name: '센서 C-1', status: '센서 오류' as const, level: 2.1, lat: 35.8230, lng: 127.1460 },
    ],
  },
]

export default function MapPage() {
  const [selectedFieldId, setSelectedFieldId] = useState(1)
  const selectedField = mockFields.find((f) => f.id === selectedFieldId)!

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>지도</h2>

      <select
        value={selectedFieldId}
        onChange={(e) => setSelectedFieldId(Number(e.target.value))}
        style={{
          fontSize: '13px',
          padding: '7px 12px',
          borderRadius: '8px',
          border: '0.5px solid #ccc',
          background: 'white',
          cursor: 'pointer',
          marginBottom: '16px',
        }}
      >
        {mockFields.map((f) => (
          <option key={f.id} value={f.id}>{f.name}</option>
        ))}
      </select>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '12px' }}>
        <FieldMap sensors={selectedField.sensors} center={selectedField.center} />
        <FieldInfo
          fieldName={selectedField.name}
          currentLevel={selectedField.currentLevel}
          sensors={selectedField.sensors}
        />
      </div>
    </div>
  )
}
*/