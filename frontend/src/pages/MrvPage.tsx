import { useState, useEffect } from 'react'
import MrvReportList from '../components/mrv/MrvReportList'
import { getFields, getMrvReports, createMrvReport, Field } from '../api/dashboard'

export default function MrvPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [reports, setReports] = useState<any[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | ''>('')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

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
        <strong style={{ fontWeight: 500 }}>MRV (측정·보고·검증)</strong>란 AWD 물관리 방식 적용 시 온실가스 감축량을 객관적으로 측정·기록·검증하는 절차입니다.
      </div>

      {/* 통합 필터 + 생성 */}
      <div style={{
        background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px',
        padding: '16px', marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={selectedFieldId}
            onChange={(e) => setSelectedFieldId(e.target.value ? Number(e.target.value) : '')}
            style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white' }}
          >
            <option value="">논 선택</option>
            {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
          </select>

          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white' }}
          />

          <button
            onClick={handleCreate}
            disabled={creating}
            style={{
              fontSize: '13px', padding: '7px 16px', borderRadius: '8px',
              border: 'none', background: '#1D9E75', color: 'white',
              cursor: creating ? 'not-allowed' : 'pointer', fontWeight: 500,
              opacity: creating ? 0.7 : 1,
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