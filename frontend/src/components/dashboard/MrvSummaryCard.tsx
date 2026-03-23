interface MrvReport {
  id: number
  fieldName: string
  reportMonth: string
  awdCount: number
  carbonReduction: number
}

interface MrvSummaryCardProps {
  report: MrvReport | null
  onNavigate: () => void
}

export default function MrvSummaryCard({ report, onNavigate }: MrvSummaryCardProps) {
  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px', fontWeight: 500 }}>MRV 보고서 요약</p>
      {report ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
            {[
              { label: '논 이름', value: report.fieldName },
              { label: '보고 월', value: report.reportMonth },
              { label: 'AWD 횟수', value: `${report.awdCount}회` },
              { label: '탄소 감축량', value: `${report.carbonReduction}kg` },
            ].map((item) => (
              <div key={item.label} style={{ background: '#f5f5f5', borderRadius: '8px', padding: '10px 12px' }}>
                <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
                <p style={{ fontSize: '14px', fontWeight: 500 }}>{item.value}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <p style={{ fontSize: '13px', color: '#aaa', textAlign: 'center', padding: '16px 0' }}>보고서 없음</p>
      )}
      <button
        onClick={onNavigate}
        style={{
          width: '100%',
          padding: '8px',
          borderRadius: '8px',
          border: '0.5px solid #ccc',
          background: 'white',
          cursor: 'pointer',
          fontSize: '13px',
          color: '#1D9E75',
          fontWeight: 500,
        }}
      >
        MRV 보고서 보기 →
      </button>
    </div>
  )
}