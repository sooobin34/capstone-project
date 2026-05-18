import { useState, useEffect } from 'react'
import { getLatestSensorLog, uploadValidationRecord, getValidationRecords, getValidationSummary, analyzeValidationRecord, getFields, getNodes } from '../api/dashboard'

const SURFACE_STATUS_OPTIONS = [
  { label: '물 있음', value: 'WATER_VISIBLE' },
  { label: '물 없음', value: 'NO_WATER_VISIBLE' },
  { label: '애매함', value: 'UNKNOWN' },
]

const SURFACE_STATUS_OPTIONS_AUTO = [
  { label: '물 있음', value: 'WATER_VISIBLE' },
  { label: '물 없음', value: 'NO_WATER_VISIBLE' },
  { label: '애매함', value: 'UNKNOWN' },
]

const STATUS_ALIAS_MAP: Record<string, 'WATER_VISIBLE' | 'NO_WATER_VISIBLE' | 'UNKNOWN'> = {
  WATER_VISIBLE: 'WATER_VISIBLE',
  NO_WATER_VISIBLE: 'NO_WATER_VISIBLE',
  UNKNOWN: 'UNKNOWN',
  LOW: 'WATER_VISIBLE',
  MID: 'UNKNOWN',
  HIGH: 'NO_WATER_VISIBLE',
}

function normalizeStatusValue(raw?: string): 'WATER_VISIBLE' | 'NO_WATER_VISIBLE' | 'UNKNOWN' {
  const key = (raw ?? '').toUpperCase()
  return STATUS_ALIAS_MAP[key] ?? 'UNKNOWN'
}

function toKoreanStatusLabel(raw?: string): string {
  const normalized = normalizeStatusValue(raw)
  if (normalized === 'WATER_VISIBLE') return '물 있음'
  if (normalized === 'NO_WATER_VISIBLE') return '물 없음'
  return '애매함'
}

const ANGLE_OPTIONS = ['수직', '좌', '우', '기타']
const DISTANCE_OPTIONS = ['50cm', '80cm', '110cm', '140cm', '170cm', '200cm', '기타']
const CONDITION_OPTIONS = ['햇빛 강함', '그림자 있음', '물 반사 있음', '흙 젖음', '흐림', '화질 흐림', '수초·벼 가림', '기타']

const STATUS_LABEL_MAP: Record<string, string> = {
  WATER_VISIBLE: '물있음',
  NO_WATER_VISIBLE: '물없음',
  UNKNOWN: '애매함',
}

function createImageTitle(observedStatus: string, angle: string, distance: string) {
  const statusLabel = STATUS_LABEL_MAP[observedStatus] ?? '상태미정'
  const parts = [statusLabel]
  if (angle) parts.push(angle)
  if (distance) parts.push(distance)
  return parts.join('_')
}

const NODE_ID_FOR_LOG = 7

const MRV_STEPS = [
  { num: '01', title: '센서 데이터 수집', desc: 'LoRa 게이트웨이가 논의 수위와 배터리 상태를 실시간으로 측정하여 서버에 저장합니다.' },
  { num: '02', title: '일일 요약 생성', desc: '하루 동안의 센서 데이터를 바탕으로 평균 수위와 논 상태를 자동으로 계산합니다.' },
  { num: '03', title: 'Validation 검증 수행', desc: '현장 사진을 업로드하고 사람의 판단과 AI 분석 결과를 비교하여 센서 정확도를 검증합니다.' },
  { num: '04', title: 'MRV 보고서 생성', desc: '수집된 센서 데이터와 검증 결과를 바탕으로 AWD 횟수, 탄소 감축량 등을 담은 공식 보고서를 생성합니다.' },
]

