import { useState, useEffect } from 'react'
import { getFields, getNodes, getLatestSensorLog, uploadValidationRecord, getValidationRecords, getValidationSummary, analyzeValidationRecord } from '../api/dashboard'

const SURFACE_STATUS_OPTIONS = [
  { label: '물 보임', value: 'WATER_VISIBLE' },
  { label: '물 안 보임', value: 'NO_WATER_VISIBLE' },
  { label: '애매함', value: 'UNKNOWN' },
]

const ANGLE_OPTIONS = ['정면', '좌측45도', '우측45도', '위에서촬영', '낮은시점', '기타']
const DISTANCE_OPTIONS = ['근접', '중간거리', '원거리', '전체구역', '기타']
const CONDITION_OPTIONS = ['햇빛 강함', '그림자 있음', '물 반사 있음', '흙 젖음', '흐림', '화질 흐림', '수초·벼 가림', '기타']

const FIELD_ID = 1
const NODE_ID = 7

export default function ValidationPage() {
  const [tab, setTab] = useState<'field' | 'auto'>('field')

  // 센서 상태
  const [latestLog, setLatestLog] = useState<any>(null)
  const [logLoading, setLogLoading] = useState(false)

  // 업로드 폼
  const [observedStatus, setObservedStatus] = useState('WATER_VISIBLE')
  const [angle, setAngle] = useState('')
  const [distance, setDistance] = useState('')
  const [conditions, setConditions] = useState<string[]>([])
  const [extraNote, setExtraNote] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState(false)

  // 목록/요약
  const [records, setRecords] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [analyzingId, setAnalyzingId] = useState<number | null>(null)

  const fetchLatestLog = async () => {
    setLogLoading(true)
    try {
      const log = await getLatestSensorLog(NODE_ID)
      setLatestLog(log)
    } catch {
      setLatestLog(null)
    } finally {
      setLogLoading(false)
    }
  }

  const fetchRecords = async () => {
    try {
      const data = await getValidationRecords(FIELD_ID)
      setRecords(data)
    } catch { }
  }

  const fetchSummary = async () => {
    try {
      const data = await getValidationSummary(FIELD_ID)
      setSummary(data)
    } catch { }
  }

  useEffect(() => {
    fetchLatestLog()
    fetchRecords()
    fetchSummary()
  }, [])

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
    if (!file) {
      setUploadError('사진을 선택해주세요.')
      return
    }
    setUploading(true)
    setUploadError('')
    setUploadSuccess(false)
    try {
      const now = new Date()
      const formData = new FormData()
      formData.append('field_id', String(FIELD_ID))
      formData.append('node_id', String(NODE_ID))
      formData.append('record_date', now.toISOString().split('T')[0])
      formData.append('observed_surface_status', observedStatus)
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

  const selectStyle = {
    fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
    border: '0.5px solid #ccc', background: 'white', width: '100%',
  }

  const inputStyle = {
    fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
    border: '0.5px solid #ccc', background: 'white', width: '100%',
    boxSizing: 'border-box' as const,
  }

  const chipStyle = (selected: boolean) => ({
    fontSize: '12px', padding: '4px 10px', borderRadius: '20px',
    border: `0.5px solid ${selected ? '#1D9E75' : '#ccc'}`,
    background: selected ? '#e8f5e9' : 'white',
    color: selected ? '#1D9E75' : '#555',
    cursor: 'pointer',
  })

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
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
        <div style={{ textAlign: 'center', padding: '80px', color: '#aaa', fontSize: '14px' }}>
          🚧 자동 분석 기능은 준비 중입니다.
        </div>
      ) : (
        <>
          {/* 1. 최신 센서값 카드 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <p style={{ fontSize: '13px', fontWeight: 500 }}>최신 LoRa 센서값 · Node {NODE_ID}</p>
              <button onClick={fetchLatestLog} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}>
                {logLoading ? '로딩...' : '새로고침'}
              </button>
            </div>
            {latestLog ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
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

          {/* 2. 사진 업로드 폼 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>사진 업로드</p>

            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>물 상태</p>
              <div style={{ display: 'flex', gap: '8px' }}>
                {SURFACE_STATUS_OPTIONS.map((s) => (
                  <button key={s.value} onClick={() => setObservedStatus(s.value)} style={chipStyle(observedStatus === s.value)}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영 각도</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {ANGLE_OPTIONS.map((a) => (
                  <button key={a} onClick={() => setAngle(angle === a ? '' : a)} style={chipStyle(angle === a)}>{a}</button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>촬영 거리</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {DISTANCE_OPTIONS.map((d) => (
                  <button key={d} onClick={() => setDistance(distance === d ? '' : d)} style={chipStyle(distance === d)}>{d}</button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>빛/방해요소 (복수 선택)</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {CONDITION_OPTIONS.map((c) => (
                  <button key={c} onClick={() => handleConditionToggle(c)} style={chipStyle(conditions.includes(c))}>{c}</button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>추가 메모 (선택)</p>
              <input type="text" value={extraNote} onChange={(e) => setExtraNote(e.target.value)} placeholder="추가 메모" style={inputStyle} />
            </div>

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

          {/* 5. 테스트 요약 카드 */}
          {summary && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '16px' }}>
              {[
                { label: '전체 테스트', value: `${summary.total_validation_count ?? 0}장` },
                { label: 'AI 분석 완료', value: `${records.filter(r => r.ai_predicted_status).length}장` },
                { label: '사람-AI 일치', value: `${summary.match_count ?? 0}건` },
                { label: '사람-AI 불일치', value: `${(summary.total_validation_count ?? 0) - (summary.match_count ?? 0)}건` },
                { label: 'AI 일치율', value: summary.validation_accuracy != null ? `${summary.validation_accuracy}%` : '-' },
              ].map((item) => (
                <div key={item.label} style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '10px', padding: '10px 12px' }}>
                  <p style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
                  <p style={{ fontSize: '16px', fontWeight: 500 }}>{item.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* 3. 검증 사진 목록 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '8px 16px' }}>
            <p style={{ fontSize: '12px', color: '#888', padding: '8px 0 10px', borderBottom: '0.5px solid #f0f0f0' }}>
              검증 기록 총 {records.length}건
            </p>
            {records.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#aaa', padding: '24px 0', textAlign: 'center' }}>검증 기록이 없습니다</p>
            ) : (
              records.map((record, i) => (
                <div key={record.id} style={{
                  display: 'flex', gap: '12px', alignItems: 'flex-start',
                  padding: '12px 0', borderBottom: i < records.length - 1 ? '0.5px solid #f0f0f0' : 'none',
                }}>
                  {record.image_url && (
                    <img src={record.image_url} alt="검증사진" style={{ width: '72px', height: '72px', objectFit: 'cover', borderRadius: '8px', flexShrink: 0 }} />
                  )}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                      <p style={{ fontSize: '13px', fontWeight: 500 }}>
                        {record.image_title || '제목 없음'} · {record.record_date}
                      </p>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        {record.is_match !== null && (
                          <span style={{
                            fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
                            background: record.is_match ? '#e8f5e9' : '#fce4ec',
                            color: record.is_match ? '#2e7d32' : '#c62828',
                          }}>
                            {record.is_match ? '일치' : '불일치'}
                          </span>
                        )}
                        <button
                          onClick={() => handleAnalyze(record.id)}
                          disabled={analyzingId === record.id}
                          style={{
                            fontSize: '11px', padding: '4px 10px', borderRadius: '8px',
                            border: '0.5px solid #1D9E75', background: 'white', cursor: 'pointer', color: '#1D9E75',
                            opacity: analyzingId === record.id ? 0.6 : 1,
                          }}
                        >
                          {analyzingId === record.id ? 'AI 분석 중...' : 'AI 분석'}
                        </button>
                      </div>
                    </div>
                    <p style={{ fontSize: '11px', color: '#888', marginBottom: '2px' }}>
                      사람: {SURFACE_STATUS_OPTIONS.find(s => s.value === record.observed_surface_status)?.label ?? record.observed_surface_status}
                      {record.ai_predicted_status && ` · AI: ${SURFACE_STATUS_OPTIONS.find(s => s.value === record.ai_predicted_status)?.label ?? record.ai_predicted_status}`}
                      {record.ai_confidence != null && ` · 신뢰도 ${record.ai_confidence}%`}
                    </p>
                    {record.note && <p style={{ fontSize: '11px', color: '#aaa' }}>{record.note}</p>}
                    <p style={{ fontSize: '10px', color: '#bbb', marginTop: '2px' }}>
                      {new Date(record.created_at).toLocaleString('ko-KR')}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  )
}