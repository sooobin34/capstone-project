interface MrvFilterProps {
  selectedFieldId: number | null
  selectedMonth: string
  sortOrder: 'newest' | 'oldest'
  onFieldIdChange: (value: number | null) => void
  onMonthChange: (value: string) => void
  onSortChange: (value: 'newest' | 'oldest') => void
  fields: { id: number; field_name: string }[]
  months: string[]  // ← 추가
}

export default function MrvFilter({
  selectedFieldId,
  selectedMonth,
  sortOrder,
  onFieldIdChange,
  onMonthChange,
  onSortChange,
  fields,
  months,  // ← 추가
}: MrvFilterProps) {
  return (
    <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
      <select
        value={selectedFieldId ?? ''}
        onChange={(e) => onFieldIdChange(e.target.value ? Number(e.target.value) : null)}
        style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
      >
        <option value="">논 선택</option>
        {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
      </select>

      <select
        value={selectedMonth}
        onChange={(e) => onMonthChange(e.target.value)}
        style={{ fontSize: '13px', padding: '7px 12px', borderRadius: '8px', border: '0.5px solid #ccc', background: 'white', cursor: 'pointer' }}
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