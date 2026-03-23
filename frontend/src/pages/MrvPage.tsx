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
}