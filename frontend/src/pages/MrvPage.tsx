import { useEffect, useMemo, useState } from 'react'
import { useFieldContext } from '../App'
import {
  createMrvReport,
  downloadMrvExcel,
  downloadMrvPdf,
  Field,
  getFields,
  getMrvReports,
  getMrvReportView,
  getValidationRecords,
  getValidationSummary,
  MrvReportView,
} from '../api/dashboard'

interface MrvListItem {
  id: number
  field_id: number
  field_name: string
  report_month: string
  total_awd_cycles: number
  flood_days: number
  status: string
  created_at: string
}

type ValidationPhoto = {
  image_url: string
  record_date?: string
  is_match?: boolean | null
}

const cardStyle: React.CSSProperties = {
  background: '#fff',
  border: '0.5px solid #e0e0e0',
  borderRadius: '12px',
  padding: '16px',
}

const sectionCardStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #e6e6e6',
  borderRadius: 10,
  padding: 14,
}

const SlideShow = ({ photos, onClickImage }: { photos: ValidationPhoto[]; onClickImage: (url: string) => void }) => {
  const [idx, setIdx] = useState(0)
  const photo = photos[idx]

  return (
    <div>
      <div style={{ position: 'relative' }}>
        <img
          src={photo.image_url}
          alt="검증사진"
          onClick={() => onClickImage(photo.image_url)}
          style={{
            width: '100%',
            aspectRatio: '4/3',
            objectFit: 'cover',
            borderRadius: '8px',
            cursor: 'pointer',
            border: '0.5px solid #e0e0e0',
          }}
        />
        {photos.length > 1 && (
          <>
            <button
              type="button"
              onClick={() => setIdx((i) => Math.max(0, i - 1))}
              disabled={idx === 0}
              style={{
                position: 'absolute',
                left: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'rgba(0,0,0,0.4)',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '28px',
                height: '28px',
                cursor: 'pointer',
                fontSize: '14px',
                opacity: idx === 0 ? 0.3 : 1,
              }}
            >
              {'<'}
            </button>
            <button
              type="button"
              onClick={() => setIdx((i) => Math.min(photos.length - 1, i + 1))}
              disabled={idx === photos.length - 1}
              style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'rgba(0,0,0,0.4)',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '28px',
                height: '28px',
                cursor: 'pointer',
                fontSize: '14px',
                opacity: idx === photos.length - 1 ? 0.3 : 1,
              }}
            >
              {'>'}
            </button>
          </>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
        <p style={{ fontSize: '11px', color: '#888' }}>{photo.record_date ?? '-'}</p>
        <div style={{ display: 'flex', gap: '4px' }}>
          {photos.map((_, i) => (
            <div
              key={i}
              onClick={() => setIdx(i)}
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: i === idx ? '#1D9E75' : '#ccc',
                cursor: 'pointer',
              }}
            />
          ))}
        </div>
        {photo.is_match !== null && photo.is_match !== undefined ? (
          <p style={{ fontSize: '11px', color: photo.is_match ? '#2e7d32' : '#c62828' }}>
            {photo.is_match ? '일치' : '불일치'}
          </p>
        ) : (
          <p style={{ fontSize: '11px', color: '#888' }}>판단 없음</p>
        )}
      </div>
    </div>
  )
}

