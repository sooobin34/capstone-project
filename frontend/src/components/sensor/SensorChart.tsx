import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler, Legend)

interface SensorData {
  nodeId: number
  label: string
  data: number[]
}

interface SensorChartProps {
  datasets: SensorData[]
  labels: string[]
  singleMode: boolean
}

const LINE_COLORS = ['#1D9E75', '#378ADD', '#BA7517', '#7F77DD', '#D85A30']

export default function SensorChart({ datasets, labels, singleMode }: SensorChartProps) {
  const chartDatasets = [
    ...datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      borderColor: LINE_COLORS[i % LINE_COLORS.length],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.4,
      fill: singleMode ? true : false,
      backgroundColor: singleMode ? 'rgba(29,158,117,0.08)' : 'transparent',
    })),
    {
      label: '임계치 (-15cm)',
      data: Array(labels.length).fill(-15),
      borderColor: '#E24B4A',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0,
      fill: false,
      backgroundColor: 'transparent',
      borderDash: [5, 5],
    },
  ]

  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>
        수위 변화 (cm) · {singleMode ? '단일 기기' : '전체 기기 비교'}
      </p>
      <Line
        data={{ labels, datasets: chartDatasets }}
        options={{
          responsive: true,
          plugins: {
            legend: {
              display: true,
              position: 'bottom' as const,
              labels: { font: { size: 11 }, boxWidth: 20 },
            },
            tooltip: {
                mode: 'index' as const,
                intersect: false,
                 position: 'nearest' as const,
                 callbacks: {
                      label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}cm`,
                 },
            },
          },
          scales: {
            x: { ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
            y: {
              ticks: {
                font: { size: 10 },
                callback: (v) => v + 'cm',
              },
              min: -20,
              max: 10,
            },
          },
        }}
      />
    </div>
  )
}

/* 아래는 3번 푸시(24일 새벽 3시)까지
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler, Legend)

interface SensorData {
  nodeId: number
  label: string
  data: number[]
}

interface SensorChartProps {
  datasets: SensorData[]
  labels: string[]
  singleMode: boolean
}

const LINE_COLORS = ['#1D9E75', '#378ADD', '#BA7517', '#7F77DD', '#D85A30']

export default function SensorChart({ datasets, labels, singleMode }: SensorChartProps) {
  const chartDatasets = [
    ...datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      borderColor: LINE_COLORS[i % LINE_COLORS.length],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.4,
      fill: singleMode ? true : false,
      backgroundColor: singleMode ? 'rgba(29,158,117,0.08)' : 'transparent',
    })),
    {
      label: '임계치 (-15cm)',
      data: Array(labels.length).fill(-15),
      borderColor: '#E24B4A',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0,
      fill: false,
      backgroundColor: 'transparent',
      borderDash: [5, 5],
    },
  ]

  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>
        수위 변화 (cm) · {singleMode ? '단일 기기' : '전체 기기 비교'}
      </p>
      <Line
        data={{ labels, datasets: chartDatasets }}
        options={{
          responsive: true,
          plugins: {
            legend: {
              display: true,
              position: 'bottom' as const,
              labels: { font: { size: 11 }, boxWidth: 20 },
            },
          },
          scales: {
            x: { ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
            y: {
              ticks: {
                font: { size: 10 },
                callback: (v) => v + 'cm',
              },
              min: -20,
              max: 10,
            },
          },
        }}
      />
    </div>
  )
}

// 아래는 2번 푸시까지
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler, Legend)

interface SensorData {
  nodeId: number
  label: string
  data: number[]
}

interface SensorChartProps {
  datasets: SensorData[]
  labels: string[]
  singleMode: boolean
}

const LINE_COLORS = ['#1D9E75', '#378ADD', '#BA7517', '#7F77DD', '#D85A30']

export default function SensorChart({ datasets, labels, singleMode }: SensorChartProps) {
  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>
        수위 변화 (cm) · {singleMode ? '단일 기기' : '전체 기기 비교'}
      </p>
      <Line
        data={{
          labels,
          datasets: [
            ...datasets.map((ds, i) => ({
              label: ds.label,
              data: ds.data,
              borderColor: LINE_COLORS[i % LINE_COLORS.length],
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.4,
              fill: singleMode,
              backgroundColor: singleMode ? 'rgba(29,158,117,0.08)' : 'transparent',
            })),
            {
              label: '임계치 (-15cm)',
              data: Array(labels.length).fill(-15),
              borderColor: '#E24B4A',
              borderWidth: 1,
              borderDash: [5, 4],
              pointRadius: 0,
              fill: false,
            },
          ],
        }}
        options={{
          responsive: true,
          plugins: {
            legend: {
              display: !singleMode,
              position: 'top' as const,
              labels: { font: { size: 11 }, boxWidth: 20 },
            },
          },
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
    </div>
  )
}

//아래는 1차 작업: feat: 버전1에서 새 구조로 개편 (대시보드 분리, 알람 페이지 추가) 까지만
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
}*/