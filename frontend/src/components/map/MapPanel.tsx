import { useState } from 'react'
import { REGIONS } from '../../data/regions'
import FieldInfo from './FieldInfo'
import { Field } from '../../api/dashboard'
import api from '../../api/axios'

interface MapPanelProps {
  fields: Field[]
  selectedFieldId: number | null
  onFieldSelect: (fieldId: number) => void
  onFieldsRefresh: () => void
  sensors: {
    id: number
    name: string
    is_active: boolean
    current_status: string
    latest_level: number | null
  }[]
  fieldName: string
  loading: boolean
}

export default function MapPanel({
  fields, selectedFieldId, onFieldSelect,
  onFieldsRefresh, sensors, fieldName, loading
}: MapPanelProps) {
  const [selectedRegion, setSelectedRegion] = useState('')

  // 논/노드 추가 관련 state (주석처리된 기능용)
  const [showAddField, setShowAddField] = useState(false)
  const [showAddNode, setShowAddNode] = useState(false)
  const [newField, setNewField] = useState({ field_name: '', latitude: '', longitude: '', location_desc: '' })
  const [newNode, setNewNode] = useState({ field_id: '', mac_address: '', latitude: '', longitude: '', location_desc: '' })
  const [addLoading, setAddLoading] = useState(false)
  const [message, setMessage] = useState('')

  const showMessage = (msg: string) => {
    setMessage(msg)
    setTimeout(() => setMessage(''), 4000)
  }

  const filteredFields = selectedRegion
    ? fields.filter(f => f.location_desc?.includes(selectedRegion))
    : fields

  const handleAddField = async () => {
    if (!newField.field_name || !newField.latitude || !newField.longitude) {
      showMessage('논 이름, 위도, 경도는 필수예요')
      return
    }
    try {
      setAddLoading(true)
      await api.post('/fields', {
        field_name: newField.field_name,
        latitude: parseFloat(newField.latitude),
        longitude: parseFloat(newField.longitude),
        location_desc: newField.location_desc || selectedRegion,
      })
      showMessage('논이 추가됐어요!')
      setNewField({ field_name: '', latitude: '', longitude: '', location_desc: '' })
      setShowAddField(false)
      onFieldsRefresh()
    } catch {
      showMessage('논 추가 실패')
    } finally {
      setAddLoading(false)
    }
  }

  const handleAddNode = async () => {
    if (!newNode.field_id || !newNode.mac_address || !newNode.latitude || !newNode.longitude) {
      showMessage('모든 필수 항목을 입력해줘요')
      return
    }
    try {
      setAddLoading(true)
      await api.post('/nodes', {
        field_id: parseInt(newNode.field_id),
        mac_address: newNode.mac_address,
        latitude: parseFloat(newNode.latitude),
        longitude: parseFloat(newNode.longitude),
        location_desc: newNode.location_desc,
        is_active: true,
      })
      showMessage('노드가 추가됐어요!')
      setNewNode({ field_id: '', mac_address: '', latitude: '', longitude: '', location_desc: '' })
      setShowAddNode(false)
      onFieldsRefresh()
    } catch {
      showMessage('노드 추가 실패')
    } finally {
      setAddLoading(false)
    }
  }

  const inputStyle = {
    width: '100%', fontSize: '12px', padding: '7px 10px',
    borderRadius: '6px', border: '0.5px solid #ccc',
    background: 'white', boxSizing: 'border-box' as const,
    marginBottom: '8px',
  }

  const btnStyle = (color = '#1D9E75') => ({
    fontSize: '12px', padding: '7px 14px', borderRadius: '6px',
    border: 'none', cursor: 'pointer', background: color, color: 'white', fontWeight: 500,
  })

  return (
    <div style={{ padding: '16px', minWidth: '320px' }}>

      {/* 메시지 */}
      {message && (
        <div style={{
          fontSize: '12px', padding: '8px 12px', borderRadius: '6px',
          background: message.includes('실패') || message.includes('필수') ? '#fce4ec' : '#e8f5e9',
          color: message.includes('실패') || message.includes('필수') ? '#c62828' : '#2e7d32',
          marginBottom: '12px',
        }}>
          {message}
        </div>
      )}

      {/* 논/노드 추가 영역 - 주석처리
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '11px', color: '#888', marginBottom: '8px', fontWeight: 500 }}>추가</p>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <button onClick={() => { setShowAddField(!showAddField); setShowAddNode(false) }}
            style={{ ...btnStyle(), flex: 1 }}>+ 논 추가</button>
          <button onClick={() => { setShowAddNode(!showAddNode); setShowAddField(false) }}
            style={{ ...btnStyle('#378ADD'), flex: 1 }}>+ 노드 추가</button>
        </div>
        {showAddField && (
          <div style={{ background: '#f9f9f9', borderRadius: '8px', padding: '12px', marginBottom: '8px' }}>
            <p style={{ fontSize: '12px', fontWeight: 500, marginBottom: '8px' }}>논 추가</p>
            <input placeholder="논 이름 *" value={newField.field_name}
              onChange={e => setNewField({ ...newField, field_name: e.target.value })} style={inputStyle} />
            <input placeholder="위도 * (예: 35.8468)" value={newField.latitude}
              onChange={e => setNewField({ ...newField, latitude: e.target.value })} style={inputStyle} />
            <input placeholder="경도 * (예: 127.1294)" value={newField.longitude}
              onChange={e => setNewField({ ...newField, longitude: e.target.value })} style={inputStyle} />
            <select value={newField.location_desc}
              onChange={e => setNewField({ ...newField, location_desc: e.target.value })} style={inputStyle}>
              <option value="">지역 선택</option>
              {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={handleAddField} disabled={addLoading} style={{ ...btnStyle(), flex: 1 }}>
                {addLoading ? '추가 중...' : '추가'}
              </button>
              <button onClick={() => setShowAddField(false)} style={{ ...btnStyle('#888'), flex: 1 }}>취소</button>
            </div>
          </div>
        )}
        {showAddNode && (
          <div style={{ background: '#f9f9f9', borderRadius: '8px', padding: '12px', marginBottom: '8px' }}>
            <p style={{ fontSize: '12px', fontWeight: 500, marginBottom: '8px' }}>노드 추가</p>
            <select value={newNode.field_id}
              onChange={e => setNewNode({ ...newNode, field_id: e.target.value })} style={inputStyle}>
              <option value="">논 선택 *</option>
              {fields.map(f => <option key={f.id} value={f.id}>{f.field_name}</option>)}
            </select>
            <input placeholder="MAC 주소 *" value={newNode.mac_address}
              onChange={e => setNewNode({ ...newNode, mac_address: e.target.value })} style={inputStyle} />
            <input placeholder="위도 *" value={newNode.latitude}
              onChange={e => setNewNode({ ...newNode, latitude: e.target.value })} style={inputStyle} />
            <input placeholder="경도 *" value={newNode.longitude}
              onChange={e => setNewNode({ ...newNode, longitude: e.target.value })} style={inputStyle} />
            <input placeholder="설명" value={newNode.location_desc}
              onChange={e => setNewNode({ ...newNode, location_desc: e.target.value })} style={inputStyle} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={handleAddNode} disabled={addLoading} style={{ ...btnStyle('#378ADD'), flex: 1 }}>
                {addLoading ? '추가 중...' : '추가'}
              </button>
              <button onClick={() => setShowAddNode(false)} style={{ ...btnStyle('#888'), flex: 1 }}>취소</button>
            </div>
          </div>
        )}
      </div>
      */}

      {/* 지역/논 선택 영역 */}
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '11px', color: '#888', marginBottom: '8px', fontWeight: 500 }}>지역 선택</p>
        <select value={selectedRegion}
          onChange={e => setSelectedRegion(e.target.value)}
          style={{ ...inputStyle, marginBottom: '8px' }}>
          <option value="">전체 지역</option>
          {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
        </select>

        <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px', fontWeight: 500 }}>논 선택</p>
        <select value={selectedFieldId ?? ''}
          onChange={e => onFieldSelect(Number(e.target.value))}
          style={inputStyle}>
          {filteredFields.map(f => <option key={f.id} value={f.id}>{f.field_name}</option>)}
        </select>
      </div>

      <div style={{ borderTop: '0.5px solid #f0f0f0', marginBottom: '16px' }} />

      {/* 센서 상태 */}
      {loading ? (
        <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '24px 0' }}>불러오는 중...</p>
      ) : (
        <FieldInfo fieldName={fieldName} sensors={sensors} />
      )}
    </div>
  )
}