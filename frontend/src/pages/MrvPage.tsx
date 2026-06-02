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

const STATUS_ORDER = ['OVERFLOODED', 'FLOODED', 'DRYING', 'DRY'] as const

const STATUS_LABEL: Record<string, string> = {
  OVERFLOODED: 'OVERFLOODED',
  FLOODED: 'FLOODED',
  DRYING: 'DRYING',
  DRY: 'DRY',
  NO_DATA: 'NO_DATA',
}

const STATUS_COLOR: Record<string, string> = {
  OVERFLOODED: '#1D9E75',
  FLOODED: '#1D9E75',
  DRYING: '#1D9E75',
  DRY: '#1D9E75',
}

const cardStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #d9e2e8',
  borderRadius: 8,
  padding: 16,
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  fontSize: 13,
  padding: '8px 10px',
  borderRadius: 6,
  border: '1px solid #cfd8df',
  background: 'white',
  color: '#111827',
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 11,
  color: '#667085',
  fontWeight: 700,
  marginBottom: 6,
}

const reportSectionStyle: React.CSSProperties = {
  border: '1px solid #d9e2e8',
  borderRadius: 8,
  padding: 14,
  background: '#fff',
}

function useIsMobile(maxWidth = 640) {
  const [isMobile, setIsMobile] = useState(() => (typeof window === 'undefined' ? false : window.innerWidth <= maxWidth))

  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth <= maxWidth)
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [maxWidth])

  return isMobile
}

function formatNumber(value: number | null | undefined, suffix = '') {
  if (value === null || value === undefined) return '-'
  const text = Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/\.00$/, '')
  return `${text}${suffix}`
}

