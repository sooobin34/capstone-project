import { useState } from 'react'
import SensorChart from '../components/sensor/SensorChart'
import SensorStats from '../components/sensor/SensorStats'

const mockLabels = Array.from({ length: 25 }, (_, i) => `${i}시`)
const mockData = [3, 2.8, 2.5, 2.2, 1.8, 1.2, 0.5, -1, -3, -6, -9, -12, -14, -15.2, -14, -11, -7, -4, -1, 1, 2, 2.8, 3.2, 3.2, 3.2]

const riceFields = ['1번 논 (전주 A)', '2번 논 (전주 B)', '3번 논 (전주 C)']
const sensors = ['센서 A-1', '센서 A-2']
const timeRanges = ['최근 6시간', '최근 24시간', '최근 7일']

export default function SensorData() {
  const [selectedField, setSelectedField] = useState('')
  const [selectedSensor, setSelectedSensor] = useState('')
  const [selectedTime, setSelectedTime] = useState('')

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '20px' }}>센서 데이터</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {[
          { label: '논 선택', value: selectedField, options: riceFields, onChange: setSelectedField },
          { label: '센서 선택', value: selectedSensor, options: sensors, onChange: setSelectedSensor },
          { label: '시간 범위', value: selectedTime, options: timeRanges, onChange: setSelectedTime },
        ].map((sel) => (
          <select
            key={sel.label}
            value={sel.value}
            onChange={(e) => sel.onChange(e.target.value)}
            style={{
              fontSize: '13px',
              padding: '7px 12px',
              borderRadius: '8px',
              border: '0.5px solid #ccc',
              background: 'white',
              cursor: 'pointer',
            }}
          >
            <option value="">{sel.label}</option>
            {sel.options.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '12px' }}>
        <SensorChart data={mockData} labels={mockLabels} />
        <SensorStats
          currentLevel={3.2}
          sensorStatus="정상"
          avg={-2.1}
          max={5.0}
          min={-15.2}
          alarmCount={1}
        />
      </div>
    </div>
  )
}