export default function MrvPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [reports, setReports] = useState<MrvListItem[]>([])
  const { selectedFieldId, setSelectedFieldId, setSelectedRegion } = useFieldContext()
  const [selectedMonth, setSelectedMonth] = useState('')
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null)
  const [selectedReportView, setSelectedReportView] = useState<MrvReportView | null>(null)
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest')
  const [validationPhotos, setValidationPhotos] = useState<ValidationPhoto[]>([])
  const [validationSummary, setValidationSummary] = useState<any>(null)
  const [modalImage, setModalImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [viewLoading, setViewLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  const loadReports = async (fieldId?: number) => {
    const data = await getMrvReports(fieldId)
    setReports(data)
    if (data.length === 0) {
      setSelectedReportId(null)
      setSelectedReportView(null)
      return
    }
    if (!selectedReportId || !data.some((r: MrvListItem) => r.id === selectedReportId)) {
      setSelectedReportId(data[0].id)
    }
  }

  useEffect(() => {
    Promise.all([getFields(), getMrvReports()])
      .then(([fieldData, reportData]) => {
        setFields(fieldData)
        setReports(reportData)
        if (reportData.length > 0) setSelectedReportId(reportData[0].id)
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadReports(selectedFieldId ?? undefined)
    if (selectedFieldId) {
      getValidationRecords(Number(selectedFieldId))
        .then((data) => setValidationPhotos((data ?? []).slice(0, 5)))
        .catch(() => setValidationPhotos([]))
      getValidationSummary(Number(selectedFieldId))
        .then(setValidationSummary)
        .catch(() => setValidationSummary(null))
    } else {
      setValidationPhotos([])
      setValidationSummary(null)
    }
  }, [selectedFieldId])

  useEffect(() => {
    if (!selectedReportId) {
      setSelectedReportView(null)
      return
    }
    setViewLoading(true)
    getMrvReportView(selectedReportId)
      .then(setSelectedReportView)
      .catch(() => setSelectedReportView(null))
      .finally(() => setViewLoading(false))
  }, [selectedReportId])

  const handleCreate = async () => {
    if (!selectedFieldId || !selectedMonth) {
      setCreateError('논과 월을 모두 선택해주세요.')
      return
    }
    setCreating(true)
    setCreateError('')
    try {
      await createMrvReport(selectedFieldId, selectedMonth)
      await loadReports(selectedFieldId)
    } catch (e: any) {
      setCreateError(e?.response?.data?.detail ?? e?.response?.data?.message ?? '보고서 생성에 실패했습니다.')
    } finally {
      setCreating(false)
    }
  }

  const handleFieldSelect = (value: string) => {
  const fieldId = value ? Number(value) : null
  setSelectedFieldId(fieldId)
  if (fieldId) {
    const field = fields.find(f => f.id === fieldId)
    if (field?.location_desc) setSelectedRegion(field.location_desc)
  }
}

  const filteredReports = useMemo(
    () =>
      reports
        .filter((r) => (selectedMonth ? r.report_month === selectedMonth : true))
        .sort((a, b) =>
          sortOrder === 'newest'
            ? b.report_month.localeCompare(a.report_month)
            : a.report_month.localeCompare(b.report_month),
        ),
    [reports, selectedMonth, sortOrder],
  )

  return (
    <div style={{ padding: '16px', maxWidth: '1200px', margin: '0 auto', boxSizing: 'border-box' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '12px' }}>MRV</h2>
      <div
        style={{
          background: '#e8f4fd',
          border: '0.5px solid #b3d9f7',
          borderRadius: '8px',
          padding: '12px 16px',
          fontSize: '13px',
          color: '#1565c0',
          lineHeight: 1.6,
          marginBottom: '16px',
        }}
      >
        <strong style={{ fontWeight: 500 }}>MRV (측정·보고·검증)</strong>란 AWD 물관리 방식 적용 시 온실가스 감축량을 객관적으로 측정·기록·검증하는 절차입니다.
      </div>

      <div style={{ ...cardStyle, marginBottom: '16px' }}>
        <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>MRV 보고서 생성 흐름</p>
        <p style={{ fontSize: '11px', color: '#888', marginBottom: '16px' }}>
          센서 데이터 수집 → 일 요약 생성 → Validation 검증 수행 → MRV 보고서 생성
        </p>
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

      <div style={{ ...cardStyle, marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={selectedFieldId ?? ''}
            onChange={(e) => handleFieldSelect(e.target.value)}
            style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', flex: '1 1 140px' }}
          >
            <option value="">논 선택</option>
            {fields.map((f) => (
              <option key={f.id} value={f.id}>
                {f.field_name}
              </option>
            ))}
          </select>

          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', flex: '1 1 140px' }}
          />

          <button
            type="button"
            onClick={handleCreate}
            disabled={creating}
            style={{
              fontSize: '13px',
              padding: '7px 16px',
              borderRadius: '8px',
              border: 'none',
              background: '#1D9E75',
              color: 'white',
              cursor: creating ? 'not-allowed' : 'pointer',
              fontWeight: 500,
              opacity: creating ? 0.7 : 1,
              whiteSpace: 'nowrap',
            }}
          >
            {creating ? '생성 중...' : '보고서 생성'}
          </button>

          <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
            {(['newest', 'oldest'] as const).map((order) => (
              <button
                key={order}
                type="button"
                onClick={() => setSortOrder(order)}
                style={{
                  fontSize: '12px',
                  padding: '4px 10px',
                  borderRadius: '20px',
                  border: '0.5px solid #ccc',
                  cursor: 'pointer',
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
        {createError && <p style={{ fontSize: '12px', color: '#c62828', marginTop: '8px' }}>{createError}</p>}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : filteredReports.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>보고서가 없습니다</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 14 }}>
          <div style={cardStyle}>
            <p style={{ margin: '0 0 10px', fontWeight: 700 }}>보고서 목록</p>
            <p style={{ fontSize: '12px', color: '#888', marginBottom: 10 }}>총 {filteredReports.length}건</p>
            {filteredReports.map((report) => (
              <button
                key={report.id}
                type="button"
                onClick={() => setSelectedReportId(report.id)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  border: selectedReportId === report.id ? '1px solid #1D9E75' : '1px solid #e8e8e8',
                  background: selectedReportId === report.id ? '#f1fbf7' : '#fff',
                  borderRadius: 8,
                  padding: 10,
                  marginBottom: 8,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontWeight: 700 }}>{report.field_name}</div>
                <div style={{ fontSize: 12, color: '#666' }}>{report.report_month}</div>
                <div style={{ fontSize: 12, color: '#666' }}>
                  AWD {report.total_awd_cycles}회 · 담수 {report.flood_days}일
                </div>
              </button>
            ))}
          </div>

          <div style={cardStyle}>
            <p style={{ margin: '0 0 12px', fontWeight: 700 }}>MRV 보고서 본문</p>
            {viewLoading ? (
              <p style={{ color: '#888' }}>보고서 본문 불러오는 중...</p>
            ) : !selectedReportView ? (
              <p style={{ color: '#888' }}>왼쪽에서 보고서를 선택하세요.</p>
            ) : (
              <div style={{ display: 'grid', gap: 12 }}>
                <section style={sectionCardStyle}>
                  <h4 style={{ margin: '0 0 8px' }}>1. 개요</h4>
                  <p style={{ margin: 0 }}>대상지: {selectedReportView.overview.field_name}</p>
                  <p style={{ margin: 0 }}>
                    분석기간: {selectedReportView.overview.period_start} ~ {selectedReportView.overview.period_end_exclusive}
                  </p>
                  <p style={{ margin: 0 }}>노드수: {selectedReportView.overview.node_count}</p>
                </section>

                <section style={sectionCardStyle}>
                  <h4 style={{ margin: '0 0 8px' }}>2. 주요 내용(결과 요약)</h4>
                  <p style={{ margin: 0 }}>AWD 사이클: {selectedReportView.summary.total_awd_cycles}회</p>
                  <p style={{ margin: 0 }}>담수일수: {selectedReportView.summary.flood_days}일</p>
                  <p style={{ margin: 0 }}>
                    탄소감축량: {selectedReportView.summary.carbon_reduction_kgco2eq ?? '-'} kgCO2-eq
                  </p>
                  <p style={{ margin: 0 }}>
                    월 평균 수위: {selectedReportView.summary.month_avg_inner_level_cm ?? '-'} cm
                  </p>
                </section>

                <section style={sectionCardStyle}>
                  <h4 style={{ margin: '0 0 8px' }}>3. 결과 분석(주차별 수위 변화)</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr>
                          {['주차', '기간', '평균', '최소', '최대', '상태 흐름'].map((h) => (
                            <th
                              key={h}
                              style={{ borderBottom: '1px solid #e0e0e0', textAlign: 'left', padding: 6 }}
                            >
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {selectedReportView.weekly_analysis.map((row) => (
                          <tr key={row.week_no}>
                            <td style={{ padding: 6 }}>{row.week_no}주</td>
                            <td style={{ padding: 6 }}>
                              {row.start_date} ~ {row.end_date}
                            </td>
                            <td style={{ padding: 6 }}>{row.avg_inner_level_cm ?? '-'}</td>
                            <td style={{ padding: 6 }}>{row.min_inner_level_cm ?? '-'}</td>
                            <td style={{ padding: 6 }}>{row.max_inner_level_cm ?? '-'}</td>
                            <td style={{ padding: 6 }}>{row.status_flow}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section style={sectionCardStyle}>
                  <h4 style={{ margin: '0 0 8px' }}>4. 현장 검증 결과</h4>
                  <p style={{ margin: 0 }}>검증 샘플: {selectedReportView.validation_results.sample_count}건</p>
                  <p style={{ margin: 0 }}>
                    센서-관찰 일치율: {selectedReportView.validation_results.sensor_observed_accuracy}%
                  </p>
                  <p style={{ margin: 0 }}>AI-센서 일치율: {selectedReportView.validation_results.ai_sensor_accuracy}%</p>
                </section>

                <section style={sectionCardStyle}>
                  <h4 style={{ margin: '0 0 8px' }}>5. 결론</h4>
                  {selectedReportView.conclusion.map((line) => (
                    <p key={line} style={{ margin: '0 0 4px' }}>
                      {line}
                    </p>
                  ))}
                </section>

                <div style={{ display: 'flex', gap: 8 }}>
                  <a
                    href={downloadMrvPdf(selectedReportView.report_id)}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      padding: '9px 12px',
                      border: '1px solid #d0d0d0',
                      borderRadius: 8,
                      textDecoration: 'none',
                      color: '#111',
                    }}
                  >
                    PDF 다운로드
                  </a>
                  <a
                    href={downloadMrvExcel(selectedReportView.report_id)}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      padding: '9px 12px',
                      border: '1px solid #d0d0d0',
                      borderRadius: 8,
                      textDecoration: 'none',
                      color: '#111',
                    }}
                  >
                    Excel 다운로드
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedFieldId && filteredReports.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '16px',
            marginTop: '16px',
          }}
        >
          <div style={cardStyle}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>AI 일치도 분석</p>
            {validationSummary ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {[
                  { label: '전체 검증', value: `${validationSummary.total_validation_count ?? 0}건` },
                  { label: 'AI-센서 일치', value: `${validationSummary.ai_sensor_match_count ?? 0}건` },
                  { label: 'AI-센서 불일치', value: `${validationSummary.ai_sensor_mismatch_count ?? 0}건` },
                  {
                    label: 'AI-센서 일치율',
                    value:
                      validationSummary.ai_sensor_accuracy != null
                        ? `${validationSummary.ai_sensor_accuracy}%`
                        : '-',
                  },
                ].map((item) => (
                  <div key={item.label} style={{ background: '#f5f5f5', borderRadius: '8px', padding: '10px 12px' }}>
                    <p style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
                    <p style={{ fontSize: '16px', fontWeight: 500 }}>{item.value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '16px 0' }}>
                검증 데이터 없음
              </p>
            )}
          </div>

          <div style={cardStyle}>
            <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px' }}>최근 검증 사진</p>
            {validationPhotos.length > 0 ? (
              <SlideShow photos={validationPhotos} onClickImage={setModalImage} />
            ) : (
              <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '16px 0' }}>
                검증 사진 없음
              </p>
            )}
          </div>
        </div>
      )}

      {modalImage && (
        <div
          onClick={() => setModalImage(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            cursor: 'pointer',
          }}
        >
          <img src={modalImage} alt="크게보기" style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: '12px' }} />
        </div>
      )}
    </div>
  )
}