function formatDelta(value: number | null | undefined) {
  if (value === null || value === undefined) return '-'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}`
}

function deltaColor(value: number | null | undefined) {
  if (value === null || value === undefined || value === 0) return '#374151'
  return value > 0 ? '#1565c0' : '#c2410c'
}

function formatStatusFlow(flow: string | null | undefined) {
  if (!flow) return '-'
  return flow
    .replace(/->/g, '→')
    .split('→')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((status) => STATUS_LABEL[status] ?? status)
    .join(' → ')
}

function normalizeConclusionLine(line: string) {
  const awdMatch = line.match(/^(\d+)\s+AWD cycles were detected during the reporting period\./)
  if (awdMatch) return `보고 기간 중 ${awdMatch[1]}회의 AWD 사이클이 관측되었다.`

  const carbonMatch = line.match(/^Estimated carbon reduction is\s+(.+?)\s+kgCO2-eq\./)
  if (carbonMatch) return `추정 탄소 감축량은 약 ${carbonMatch[1]} kgCO2-eq이다.`

  const legacyConclusionMap: Record<string, string> = {
    'No complete AWD cycle was observed in this period.':
      '보고 기간 중 완결된 AWD 사이클은 관측되지 않았다.',
    'Consider extending monitoring duration or increasing dry-down intervals for clearer AWD transitions.':
      '향후 모니터링 기간 확대와 물관리 조건 보완을 통해 AWD 전환 흐름을 더 명확히 확인할 필요가 있다.',
  }
  return legacyConclusionMap[line] ?? line
}

function MatchBadge({ value }: { value: boolean | null | undefined }) {
  if (value === true) return <span style={{ color: '#1D9E75', fontWeight: 700, fontSize: 11 }}>일치</span>
  if (value === false) return <span style={{ color: '#ef4444', fontWeight: 700, fontSize: 11 }}>불일치</span>
  return <span style={{ color: '#98a2b3', fontSize: 11 }}>판정 불가</span>
}

function SectionHeader({ num, title }: { num: string; title: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <div
        style={{
          width: 22,
          height: 22,
          display: 'grid',
          placeItems: 'center',
          background: '#0F6B4F',
          color: 'white',
          fontSize: 11,
          fontWeight: 800,
          borderRadius: 4,
          flexShrink: 0,
        }}
      >
        {num}
      </div>
      <span style={{ fontSize: 14, fontWeight: 800, color: '#111827' }}>{title}</span>
    </div>
  )
}

function ReportDocument({ view, onClickImage, isMobile }: { view: MrvReportView; onClickImage: (url: string) => void; isMobile: boolean }) {
  const { overview, summary, weekly_analysis, validation_results, conclusion } = view
  const statusCounts = summary.status_counts
  const maxDays = Math.max(1, ...STATUS_ORDER.map((status) => statusCounts[status] ?? 0))
  const dominantStatus = STATUS_LABEL[summary.dominant_status] ?? summary.dominant_status ?? '-'

  const kpis = [
    { label: 'AWD 사이클', value: formatNumber(summary.total_awd_cycles, '회'), sub: '관측된 물관리 전환' },
    { label: 'Flood days', value: formatNumber(summary.flood_days, '일'), sub: 'FLOODED + OVERFLOODED' },
    { label: '월 평균 수위', value: formatNumber(summary.month_avg_inner_level_cm, 'cm'), sub: '내부 수위 평균' },
    { label: '탄소감축량', value: formatNumber(summary.carbon_reduction_kgco2eq, ' kgCO2-eq'), sub: 'AWD 기반 추정값' },
  ]

  const representativeImages = validation_results.rows.filter((row) => row.image_url).slice(0, 3)
  const validationRows = [
    ['검증 샘플', `${validation_results.sample_count}건`],
    ['센서-관찰 일치/불일치', `${validation_results.sensor_observed_match_count}건 / ${validation_results.sensor_observed_mismatch_count}건`],
    ['센서-관찰 일치율', formatNumber(validation_results.sensor_observed_accuracy, '%')],
    ['AI-센서 일치/불일치', `${validation_results.ai_sensor_match_count}건 / ${validation_results.ai_sensor_mismatch_count}건`],
    ['AI-센서 일치율', formatNumber(validation_results.ai_sensor_accuracy, '%')],
    ['비고', validation_results.note && validation_results.note !== '별도 비고 없음' ? validation_results.note : '-'],
  ]
  const downloadLinkStyle: React.CSSProperties = {
    padding: isMobile ? '10px 11px' : '8px 11px',
    border: '1px solid rgba(255,255,255,0.55)',
    borderRadius: 6,
    color: 'white',
    textDecoration: 'none',
    fontSize: 12,
    fontWeight: 700,
    background: 'rgba(255,255,255,0.1)',
    textAlign: 'center',
    boxSizing: 'border-box',
    flex: isMobile ? '1 1 0' : '0 0 auto',
  }

  return (
    <div
      style={{
        border: '1px solid #cfd8df',
        borderRadius: 8,
        overflow: 'hidden',
        background: '#fff',
        fontSize: 13,
        boxShadow: isMobile ? '0 8px 22px rgba(16, 24, 40, 0.07)' : '0 14px 35px rgba(16, 24, 40, 0.08)',
      }}
    >
      <div
        style={{
          background: '#0F6B4F',
          color: 'white',
          padding: isMobile ? '14px 14px' : '18px 22px',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 14,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ minWidth: 0, flex: '1 1 220px' }}>
          <div style={{ fontSize: isMobile ? 16 : 18, fontWeight: 800, letterSpacing: 0 }}>AquaPaddy MRV 보고서</div>
          <div style={{ fontSize: 12, opacity: 0.9, marginTop: 5, lineHeight: 1.5 }}>
            {overview.field_name} · 분석기간 {overview.period_start} ~ {overview.period_end_exclusive} · 보고월 {overview.report_month}
          </div>
          <div
            style={{
              display: 'inline-flex',
              marginTop: 10,
              padding: '4px 8px',
              borderRadius: 4,
              background: 'rgba(255,255,255,0.14)',
              border: '1px solid rgba(255,255,255,0.25)',
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            탄소배출권 플랫폼 기반 구축
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', width: isMobile ? '100%' : 'auto' }}>
          <a
            href={downloadMrvPdf(view.report_id)}
            target="_blank"
            rel="noreferrer"
            style={downloadLinkStyle}
          >
            PDF 다운로드
          </a>
          <a
            href={downloadMrvExcel(view.report_id)}
            target="_blank"
            rel="noreferrer"
            style={downloadLinkStyle}
          >
            Excel 다운로드
          </a>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: 10,
          padding: isMobile ? '12px 14px' : '12px 22px',
          borderBottom: '1px solid #e5edf2',
          background: '#f7f9fb',
        }}
      >
        {[
          ['연구 범위', '탄소배출권 거래 전 단계의 MRV 기반 구축'],
          ['MRV 구성', '수위 실측·현장 검증·기록·보고 문서화'],
          ['확장 방향', '제도 연계 및 거래 단계 검토'],
        ].map(([label, value]) => (
          <div key={label}>
            <div style={{ fontSize: 10, color: '#667085', fontWeight: 800, marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 12, color: '#111827', fontWeight: 700, lineHeight: 1.45 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, minmax(0, 1fr))' : 'repeat(auto-fit, minmax(135px, 1fr))', borderBottom: '1px solid #e5edf2' }}>
        {kpis.map((kpi, index) => (
          <div
            key={kpi.label}
            style={{
              padding: isMobile ? '12px 10px' : '14px 16px',
              borderRight: isMobile ? (index % 2 === 0 ? '1px solid #e5edf2' : 'none') : index < kpis.length - 1 ? '1px solid #e5edf2' : 'none',
              borderTop: isMobile && index > 1 ? '1px solid #e5edf2' : 'none',
              background: index % 2 === 0 ? '#f8faf9' : '#fbfcfe',
              minHeight: isMobile ? 70 : 76,
            }}
          >
            <div style={{ fontSize: 11, color: '#667085', marginBottom: 5, fontWeight: 700 }}>{kpi.label}</div>
            <div style={{ fontSize: isMobile ? 16 : 19, fontWeight: 800, color: '#0F6B4F', lineHeight: 1.15, wordBreak: 'break-word' }}>{kpi.value}</div>
            <div style={{ fontSize: 10, color: '#98a2b3', marginTop: 4 }}>{kpi.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ padding: isMobile ? '14px 12px' : '20px 22px', display: 'grid', gap: 16, background: '#fbfcfe' }}>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
          <section style={reportSectionStyle}>
            <SectionHeader num="1" title="개요" />
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <tbody>
                {[
                  ['대상지', overview.field_name],
                  ['위치', overview.field_location_desc || '-'],
                  ['분석기간', `${overview.period_start} ~ ${overview.period_end_exclusive}`],
                  ['IoT 노드 수', `${overview.node_count}개`],
                  ['보고 상태', overview.status === 'COMPLETED' ? '완료' : '진행 중'],
                  ['연구 단계', 'MRV 기반 구축 및 보고 문서화'],
                ].map(([label, value]) => (
                  <tr key={label}>
                    <td
                      style={{
                        padding: '8px 10px',
                        background: '#F2F7F5',
                        fontWeight: 800,
                        width: isMobile ? 92 : '30%',
                        border: '1px solid #d9e2e8',
                        color: '#111827',
                      }}
                    >
                      {label}
                    </td>
                    <td style={{ padding: '8px 10px', border: '1px solid #d9e2e8', color: '#344054' }}>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section style={reportSectionStyle}>
            <SectionHeader num="2" title="주요 내용 (결과 요약)" />
            <div style={{ display: 'grid', gap: 12 }}>
              <div>
                <div style={{ fontSize: 12, color: '#344054', fontWeight: 800, marginBottom: 10 }}>상태별 관측 일수</div>
                <div style={{ display: 'grid', gap: 8 }}>
                  {STATUS_ORDER.map((status) => {
                    const days = statusCounts[status] ?? 0
                    const pct = Math.round((days / maxDays) * 100)
                    return (
                      <div key={status} style={{ display: 'grid', gridTemplateColumns: isMobile ? '92px 1fr 34px' : '72px 1fr 42px', alignItems: 'center', gap: isMobile ? 7 : 10 }}>
                        <span style={{ fontSize: isMobile ? 10 : 11, color: '#475467', fontWeight: 700 }}>{STATUS_LABEL[status]}</span>
                        <div style={{ background: '#eef2f5', borderRadius: 4, height: 12, overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${pct}%`,
                              height: '100%',
                              background: STATUS_COLOR[status],
                              minWidth: days > 0 ? 4 : 0,
                            }}
                          />
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 800, color: '#111827', textAlign: 'right' }}>{days}일</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, minmax(0, 1fr))', gap: 8, paddingTop: 2 }}>
                {[
                  ['우세 상태', dominantStatus],
                  ['검증 방법', validation_results.validation_method || '-'],
                  ['검증 샘플', `${validation_results.sample_count}건`],
                  ['센서-관찰', formatNumber(validation_results.sensor_observed_accuracy, '%')],
                ].map(([label, value]) => (
                  <div key={label} style={{ background: '#F7F9FB', border: '1px solid #e5edf2', borderRadius: 6, padding: '8px 10px' }}>
                    <div style={{ color: '#667085', fontSize: 10, fontWeight: 800, marginBottom: 3 }}>{label}</div>
                    <div style={{ color: '#111827', fontSize: 12, fontWeight: 800 }}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        <section style={reportSectionStyle}>
          <SectionHeader num="3" title="결과 분석" />

          <p style={{ fontSize: 12, fontWeight: 800, color: '#344054', marginBottom: 7 }}>주차별 수위 변화</p>
          {isMobile ? (
            <div style={{ display: 'grid', gap: 9, marginBottom: 16 }}>
              {weekly_analysis.length === 0 ? (
                <div style={{ padding: 16, textAlign: 'center', color: '#98a2b3', border: '1px solid #d9e2e8', borderRadius: 8 }}>데이터 없음</div>
              ) : (
                weekly_analysis.map((row) => (
                  <div key={row.week_no} style={{ border: '1px solid #b7c7c0', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '9px 10px', background: '#EAF4EF', borderBottom: '1px solid #b7c7c0' }}>
                      <span style={{ fontSize: 12, fontWeight: 900, color: '#111827' }}>{row.week_no}주</span>
                      <span style={{ fontSize: 12, fontWeight: 900, color: deltaColor(row.change_inner_level_cm) }}>{formatDelta(row.change_inner_level_cm)}cm</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
                      {[
                        ['평균', formatNumber(row.avg_inner_level_cm, 'cm')],
                        ['최소', formatNumber(row.min_inner_level_cm, 'cm')],
                        ['최대', formatNumber(row.max_inner_level_cm, 'cm')],
                        ['변화', `${formatDelta(row.change_inner_level_cm)}cm`],
                      ].map(([label, value], index) => (
                        <div key={label} style={{ padding: '8px 10px', borderTop: index > 1 ? '1px solid #e5edf2' : 'none', borderRight: index % 2 === 0 ? '1px solid #e5edf2' : 'none' }}>
                          <div style={{ fontSize: 10, color: '#667085', fontWeight: 800, marginBottom: 3 }}>{label}</div>
                          <div style={{ fontSize: 12, color: '#111827', fontWeight: 800 }}>{value}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ padding: '9px 10px', borderTop: '1px solid #e5edf2' }}>
                      <div style={{ fontSize: 10, color: '#667085', fontWeight: 800, marginBottom: 4 }}>상태 흐름</div>
                      <div style={{ fontSize: 12, color: '#344054', fontWeight: 700, lineHeight: 1.5, wordBreak: 'break-word' }}>{formatStatusFlow(row.status_flow)}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div style={{ overflowX: 'auto', marginBottom: 16, border: '1px solid #b7c7c0', borderRadius: 8 }}>
              <table style={{ width: '100%', minWidth: 760, borderCollapse: 'collapse', fontSize: 11 }}>
                <thead>
                  <tr style={{ background: '#EAF4EF' }}>
                    {['주차', '평균(cm)', '변화(cm)', '최소(cm)', '최대(cm)', '상태 흐름'].map((header) => (
                      <th
                        key={header}
                        style={{
                          padding: '9px 8px',
                          borderBottom: '1px solid #9bbcae',
                          borderRight: '1px solid #b7c7c0',
                          fontWeight: 800,
                          color: '#111827',
                          textAlign: 'center',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {weekly_analysis.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ padding: 16, textAlign: 'center', color: '#98a2b3' }}>
                        데이터 없음
                      </td>
                    </tr>
                  ) : (
                    weekly_analysis.map((row, index) => (
                      <tr key={row.week_no} style={{ background: index % 2 === 0 ? '#ffffff' : '#f8faf9' }}>
                        <td style={{ padding: '9px 8px', borderTop: '1px solid #c2cdc8', borderRight: '1px solid #c2cdc8', textAlign: 'center', fontWeight: 800 }}>
                          {row.week_no}주
                        </td>
                        <td style={{ padding: '9px 8px', borderTop: '1px solid #c2cdc8', borderRight: '1px solid #c2cdc8', textAlign: 'center' }}>
                          {formatNumber(row.avg_inner_level_cm)}
                        </td>
                        <td
                          style={{
                            padding: '9px 8px',
                            borderTop: '1px solid #c2cdc8',
                            borderRight: '1px solid #c2cdc8',
                            textAlign: 'center',
                            fontWeight: 800,
                            color: deltaColor(row.change_inner_level_cm),
                          }}
                        >
                          {formatDelta(row.change_inner_level_cm)}
                        </td>
                        <td style={{ padding: '9px 8px', borderTop: '1px solid #c2cdc8', borderRight: '1px solid #c2cdc8', textAlign: 'center' }}>
                          {formatNumber(row.min_inner_level_cm)}
                        </td>
                        <td style={{ padding: '9px 8px', borderTop: '1px solid #c2cdc8', borderRight: '1px solid #c2cdc8', textAlign: 'center' }}>
                          {formatNumber(row.max_inner_level_cm)}
                        </td>
                        <td style={{ padding: '9px 10px', borderTop: '1px solid #c2cdc8', color: '#344054', fontWeight: 600 }}>
                          {formatStatusFlow(row.status_flow)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          <p style={{ fontSize: 12, fontWeight: 800, color: '#344054', marginBottom: 7 }}>현장 검증 결과</p>
          {isMobile ? (
            <div style={{ display: 'grid', gap: 8, marginBottom: representativeImages.length > 0 ? 14 : 0 }}>
              {validationRows.map(([label, value]) => (
                <div key={label} style={{ border: '1px solid #cfd8df', borderRadius: 7, overflow: 'hidden', background: '#fff' }}>
                  <div style={{ padding: '7px 10px', background: '#f7f9fb', color: '#344054', fontSize: 10, fontWeight: 900 }}>{label}</div>
                  <div style={{ padding: '8px 10px', color: '#111827', fontSize: 12, fontWeight: 700, lineHeight: 1.5 }}>{value}</div>
                </div>
              ))}
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, marginBottom: representativeImages.length > 0 ? 14 : 0 }}>
              <tbody>
                {validationRows.map(([label, value]) => (
                  <tr key={label}>
                    <td style={{ padding: '8px 10px', border: '1px solid #cfd8df', background: '#f7f9fb', width: '30%', fontWeight: 800, color: '#344054' }}>{label}</td>
                    <td style={{ padding: '8px 10px', border: '1px solid #cfd8df', color: '#111827' }}>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {representativeImages.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: '#667085', marginBottom: 7, fontWeight: 700 }}>대표 검증 사진</p>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
                {representativeImages.map((row) => (
                  <div key={row.record_id} style={{ border: '1px solid #d9e2e8', borderRadius: 8, padding: 8, background: '#fbfcfe' }}>
                    <img
                      src={row.image_url!}
                      alt="검증"
                      onClick={() => onClickImage(row.image_url!)}
                      style={{ width: '100%', aspectRatio: '4/3', objectFit: 'cover', borderRadius: 6, border: '1px solid #e5edf2', cursor: 'pointer' }}
                    />
                    <div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 10, color: '#667085' }}>{row.record_date}</span>
                      <MatchBadge value={row.ai_sensor_match} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        <section style={reportSectionStyle}>
          <SectionHeader num="4" title="결론" />
          <div style={{ background: '#F2F7F5', borderLeft: '4px solid #0F6B4F', borderRadius: 6, padding: '12px 14px' }}>
            {conclusion.map((line, index) => (
              <p key={`${index}-${line}`} style={{ margin: index === 0 ? 0 : '7px 0 0', fontSize: 12, color: '#1a3d2f', lineHeight: 1.65 }}>
                {normalizeConclusionLine(line)}
              </p>
            ))}
          </div>
        </section>
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
  const [modalImage, setModalImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [viewLoading, setViewLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const isMobile = useIsMobile()

  const loadReports = async (fieldId?: number) => {
    const data = await getMrvReports(fieldId)
    setReports(data)
    if (data.length === 0) {
      setSelectedReportId(null)
      setSelectedReportView(null)
      return
    }
    if (!selectedReportId || !data.some((report: MrvListItem) => report.id === selectedReportId)) {
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
    if (loading) return
    loadReports(selectedFieldId ?? undefined)
  }, [selectedFieldId, loading])

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
      const created = await createMrvReport(selectedFieldId, selectedMonth)
      await loadReports(selectedFieldId)
      if (created?.id) setSelectedReportId(created.id)
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
      const field = fields.find((f) => f.id === fieldId)
      if (field?.location_desc) setSelectedRegion(field.location_desc)
    }
  }

  const filteredReports = useMemo(
    () =>
      reports
        .filter((report) => (selectedMonth ? report.report_month === selectedMonth : true))
        .sort((a, b) => b.report_month.localeCompare(a.report_month)),
    [reports, selectedMonth],
  )

  useEffect(() => {
    if (loading) return
    if (filteredReports.length === 0) {
      setSelectedReportId(null)
      return
    }
    if (!selectedReportId || !filteredReports.some((report) => report.id === selectedReportId)) {
      setSelectedReportId(filteredReports[0].id)
    }
  }, [filteredReports, loading, selectedReportId])

  return (
    <div style={{ padding: isMobile ? 10 : 16, maxWidth: 1200, margin: '0 auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ fontSize: isMobile ? 18 : 19, fontWeight: 800, margin: 0, color: '#111827' }}>MRV 보고서</h2>
          <p style={{ fontSize: 12, color: '#667085', margin: '4px 0 0' }}>탄소배출권 플랫폼 기반 구축을 위한 실측·검증·기록 보고</p>
        </div>
      </div>

      <div style={{ ...cardStyle, marginBottom: 14, padding: isMobile ? 12 : cardStyle.padding }}>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12, alignItems: 'end' }}>
          <label>
            <span style={labelStyle}>대상 논</span>
            <select
              value={selectedFieldId ?? ''}
              onChange={(event) => handleFieldSelect(event.target.value)}
              style={inputStyle}
            >
              <option value="">전체 논</option>
              {fields.map((field) => (
                <option key={field.id} value={field.id}>
                  {field.field_name}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span style={labelStyle}>보고월</span>
            <input type="month" value={selectedMonth} onChange={(event) => setSelectedMonth(event.target.value)} style={inputStyle} />
          </label>

          <button
            type="button"
            onClick={handleCreate}
            disabled={creating}
            style={{
              fontSize: 13,
              padding: '9px 14px',
              borderRadius: 6,
              border: 'none',
              background: '#1D9E75',
              color: 'white',
              cursor: creating ? 'not-allowed' : 'pointer',
              fontWeight: 800,
              opacity: creating ? 0.7 : 1,
              minHeight: 36,
              width: isMobile ? '100%' : 'auto',
            }}
          >
            {creating ? '생성 중...' : '보고서 생성'}
          </button>

          <div style={{ fontSize: 11, color: '#667085', lineHeight: 1.45, alignSelf: 'center' }}>
            보고서는 최신 보고월 기준으로 자동 표시됩니다.
          </div>
        </div>
        {createError && <p style={{ fontSize: 12, color: '#c62828', margin: '9px 0 0', fontWeight: 700 }}>{createError}</p>}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#98a2b3', fontSize: 14 }}>불러오는 중...</div>
      ) : filteredReports.length === 0 ? (
        <div style={{ ...cardStyle, textAlign: 'center', padding: 42, color: '#98a2b3', fontSize: 14 }}>보고서가 없습니다</div>
      ) : (
        <div>
          {filteredReports.length > 1 && (
            <div
              style={{
                ...cardStyle,
                marginBottom: 12,
                display: 'flex',
                alignItems: isMobile ? 'stretch' : 'center',
                gap: 10,
                flexWrap: 'wrap',
                flexDirection: isMobile ? 'column' : 'row',
                padding: 12,
              }}
            >
              <span style={{ fontSize: 12, color: '#667085', fontWeight: 800 }}>보고서 선택</span>
              <select
                value={selectedReportId ?? ''}
                onChange={(event) => setSelectedReportId(event.target.value ? Number(event.target.value) : null)}
                style={{ ...inputStyle, width: isMobile ? '100%' : 'auto', minWidth: isMobile ? 0 : 220 }}
              >
                {filteredReports.map((report) => (
                  <option key={report.id} value={report.id}>
                    {report.field_name} · {report.report_month}
                  </option>
                ))}
              </select>
              <span style={{ fontSize: 11, color: '#98a2b3', marginLeft: isMobile ? 0 : 'auto', fontWeight: 700 }}>총 {filteredReports.length}건</span>
            </div>
          )}

          {viewLoading ? (
            <div style={{ textAlign: 'center', padding: 48, color: '#98a2b3', fontSize: 14 }}>보고서 불러오는 중...</div>
          ) : !selectedReportView ? (
            <div style={{ ...cardStyle, textAlign: 'center', padding: 42, color: '#98a2b3', fontSize: 14 }}>보고서를 선택하세요.</div>
          ) : (
            <ReportDocument view={selectedReportView} onClickImage={setModalImage} isMobile={isMobile} />
          )}
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
            background: 'rgba(0,0,0,0.72)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            cursor: 'pointer',
            padding: 18,
          }}
        >
          <img src={modalImage} alt="크게보기" style={{ maxWidth: '92vw', maxHeight: '90vh', borderRadius: 8 }} />
        </div>
      )}
    </div>
  )
}
