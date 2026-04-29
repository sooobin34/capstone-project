import { useState, useEffect } from 'react'
import MrvFilter from '../components/mrv/MrvFilter'
import MrvReportList from '../components/mrv/MrvReportList'
import { getFields, getMrvReports, Field } from '../api/dashboard'

export default function MrvPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [reports, setReports] = useState<any[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [selectedMonth, setSelectedMonth] = useState('')
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest')
  const [loading, setLoading] = useState(true)

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
    getMrvReports(selectedFieldId ?? undefined)
      .then(setReports)
      .catch(e => console.error('MRV 조회 실패', e))
  }, [selectedFieldId])

  const months = [...new Set(reports.map((r) => r.report_month))].sort()

  const filtered = reports
    .filter((r) => selectedMonth ? r.report_month === selectedMonth : true)
    .sort((a, b) => sortOrder === 'newest'
      ? b.report_month.localeCompare(a.report_month)
      : a.report_month.localeCompare(b.report_month)
    )

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '12px' }}>MRV</h2>
      <div style={{
        background: '#e8f4fd', border: '0.5px solid #b3d9f7', borderRadius: '8px',
        padding: '12px 16px', fontSize: '13px', color: '#1565c0', lineHeight: 1.6, marginBottom: '16px',
      }}>
        <strong style={{ fontWeight: 500 }}>MRV (측정·보고·검증)</strong>란 AWD 물관리 방식 적용 시 온실가스 감축량을 객관적으로 측정·기록·검증하는 절차입니다. 담수일수, 건조일수, AWD 횟수 등을 바탕으로 메탄 감축 실적을 산출하며, 탄소배출권 거래에 활용할 수 있는 공식 보고서를 생성합니다.
      </div>

      <MrvFilter
        selectedFieldId={selectedFieldId}
        selectedMonth={selectedMonth}
        sortOrder={sortOrder}
        onFieldIdChange={setSelectedFieldId}
        onMonthChange={setSelectedMonth}
        onSortChange={setSortOrder}
        fields={fields}
        months={months}
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>불러오는 중...</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#aaa', fontSize: '14px' }}>보고서가 없습니다</div>
      ) : (
        <MrvReportList reports={filtered} />
      )}
    </div>
  )
}