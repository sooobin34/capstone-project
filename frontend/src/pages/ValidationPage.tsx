import { useState, useEffect } from 'react'
import { getFields, getNodes, uploadValidationRecord, getValidationRecords, getValidationSummary, analyzeValidationRecord } from '../api/dashboard'

const STATUS_OPTIONS = ['FLOODED', 'DRYING', 'DRY', 'UNKNOWN']
const STATUS_LABEL: Record<string, string> = {
  FLOODED: '담수', DRYING: '건조중', DRY: '건조', UNKNOWN: '알 수 없음'
}

export default function ValidationPage() {
  const [fields, setFields] = useState<any[]>([])
  const [nodes, setNodes] = useState<any[]>([])
  const [records, setRecords] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)

  const [fieldId, setFieldId] = useState<number | ''>('')
  const [nodeId, setNodeId] = useState<number | ''>('')
  const [recordDate, setRecordDate] = useState('')
  const [imageTitle, setImageTitle] = useState('')
  const [sensorStatus, setSensorStatus] = useState('FLOODED')
  const [observedStatus, setObservedStatus] = useState('FLOODED')
  const [note, setNote] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState(false)

  useEffect(() => {
    getFields().then(setFields).catch(console.error)
  }, [])

  useEffect(() => {
    if (fieldId) {
      getNodes(Number(fieldId)).then(setNodes).catch(console.error)
      getValidationRecords(Number(fieldId)).then(setRecords).catch(console.error)
      getValidationSummary(Number(fieldId)).then(setSummary).catch(console.error)
    } else {
      setNodes([])
      getValidationRecords().then(setRecords).catch(console.error)
      getValidationSummary().then(setSummary).catch(console.error)
    }
  }, [fieldId])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) {
      setFile(f)
      setPreview(URL.createObjectURL(f))
    }
  }

  const handleUpload = async () => {
    if (!fieldId || !nodeId || !recordDate || !file) {
      setUploadError('논, 노드, 날짜, 사진을 모두 입력해주세요.')
      return
    }
    setUploading(true)
    setUploadError('')
    setUploadSuccess(false)
    try {
      const formData = new FormData()
      formData.append('field_id', String(fieldId))
      formData.append('node_id', String(nodeId))
      formData.append('record_date', recordDate)
      formData.append('image_title', imageTitle || file.name)
      formData.append('sensor_predicted_status', sensorStatus)
      formData.append('observed_surface_status', observedStatus)
      formData.append('note', note)
      formData.append('file', file)

      await uploadValidationRecord(formData)
      setUploadSuccess(true)
      setFile(null)
      setPreview(null)
      setImageTitle('')
      setNote('')

      // 목록 새로고침
      const updated = await getValidationRecords(fieldId ? Number(fieldId) : undefined)
      setRecords(updated)
      const updatedSummary = await getValidationSummary(fieldId ? Number(fieldId) : undefined)
      setSummary(updatedSummary)
    } catch (e: any) {
      setUploadError(e?.response?.data?.message ?? '업로드 실패')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async (recordId: number) => {
    try {
      await analyzeValidationRecord(recordId)
      const updated = await getValidationRecords(fieldId ? Number(fieldId) : undefined)
      setRecords(updated)
    } catch {
      alert('AI 분석 실패')
    }
  }

  const selectStyle = {
    fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
    border: '0.5px solid #ccc', background: 'white', width: '100%',
  }

  const inputStyle = {
    fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
    border: '0.5px solid #ccc', background: 'white', width: '100%',
    boxSizing: 'border-box' as const,
  }

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '16px' }}>검증 사진</h2>

      {/* 요약 */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '16px' }}>
          {[
            { label: '총 검증 수', value: `${summary.total_count ?? 0}건` },
            { label: '일치 수', value: `${summary.match_count ?? 0}건` },
            { label: '정확도', value: `${summary.validation_accuracy ?? 0}%` },
          ].map((item) => (
            <div key={item.label} style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '10px', padding: '12px 16px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
              <p style={{ fontSize: '20px', fontWeight: 500 }}>{item.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* 업로드 폼 */}
      <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
        <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>사진 업로드</p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <div>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>논 선택</p>
            <select value={fieldId} onChange={(e) => { setFieldId(e.target.value ? Number(e.target.value) : ''); setNodeId('') }} style={selectStyle}>
              <option value="">논 선택</option>
              {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
            </select>
          </div>
          <div>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>노드 선택</p>
            <select value={nodeId} onChange={(e) => setNodeId(e.target.value ? Number(e.target.value) : '')} style={selectStyle}>
              <option value="">노드 선택</option>
              {nodes.map((n) => <option key={n.id} value={n.id}>Node {n.id}</option>)}
            </select>
          </div>
          <div>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영일</p>
            <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>사진 제목</p>
            <input type="text" value={imageTitle} onChange={(e) => setImageTitle(e.target.value)} placeholder="사진 제목 (선택)" style={inputStyle} />
          </div>
          <div>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>센서 예측 상태</p>
            <select value={sensorStatus} onChange={(e) => setSensorStatus(e.target.value)} style={selectStyle}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </select>
          </div>
          <div>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>실제 관찰 상태</p>
            <select value={observedStatus} onChange={(e) => setObservedStatus(e.target.value)} style={selectStyle}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: '10px' }}>
          <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>메모</p>
          <input type="text" value={note} onChange={(e) => setNote(e.target.value)} placeholder="메모 (선택)" style={inputStyle} />
        </div>

        {/* 사진 업로드 */}
        <div style={{ marginBottom: '12px' }}>
          <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>사진 선택</p>
          <input type="file" accept="image/*" onChange={handleFileChange} style={{ fontSize: '13px' }} />
          {preview && (
            <img src={preview} alt="미리보기" style={{ marginTop: '10px', maxHeight: '200px', borderRadius: '8px', border: '0.5px solid #e0e0e0' }} />
          )}
        </div>

        {uploadError && <p style={{ fontSize: '12px', color: '#c62828', marginBottom: '8px' }}>{uploadError}</p>}
        {uploadSuccess && <p style={{ fontSize: '12px', color: '#2e7d32', marginBottom: '8px' }}>업로드 성공!</p>}

        <button
          onClick={handleUpload}
          disabled={uploading}
          style={{
            fontSize: '13px', padding: '8px 20px', borderRadius: '8px',
            border: 'none', background: '#1D9E75', color: 'white',
            cursor: uploading ? 'not-allowed' : 'pointer', fontWeight: 500,
            opacity: uploading ? 0.7 : 1,
          }}
        >
          {uploading ? '업로드 중...' : '저장'}
        </button>
      </div>

      {/* 검증 기록 목록 */}
      <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '8px 16px' }}>
        <p style={{ fontSize: '12px', color: '#888', padding: '8px 0 10px', borderBottom: '0.5px solid #f0f0f0' }}>
          검증 기록 총 {records.length}건
        </p>
        {records.length === 0 ? (
          <p style={{ fontSize: '13px', color: '#aaa', padding: '24px 0', textAlign: 'center' }}>검증 기록이 없습니다</p>
        ) : (
          records.map((record, i) => (
            <div key={record.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '12px 0', borderBottom: i < records.length - 1 ? '0.5px solid #f0f0f0' : 'none',
              gap: '12px',
            }}>
              {record.image_url && (
                <img src={record.image_url} alt="검증사진" style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '8px', flexShrink: 0 }} />
              )}
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '2px' }}>
                  {record.image_title || '제목 없음'} · {record.record_date}
                </p>
                <p style={{ fontSize: '11px', color: '#888' }}>
                  센서: {STATUS_LABEL[record.sensor_predicted_status] ?? record.sensor_predicted_status} · 실제: {STATUS_LABEL[record.observed_surface_status] ?? record.observed_surface_status}
                </p>
                {record.ai_analysis_result && (
                  <p style={{ fontSize: '11px', color: '#1565c0', marginTop: '2px' }}>AI: {record.ai_analysis_result}</p>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                <span style={{
                  fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
                  background: record.is_match ? '#e8f5e9' : '#fce4ec',
                  color: record.is_match ? '#2e7d32' : '#c62828',
                }}>
                  {record.is_match ? '일치' : '불일치'}
                </span>
                <button
                  onClick={() => handleAnalyze(record.id)}
                  style={{
                    fontSize: '11px', padding: '4px 10px', borderRadius: '8px',
                    border: '0.5px solid #ccc', background: 'white', cursor: 'pointer', color: '#555',
                  }}
                >
                  AI 분석
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}