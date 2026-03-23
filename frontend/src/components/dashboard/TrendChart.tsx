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

interface TrendChartProps {
  data: number[]
  labels: string[]
}

export default function TrendChart({ data, labels }: TrendChartProps) {
  const chartData = {
    labels,
    datasets: [
      {
        data,
        borderColor: '#1D9E75',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.4,
        fill: true,
        backgroundColor: 'rgba(29,158,117,0.08)',
      },
    ],
  }

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { font: { size: 10 }, maxTicksLimit: 6 } },
      y: {
        ticks: { font: { size: 10 }, callback: (v: number | string) => v + 'cm' },
        min: -20,
        max: 10,
      },
    },
  }

  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>수위 추이 (24시간)</p>
      <Line data={chartData} options={options} />
    </div>
  )
}