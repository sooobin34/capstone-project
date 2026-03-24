import { useState, useEffect } from 'react'
import MrvFilter from '../components/mrv/MrvFilter'
import MrvReportList from '../components/mrv/MrvReportList'
import { getFields, getMrvReports, Field } from '../api/dashboard'

const mockReports = [
  { id: 1, title: 'MRV 월간 보고서', report_month: '2025-06', field_id: 1, field_name: '전북대 1구역', total_awd_cycles: 3, flood_days: 28, status: '완료' as const },
  { id: 2, title: 'MRV 월간 보고서', report_month: '2025-05', field_id: 1, field_name: '전북대 1구역', total_awd_cycles: 2, flood_days: 26, status: '완료' as const },
  { id: 3, title: 'MRV 월간 보고서', report_month: '2025-06', field_id: 2, field_name: '전북 익산 테스트 논', total_awd_cycles: 2, flood_days: 22, status: '완료' as const },
]

export default function MrvPage() {
  const [fields, setFields] = useState<Field[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)
  const [selectedMonth, setSelectedMonth] = useState('')
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest')

  useEffect(() => {
    fetchFields()
  }, [])

  const fetchFields = async () => {
    try {
      const data = await getFields()
      setFields(data)
    } catch (e) {
      console.error('논 조회 실패', e)
    }
  }

  const filtered = mockReports
    .filter((r) => selectedFieldId ? r.field_id === selectedFieldId : true)
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
      />

      <MrvReportList reports={filtered} />
    </div>
  )
}

/* 아래는 api 수정 전 버전
import { useState } from 'react'
import MrvFilter from '../components/mrv/MrvFilter'
import MrvReportList from '../components/mrv/MrvReportList'

const mockReports = [
  { id: 1, title: 'MRV 월간 보고서 2025-06', date: '2025-06-30', field: '1번 논 (전주 A)', awdCount: 3, floodDays: 28, status: '완료' as const },
  { id: 2, title: 'MRV 월간 보고서 2025-05', date: '2025-05-31', field: '1번 논 (전주 A)', awdCount: 2, floodDays: 26, status: '완료' as const },
  { id: 3, title: 'MRV 월간 보고서 2025-04', date: '2025-04-30', field: '1번 논 (전주 A)', awdCount: 2, floodDays: 22, status: '완료' as const },
  { id: 4, title: 'MRV 월간 보고서 2025-06', date: '2025-06-30', field: '2번 논 (전주 B)', awdCount: 1, floodDays: 20, status: '완료' as const },
  { id: 5, title: 'MRV 월간 보고서 2025-06', date: '2025-06-30', field: '3번 논 (전주 C)', awdCount: 2, floodDays: 24, status: '작성중' as const },
]

export default function MrvPage() {
  const [selectedField, setSelectedField] = useState('')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest')

  const filtered = mockReports
    .filter((r) => selectedField ? r.field === selectedField : true)
    .filter((r) => selectedMonth ? r.title.includes(selectedMonth.replace('년 ', '-').replace('월', '')) : true)
    .sort((a, b) => sortOrder === 'newest'
      ? b.date.localeCompare(a.date)
      : a.date.localeCompare(b.date)
    )

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '12px' }}>MRV</h2>
      <div style={{
        background: '#e8f4fd',
        border: '0.5px solid #b3d9f7',
        borderRadius: '8px',
        padding: '12px 16px',
        fontSize: '13px',
        color: '#1565c0',
        lineHeight: 1.6,
        marginBottom: '16px',
      }}>
        <strong style={{ fontWeight: 500 }}>MRV (측정·보고·검증)</strong>란 AWD 물관리 방식 적용 시 온실가스 감축량을 객관적으로 측정·기록·검증하는 절차입니다. 담수일수, 건조일수, AWD 횟수 등을 바탕으로 메탄 감축 실적을 산출하며, 탄소배출권 거래에 활용할 수 있는 공식 보고서를 생성합니다.
      </div>

      <MrvFilter
        selectedField={selectedField}
        selectedMonth={selectedMonth}
        sortOrder={sortOrder}
        onFieldChange={setSelectedField}
        onMonthChange={setSelectedMonth}
        onSortChange={setSortOrder}
      />

      <MrvReportList reports={filtered} />
    </div>
  )
}*/