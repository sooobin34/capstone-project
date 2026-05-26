import { useState, useEffect } from 'react'
import MrvReportList from '../components/mrv/MrvReportList'
import { getFields, getMrvReports, createMrvReport, getValidationRecords, getValidationSummary, Field } from '../api/dashboard'

const SlideShow = ({ photos, onClickImage }: { photos: any[], onClickImage: (url: string) => void }) => {
  const [idx, setIdx] = useState(0)
  const photo = photos[idx]
  return (
    <div>
      <div style={{ position: 'relative' }}>
        <img
          src={photo.image_url}
          alt="검증사진"
          onClick={() => onClickImage(photo.image_url)}
          style={{ width: '100%', aspectRatio: '4/3', objectFit: 'cover', borderRadius: '8px', cursor: 'pointer', border: '0.5px solid #e0e0e0' }}
        />
        {photos.length > 1 && (
          <>
            <button onClick={() => setIdx(i => Math.max(0, i - 1))} disabled={idx === 0}
              style={{ position: 'absolute', left: '8px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.4)', color: 'white', border: 'none', borderRadius: '50%', width: '28px', height: '28px', cursor: 'pointer', fontSize: '14px', opacity: idx === 0 ? 0.3 : 1 }}>‹</button>
            <button onClick={() => setIdx(i => Math.min(photos.length - 1, i + 1))} disabled={idx === photos.length - 1}
              style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.4)', color: 'white', border: 'none', borderRadius: '50%', width: '28px', height: '28px', cursor: 'pointer', fontSize: '14px', opacity: idx === photos.length - 1 ? 0.3 : 1 }}>›</button>
          </>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
        <p style={{ fontSize: '11px', color: '#888' }}>{photo.record_date}</p>
        <div style={{ display: 'flex', gap: '4px' }}>
          {photos.map((_, i) => (
            <div key={i} onClick={() => setIdx(i)} style={{ width: '6px', height: '6px', borderRadius: '50%', background: i === idx ? '#1D9E75' : '#ccc', cursor: 'pointer' }} />
          ))}
        </div>
        {photo.is_match !== null && (
          <p style={{ fontSize: '11px', color: photo.is_match ? '#2e7d32' : '#c62828' }}>
            {photo.is_match ? '✓ 일치' : '✗ 불일치'}
          </p>
        )}
      </div>
    </div>
  )
}

export default function MrvPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [reports, setReports] = useState<any[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | ''>('')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [validationPhotos, setValidationPhotos] = useState<any[]>([])
  const [validationSummary, setValidationSummary] = useState<any>(null)
  const [modalImage, setModalImage] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([getFields(), getMrvReports()])
      .then(([fieldData, reportData]) => {
        setFields(fieldData)
        setReports(reportData)
      })
      .catch(e => console.error('조회 실패', e))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getMrvReports(selectedFieldId ? Number(selectedFieldId) : undefined)
      .then(setReports)
      .catch(e => console.error('MRV 조회 실패', e))

    if (selectedFieldId) {
      getValidationRecords(Number(selectedFieldId))
        .then(data => setValidationPhotos(data.slice(0, 3)))
        .catch(console.error)
      getValidationSummary(Number(selectedFieldId))
        .then(setValidationSummary)
        .catch(console.error)
    } else {
      setValidationPhotos([])
      setValidationSummary(null)
    }
  }, [selectedFieldId])

  const handleCreate = async () => {
    if (!selectedFieldId || !selectedMonth) {
      setCreateError('논과 월을 모두 선택해주세요.')
      return
    }
    setCreating(true)
    setCreateError('')
    try {
      await createMrvReport(Number(selectedFieldId), selectedMonth)
      const updated = await getMrvReports(selectedFieldId ? Number(selectedFieldId) : undefined)
      setReports(updated)
    } catch (e: any) {
      setCreateError(e?.response?.data?.message ?? '생성 실패. 해당 월의 일일 요약 데이터가 필요합니다.')
    } finally {
      setCreating(false)
    }
  }

  const filtered = reports
    .filter((r) => selectedMonth ? r.report_month === selectedMonth : true)
    .sort((a, b) => sortOrder === 'newest'
      ? b.report_month.localeCompare(a.report_month)
      : a.report_month.localeCompare(b.report_month)
    )

  return (
    <div style={{ padding: '16px', maxWidth: '1200px', margin: '0 auto', boxSizing: 'border-box' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '12px' }}>MRV</h2>
      <div style={{
        background: '#e8f4fd', border: '0.5px solid #b3d9f7', borderRadius: '8px',
        padding: '12px 16px', fontSize: '13px', color: '#1565c0', lineHeight: 1.6, marginBottom: '16px',
      }}>
        <strong style={{ fontWeight: 500 }}>MRV (측정·보고·검증)</strong>란 AWD 물관리 방식 적용 시 온실가스 감축량을 객관적으로 측정·기록·검증하는 절차입니다.
      </div>

{/* MRV 보고서 생성 흐름 */}
<div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
  <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>MRV 보고서 생성 흐름</p>
  <p style={{ fontSize: '11px', color: '#888', marginBottom: '16px' }}>센서 데이터 수집 → 일 요약 생성 → Validation 검증 수행 → MRV 보고서 생성</p>
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
    {[
      { num: '01', title: '센서 데이터 수집', desc: 'LoRa 게이트웨이가 논의 수위와 배터리 상태를 실시간으로 측정하여 서버에 저장합니다.' },
      { num: '02', title: '일일 요약 생성', desc: '하루 동안의 센서 데이터를 바탕으로 평균 수위와 논 상태를 자동으로 계산합니다.' },
      { num: '03', title: 'Validation 검증 수행', desc: '현장 사진을 업로드하고 사람의 판단과 AI 분석 결과를 비교하여 센서 정확도를 검증합니다.' },
      { num: '04', title: 'MRV 보고서 생성', desc: '수집된 센서 데이터와 검증 결과를 바탕으로 AWD 횟수, 탄소 감축량 등을 담은 공식 보고서를 생성합니다.' },
    ].map((step) => (
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
      {/* 통합 필터 + 생성 */}
      <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={selectedFieldId}
            onChange={(e) => setSelectedFieldId(e.target.value ? Number(e.target.value) : '')}
            style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', flex: '1 1 120px' }}
          >
            <option value="">논 선택</option>
            {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
          </select>

          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', flex: '1 1 120px' }}
          />

          <button
            onClick={handleCreate}
            disabled={creating}
            style={{
              fontSize: '13px', padding: '7px 16px', borderRadius: '8px',
              border: 'none', background: '#1D9E75', color: 'white',
              cursor: creating ? 'not-allowed' : 'pointer', fontWeight: 500,
              opacity: creating ? 0.7 : 1, whiteSpace: 'nowrap',
            }}
          >
            {creating ? '생성 중...' : '보고서 생성'}
          </button>

          <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
            {(['newest', 'oldest'] as const).map((order) => (
              <button
                key={order}
                onClick={() => setSortOrder(order)}
                style={{
                  fontSize: '12px', padding: '4px 10px', borderRadius: '20px',
                  border: '0.5px solid #ccc', cursor: 'pointer',
                  background: sortOrder === order ? '#f0f0f0' : 'white',
                  fontWeight: sortOrder === order ? 500 : 400,
                  color: sortOrder === order ? '#222' : '#888',
                  whiteSpace: 'nowrap',
                }}
              >
                {order === 'newest' ? '최신순' : '날짜순'}
              </button>
            ))}
          </div>
        </div>
        {createError && (
          <p style={{ fontSize: '12px', color: '#c62828', marginTop: '8px' }}>{createError}</p>
        )}
      </div>

      {/* 보고서 목록 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>보고서가 없습니다</div>
      ) : (
        <MrvReportList reports={filtered} onStatusChange={() => getMrvReports(selectedFieldId ? Number(selectedFieldId) : undefined).then(setReports)} />
      )}

      {/* 논 선택 시 하단 섹션 */}
      {selectedFieldId && filtered.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px', marginTop: '16px'
        }}>
          {/* AI 일치도 분석 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px' }}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>AI 일치도 분석</p>
            {validationSummary ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {[
                  { label: '전체 검증', value: `${validationSummary.total_validation_count ?? 0}건` },
                  { label: 'AI-센서 일치', value: `${validationSummary.ai_sensor_match_count ?? 0}건` },
                  { label: 'AI-센서 불일치', value: `${validationSummary.ai_sensor_mismatch_count ?? 0}건` },
                  { label: 'AI-센서 일치율', value: validationSummary.ai_sensor_accuracy != null ? `${validationSummary.ai_sensor_accuracy}%` : '-' },
                ].map((item) => (
                  <div key={item.label} style={{ background: '#f5f5f5', borderRadius: '8px', padding: '10px 12px' }}>
                    <p style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
                    <p style={{ fontSize: '16px', fontWeight: 500 }}>{item.value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '16px 0' }}>검증 데이터 없음</p>
            )}
          </div>

          {/* 검증 사진 슬라이드 */}
          <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px' }}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>최근 검증 사진</p>
            {validationPhotos.length > 0 ? (
              <SlideShow photos={validationPhotos} onClickImage={setModalImage} />
            ) : (
              <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '16px 0' }}>검증 사진 없음</p>
            )}
          </div>
        </div>
      )}

      {/* 사진 모달 */}
      {modalImage && (
        <div
          onClick={() => setModalImage(null)}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', zIndex: 1000, cursor: 'pointer',
          }}
        >
          <img src={modalImage} alt="크게보기" style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: '12px' }} />
        </div>
      )}
    </div>
  )
}
