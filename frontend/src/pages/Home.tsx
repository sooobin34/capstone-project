import { useEffect, useState } from 'react'
import WaterLevelCard from '../components/dashboard/WaterLevelCard'
import TrendChart from '../components/dashboard/TrendChart'
import MapPreview from '../components/dashboard/MapPreview'
import AlarmSummaryCard from '../components/dashboard/AlarmSummaryCard'
import MrvSummaryCard from '../components/dashboard/MrvSummaryCard'
import { getDashboard, getSensorLogsRange, mapWaterStatus } from '../api/dashboard'

interface HomeProps {
  onNavigate: (page: string) => void
}

export default function Home({ onNavigate }: HomeProps) {
  const [dashboard, setDashboard] = useState<any>(null)
  const [chartData, setChartData] = useState<number[]>([])
  const [chartLabels, setChartLabels] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(async (data) => {
        setDashboard(data)
        // 최신 노드 ID로 그래프 데이터 가져오기
        if (data.latest_daily_summary?.node_id) {
          const nodeId = data.latest_daily_summary.node_id
          try {
            const logs = await getSensorLogsRange(nodeId, '1d')
            setChartData(logs.map((l: any) => l.inner_water_level))
            setChartLabels(logs.map((l: any) =>
              new Date(l.measured_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
            ))
          } catch {
            console.log('대시보드 데이터:', data)
            setChartData([])
            setChartLabels([])
          }
        }
      })
      .catch(e => console.error('대시보드 조회 실패', e))
      .finally(() => setLoading(false))
  }, [])

  const latestLevel = dashboard?.latest_daily_summary?.avg_inner_level
    ? parseFloat(dashboard.latest_daily_summary.avg_inner_level)
    : 0
  const latestStatus = dashboard?.latest_daily_summary?.daily_status
    ? mapWaterStatus(dashboard.latest_daily_summary.daily_status)
    : '데이터 없음'

  const latestMrv = dashboard?.latest_mrv_report
    ? {
        id: dashboard.latest_mrv_report.id,
        fieldName: dashboard.latest_mrv_report.field_name,
        reportMonth: dashboard.latest_mrv_report.report_month,
        awdCount: dashboard.latest_mrv_report.total_awd_cycles,
        carbonReduction: dashboard.latest_mrv_report.carbon_reduction,
      }
    : null

  const latestMeasured = dashboard?.latest_measured_at
  ? (() => {
      const diff = Math.floor((Date.now() - new Date(dashboard.latest_measured_at).getTime()) / 60000)
      if (diff < 0) return '방금 전'
      if (diff < 60) return `${diff}분 전`
      if (diff < 1440) return `${Math.floor(diff / 60)}시간 전`
      return `${Math.floor(diff / 1440)}일 전`
    })()
  : '-'

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 48px)', color: '#aaa', fontSize: '14px' }}>
      불러오는 중...
    </div>
  )

  return (
    <div style={{ padding: '16px 24px', maxWidth: '1200px', margin: '0 auto', height: 'calc(100vh - 48px)', display: 'flex', flexDirection: 'column', gap: '12px' }}>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '10px' }}>
        {[
          { label: '전체 논', value: `${dashboard?.total_fields ?? 0}개` },
          { label: '전체 기기', value: `${dashboard?.total_nodes ?? 0}대` },
          { label: '미해결 알람', value: `${dashboard?.unresolved_alerts ?? 0}건`, danger: (dashboard?.unresolved_alerts ?? 0) > 0 },
          { label: '최근 측정', value: latestMeasured },
        ].map((card) => (
          <div key={card.label} style={{
            background: 'white', border: '0.5px solid #e0e0e0',
            borderRadius: '10px', padding: '10px 16px',
          }}>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>{card.label}</p>
            <p style={{ fontSize: '20px', fontWeight: 500, color: card.danger ? '#c62828' : '#222' }}>{card.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', flex: 1, minHeight: 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <WaterLevelCard level={latestLevel} status={latestStatus} fieldName={dashboard?.latest_daily_summary ? `Node ${dashboard.latest_daily_summary.node_id}` : '-'} />
          <MapPreview
  fieldCount={dashboard?.total_fields ?? 0}
  onNavigate={() => onNavigate('지도')}
/>
        </div>
        <TrendChart data={chartData} labels={chartLabels} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <AlarmSummaryCard
            totalCount={dashboard?.total_alerts ?? 0}
            unresolvedCount={dashboard?.unresolved_alerts ?? 0}
            recentAlerts={dashboard?.recent_alerts ?? []}
          />
          {latestMrv && (
            <MrvSummaryCard
              report={latestMrv}
              onNavigate={() => onNavigate('MRV')}
            />
          )}
        </div>
      </div>

    </div>
  )
}