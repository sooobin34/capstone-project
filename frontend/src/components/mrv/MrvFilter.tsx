interface MrvFilterProps {
  selectedFieldId: number | null
  selectedMonth: string
  sortOrder: 'newest' | 'oldest'
  onFieldIdChange: (value: number | null) => void
  onMonthChange: (value: string) => void
  onSortChange: (value: 'newest' | 'oldest') => void
  fields: { id: number; field_name: string }[]
}

const months = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06', '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12']

export default function MrvFilter({
  selectedFieldId,
  selectedMonth,
  sortOrder,
  onFieldIdChange,
  onMonthChange,
  onSortChange,
  fields,
}: MrvFilterProps) {
  return (
    <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
      <select
        value={selectedFieldId ?? ''}
        onChange={(e) => onFieldIdChange(e.target.value ? Number(e.target.value) : null)}
        style={{
          fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
          border: '0.5px solid #ccc', background: 'white', cursor: 'pointer',
        }}
      >
        <option value="">논 선택</option>
        {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
      </select>

      <select
        value={selectedMonth}
        onChange={(e) => onMonthChange(e.target.value)}
        style={{
          fontSize: '13px', padding: '7px 12px', borderRadius: '8px',
          border: '0.5px solid #ccc', background: 'white', cursor: 'pointer',
        }}
      >
        <option value="">기간 선택</option>
        {months.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>

      <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
        {(['newest', 'oldest'] as const).map((order) => (
          <button
            key={order}
            onClick={() => onSortChange(order)}
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
  )
}

/*아래는 api 수정 전 버전
interface MrvFilterProps {
  selectedField: string
  selectedMonth: string
  sortOrder: 'newest' | 'oldest'
  onFieldChange: (value: string) => void
  onMonthChange: (value: string) => void
  onSortChange: (value: 'newest' | 'oldest') => void
}

const fields = ['1번 논 (전주 A)', '2번 논 (전주 B)', '3번 논 (전주 C)']
const months = ['2025년 전체', '2025년 6월', '2025년 5월', '2025년 4월']

export default function MrvFilter({
  selectedField,
  selectedMonth,
  sortOrder,
  onFieldChange,
  onMonthChange,
  onSortChange,
}: MrvFilterProps) {
  return (
    <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
      <select
        value={selectedField}
        onChange={(e) => onFieldChange(e.target.value)}
        style={{
          fontSize: '13px',
          padding: '7px 12px',
          borderRadius: '8px',
          border: '0.5px solid #ccc',
          background: 'white',
          cursor: 'pointer',
        }}
      >
        <option value="">논 선택</option>
        {fields.map((f) => <option key={f} value={f}>{f}</option>)}
      </select>

      <select
        value={selectedMonth}
        onChange={(e) => onMonthChange(e.target.value)}
        style={{
          fontSize: '13px',
          padding: '7px 12px',
          borderRadius: '8px',
          border: '0.5px solid #ccc',
          background: 'white',
          cursor: 'pointer',
        }}
      >
        <option value="">기간 선택</option>
        {months.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>

      <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
        {(['newest', 'oldest'] as const).map((order) => (
          <button
            key={order}
            onClick={() => onSortChange(order)}
            style={{
              fontSize: '12px',
              padding: '4px 10px',
              borderRadius: '20px',
              border: '0.5px solid #ccc',
              cursor: 'pointer',
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
  )
}*/