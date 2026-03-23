import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

interface SensorChartProps {
  data: number[]
  labels: string[]
}

export default function SensorChart({ data, labels }: SensorChartProps) {
  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>수위 변화 (cm)</p>
      <Line
        data={{
          labels,
          datasets: [
            {
              data,
              borderColor: '#1D9E75',
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.4,
              fill: true,
              backgroundColor: 'rgba(29,158,117,0.08)',
              label: '수위',
            },
            {
              data: Array(labels.length).fill(-15),
              borderColor: '#E24B4A',
              borderWidth: 1,
              borderDash: [5, 4],
              pointRadius: 0,
              label: '임계치',
              fill: false,
            },
          ],
        }}
        options={{
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
            y: {
              ticks: { font: { size: 10 }, callback: (v) => v + 'cm' },
              min: -20,
              max: 10,
            },
          },
        }}
      />
      <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '11px', color: '#888' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '20px', height: '2px', background: '#1D9E75', display: 'inline-block', borderRadius: '2px' }} />
          수위
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '20px', height: '0', border: '1px dashed #E24B4A', display: 'inline-block' }} />
          임계치 (−15cm)
        </span>
      </div>
    </div>
  )
}