export default function ValidationPage() {
  const [tab, setTab] = useState<'field' | 'auto'>('field')
  const [latestLog, setLatestLog] = useState<any>(null)
  const [logLoading, setLogLoading] = useState(false)

  // 필드/노드 목록
  const [fields, setFields] = useState<any[]>([])
  const [nodes, setNodes] = useState<any[]>([])
  const [fieldId, setFieldId] = useState<number | ''>('')
  const [nodeId, setNodeId] = useState<number | ''>('')

  // 업로드 폼
  const [observedStatus, setObservedStatus] = useState('WATER_VISIBLE')
  const [angle, setAngle] = useState('')
  const [distance, setDistance] = useState('')
  const [conditions, setConditions] = useState<string[]>([])
  const [extraNote, setExtraNote] = useState('')
  const [recordDate, setRecordDate] = useState('')
  const [captureTime, setCaptureTime] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState(false)

  const [records, setRecords] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [analyzingId, setAnalyzingId] = useState<number | null>(null)
  const [modalImage, setModalImage] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterDate, setFilterDate] = useState('')

  useEffect(() => {
    getFields().then(setFields).catch(console.error)
    fetchLatestLog()
    fetchRecords()
    fetchSummary()
  }, [])

  useEffect(() => {
    if (fieldId) {
      getNodes(Number(fieldId)).then(setNodes).catch(console.error)
    } else {
      setNodes([])
      setNodeId('')
    }
  }, [fieldId])

  const fetchLatestLog = async () => {
    setLogLoading(true)
    try {
      const log = await getLatestSensorLog(NODE_ID_FOR_LOG)
      setLatestLog(log)
    } catch {
      setLatestLog(null)
    } finally {
      setLogLoading(false)
    }
  }

  const fetchRecords = async () => {
    try {
      const data = await getValidationRecords()
      setRecords(data)
    } catch { }
  }

  const fetchSummary = async () => {
    try {
      const data = await getValidationSummary()
      setSummary(data)
    } catch { }
  }

  const filteredRecords = records
    .filter(r => filterStatus ? normalizeStatusValue(r.observed_surface_status) === filterStatus : true)
    .filter(r => filterDate ? r.record_date === filterDate : true)

  const handleConditionToggle = (c: string) => {
    setConditions(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])
  }

  const buildNote = () => {
    const parts = []
    if (angle) parts.push(angle)
    if (distance) parts.push(distance)
    if (conditions.length > 0) parts.push(conditions.join(', '))
    if (extraNote) parts.push(extraNote)
    return parts.join(' / ')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) {
      setFile(f)
      setPreview(URL.createObjectURL(f))
    }
  }

  const handleUpload = async () => {
    if (!fieldId || !nodeId || !file || !recordDate || !captureTime) {
      setUploadError('논, 노드, 사진, 촬영 날짜, 촬영 시각은 필수입니다.')
      return
    }
    setUploading(true)
    setUploadError('')
    setUploadSuccess(false)
    try {
      const formData = new FormData()
      const autoTitle = createImageTitle(observedStatus, angle, distance)
      formData.append('field_id', String(fieldId))
      formData.append('node_id', String(nodeId))
      formData.append('record_date', recordDate)
      formData.append('captured_at', `${recordDate}T${captureTime}:00+09:00`)
      formData.append('observed_surface_status', observedStatus)
      formData.append('image_title', autoTitle)
      formData.append('note', buildNote())
      formData.append('file', file)

      await uploadValidationRecord(formData)
      setUploadSuccess(true)
      setFile(null)
      setPreview(null)
      setAngle('')
      setDistance('')
      setConditions([])
      setExtraNote('')
      setRecordDate('')
      setCaptureTime('')
      await fetchRecords()
      await fetchSummary()
    } catch (e: any) {
      setUploadError(e?.response?.data?.message ?? '업로드 실패')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async (id: number) => {
    setAnalyzingId(id)
    try {
      await analyzeValidationRecord(id)
      await fetchRecords()
      await fetchSummary()
    } catch {
      alert('AI 분석 실패')
    } finally {
      setAnalyzingId(null)
    }
  }

  const inputStyle = {
    fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
    border: '0.5px solid #ccc', background: 'white', width: '100%',
    boxSizing: 'border-box' as const,
  }

  const requiredInputStyle = {
    ...inputStyle,
    border: '0.5px solid #1D9E75',
  }

  const chipStyle = (selected: boolean) => ({
    fontSize: '12px', padding: '4px 10px', borderRadius: '20px',
    border: `0.5px solid ${selected ? '#1D9E75' : '#ccc'}`,
    background: selected ? '#e8f5e9' : 'white',
    color: selected ? '#1D9E75' : '#555',
    cursor: 'pointer',
  })

  return (
    <div style={{ padding: '16px', maxWidth: '1200px', margin: '0 auto', boxSizing: 'border-box' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '16px' }}>검증 사진</h2>

      {/* 탭 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {[
          { key: 'field', label: '현장 테스트' },
          { key: 'auto', label: '자동 분석' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as 'field' | 'auto')}
            style={{
              fontSize: '13px', padding: '7px 18px', borderRadius: '8px',
              border: 'none', cursor: 'pointer', fontWeight: 500,
              background: tab === t.key ? '#1D9E75' : '#f0f0f0',
              color: tab === t.key ? 'white' : '#888',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'auto' ? (
        <>
          {/* MRV 보고서 생성 흐름 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>MRV 보고서 생성 흐름</p>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '16px' }}>센서 데이터 수집 → 일 요약 생성 → Validation 검증 수행 → MRV 보고서 생성</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
              {MRV_STEPS.map((step) => (
                <div key={step.num} style={{ background: '#f5f5f5', borderRadius: '10px', padding: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#1D9E75' }}>{step.num}</span>
                    <span style={{ fontSize: '12px', fontWeight: 500 }}>{step.title}</span>
                  </div>
                  <p style={{ fontSize: '11px', color: '#666', lineHeight: 1.5 }}>{step.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 검증 사진 목록 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '8px 16px' }}>
            <div style={{ display: 'flex', gap: '8px', padding: '8px 0 10px', borderBottom: '0.5px solid #f0f0f0', flexWrap: 'wrap' }}>
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                style={{ fontSize: '12px', padding: '5px 8px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white' }}>
                <option value="">전체 상태</option>
                {SURFACE_STATUS_OPTIONS_AUTO.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
              <input type="date" value={filterDate} onChange={(e) => setFilterDate(e.target.value)}
                style={{ fontSize: '12px', padding: '5px 8px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white' }} />
              {(filterStatus || filterDate) && (
                <button onClick={() => { setFilterStatus(''); setFilterDate('') }}
                  style={{ fontSize: '12px', padding: '5px 10px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer', color: '#888' }}>
                  초기화
                </button>
              )}
            </div>
            <p style={{ fontSize: '12px', color: '#888', padding: '8px 0 10px', borderBottom: '0.5px solid #f0f0f0' }}>
              검증 기록 총 {filteredRecords.length}건
            </p>
            {filteredRecords.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#aaa', padding: '24px 0', textAlign: 'center' }}>검증 기록이 없습니다</p>
            ) : (
              filteredRecords.map((record, i) => (
                <div key={record.id} style={{
                  display: 'flex', gap: '12px', alignItems: 'flex-start',
                  padding: '12px 0', borderBottom: i < filteredRecords.length - 1 ? '0.5px solid #f0f0f0' : 'none',
                }}>
                  {record.image_url && (
                    <img src={record.image_url} alt="검증사진" onClick={() => setModalImage(record.image_url)}
                      style={{ width: '64px', height: '64px', objectFit: 'cover', borderRadius: '8px', flexShrink: 0, cursor: 'pointer' }} />
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px', gap: '8px', flexWrap: 'wrap' }}>
                      <p style={{ fontSize: '13px', fontWeight: 500, wordBreak: 'break-word' }}>
                        {record.image_title || '제목 없음'} · {record.record_date}
                      </p>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0 }}>
                        {record.is_match !== null && (
                          <span style={{
                            fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
                            background: record.is_match ? '#e8f5e9' : '#fce4ec',
                            color: record.is_match ? '#2e7d32' : '#c62828',
                          }}>{record.is_match ? '일치' : '불일치'}</span>
                        )}
                        <button onClick={() => handleAnalyze(record.id)} disabled={analyzingId === record.id}
                          style={{
                            fontSize: '11px', padding: '4px 10px', borderRadius: '8px',
                            border: '0.5px solid #1D9E75', background: 'white', cursor: 'pointer', color: '#1D9E75',
                            opacity: analyzingId === record.id ? 0.6 : 1, whiteSpace: 'nowrap',
                          }}>
                          {analyzingId === record.id ? 'AI 분석 중...' : 'AI 분석'}
                        </button>
                      </div>
                    </div>
                    <p style={{ fontSize: '11px', color: '#888', marginBottom: '2px' }}>
<<<<<<< Updated upstream
                      사람: {SURFACE_STATUS_OPTIONS.find(s => s.value === record.observed_surface_status)?.label ?? record.observed_surface_status}
{record.ai_predicted_status && ` · AI: ${SURFACE_STATUS_OPTIONS_AUTO.find(s => s.value === record.ai_predicted_status)?.label ?? record.ai_predicted_status}`}
=======
                      사람: {toKoreanStatusLabel(record.observed_surface_status)}
                      {record.ai_predicted_status && ` · AI: ${toKoreanStatusLabel(record.ai_predicted_status)}`}
>>>>>>> Stashed changes
                      {record.ai_confidence != null && ` · 신뢰도 ${record.ai_confidence}%`}
                    </p>
                    {record.note && <p style={{ fontSize: '11px', color: '#aaa' }}>{record.note}</p>}
                    <p style={{ fontSize: '10px', color: '#bbb', marginTop: '2px' }}>{new Date(record.created_at).toLocaleString('ko-KR')}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      ) : (
        <>
          {/* 최신 센서값 카드 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <p style={{ fontSize: '13px', fontWeight: 500 }}>최신 LoRa 센서값 · Node {NODE_ID_FOR_LOG}</p>
              <button onClick={fetchLatestLog} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}>
                {logLoading ? '로딩...' : '새로고침'}
              </button>
            </div>
            {latestLog ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '8px' }}>
                {[
                  { label: '내부 수위', value: `${latestLog.inner_water_level}cm` },
                  { label: '배터리', value: `${latestLog.battery_voltage}V` },
                  { label: '측정 시간', value: new Date(latestLog.measured_at).toLocaleString('ko-KR') },
                ].map((item) => (
                  <div key={item.label} style={{ background: '#f5f5f5', borderRadius: '8px', padding: '8px 12px' }}>
                    <p style={{ fontSize: '10px', color: '#888', marginBottom: '2px' }}>{item.label}</p>
                    <p style={{ fontSize: '14px', fontWeight: 500 }}>{item.value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '12px 0' }}>센서 데이터 없음</p>
            )}
          </div>

          {/* 사진 업로드 폼 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>사진 업로드</p>
            <p style={{ fontSize: '11px', color: '#1D9E75', marginBottom: '12px' }}>* 표시는 필수 항목입니다</p>

            {/* 논 선택 (필수) */}
            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>논 선택 *</p>
              <select value={fieldId} onChange={(e) => { setFieldId(e.target.value ? Number(e.target.value) : ''); setNodeId('') }}
                style={requiredInputStyle}>
                <option value="">논 선택</option>
                {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
              </select>
            </div>

            {/* 노드 선택 (필수) */}
            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>센서 노드 *</p>
              <select value={nodeId} onChange={(e) => setNodeId(e.target.value ? Number(e.target.value) : '')}
                disabled={!fieldId}
                style={{ ...requiredInputStyle, opacity: fieldId ? 1 : 0.5 }}>
                <option value="">노드 선택</option>
                {nodes.map((n) => <option key={n.id} value={n.id}>Node {n.id} · {n.location_desc}</option>)}
              </select>
            </div>

            {/* 촬영 날짜/시각 (필수) */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
              <div>
                <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영 날짜 *</p>
                <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)}
                  style={requiredInputStyle} />
              </div>
              <div>
                <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영 시각 *</p>
                <input type="time" value={captureTime} onChange={(e) => setCaptureTime(e.target.value)}
                  style={requiredInputStyle} />
              </div>
            </div>

            {/* 관찰 상태 (필수) */}
            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>관찰 상태 *</p>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {SURFACE_STATUS_OPTIONS.map((s) => (
                  <button key={s.value} onClick={() => setObservedStatus(s.value)} style={chipStyle(observedStatus === s.value)}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 촬영 각도 (선택) */}
            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영 각도</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {ANGLE_OPTIONS.map((a) => (
                  <button key={a} onClick={() => setAngle(angle === a ? '' : a)} style={chipStyle(angle === a)}>{a}</button>
                ))}
              </div>
            </div>

            {/* 촬영 높이 (선택) */}
            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영 높이</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {DISTANCE_OPTIONS.map((d) => (
                  <button key={d} onClick={() => setDistance(distance === d ? '' : d)} style={chipStyle(distance === d)}>{d}</button>
                ))}
              </div>
            </div>

            {/* 빛/방해요소 (선택) */}
            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>빛/방해요소</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {CONDITION_OPTIONS.map((c) => (
                  <button key={c} onClick={() => handleConditionToggle(c)} style={chipStyle(conditions.includes(c))}>{c}</button>
                ))}
              </div>
            </div>

            {/* 메모 (선택) */}
            <div style={{ marginBottom: '12px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>메모</p>
              <input type="text" value={extraNote} onChange={(e) => setExtraNote(e.target.value)} placeholder="추가 메모" style={inputStyle} />
            </div>

            {/* 사진 선택 (필수) */}
            <div style={{ marginBottom: '12px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>사진 선택 *</p>
              <input type="file" accept="image/*" capture="environment" onChange={handleFileChange}
                style={{ fontSize: '13px', width: '100%' }} />
              {preview && (
                <img src={preview} alt="미리보기" style={{ marginTop: '10px', maxWidth: '100%', maxHeight: '200px', borderRadius: '8px', border: '0.5px solid #e0e0e0' }} />
              )}
            </div>

            {uploadError && <p style={{ fontSize: '12px', color: '#c62828', marginBottom: '8px' }}>{uploadError}</p>}
            {uploadSuccess && <p style={{ fontSize: '12px', color: '#2e7d32', marginBottom: '8px' }}>업로드 성공!</p>}

            <button onClick={handleUpload} disabled={uploading}
              style={{
                fontSize: '13px', padding: '8px 20px', borderRadius: '8px',
                border: 'none', background: '#1D9E75', color: 'white',
                cursor: uploading ? 'not-allowed' : 'pointer', fontWeight: 500,
                opacity: uploading ? 0.7 : 1, width: '100%',
              }}>
              {uploading ? '업로드 중...' : '저장'}
            </button>
          </div>
        </>
      )}

      {modalImage && (
        <div onClick={() => setModalImage(null)}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', zIndex: 1000, cursor: 'pointer',
          }}>
          <img src={modalImage} alt="크게보기" style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: '12px' }} />
        </div>
      )}
    </div>
  )
}
