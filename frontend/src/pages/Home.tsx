import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import WaterLevelCard from '../components/dashboard/WaterLevelCard'
import TrendChart from '../components/dashboard/TrendChart'
import MapPreview from '../components/dashboard/MapPreview'
import AlarmSummaryCard from '../components/dashboard/AlarmSummaryCard'
import MrvSummaryCard from '../components/dashboard/MrvSummaryCard'
import { getDashboard, getSensorLogsRange, mapWaterStatus } from '../api/dashboard'

export default function Home() {
  const navigate = useNavigate()
  const [dashboard, setDashboard] = useState<any>(null)
  const [chartData, setChartData] = useState<number[]>([])
  const [chartLabels, setChartLabels] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(async (data) => {
        setDashboard(data)
        if (data.latest_daily_summary?.node_id) {
          const nodeId = data.latest_daily_summary.node_id
          try {
            const logs = await getSensorLogsRange(nodeId, '1d')
            setChartData(logs.map((l: any) => l.inner_water_level))
            setChartLabels(logs.map((l: any) =>
              new Date(l.measured_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
            ))
          } catch {
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
    <div style={{
      padding: '12px 24px',
      maxWidth: '1200px',
      margin: '0 auto',
      height: 'calc(100vh - 48px)',
      display: 'grid',
      gridTemplateColumns: '1fr 2fr 1fr',
      gridTemplateRows: 'auto 1fr',
      gap: '10px',
      boxSizing: 'border-box',
      overflow: 'hidden',
    }}>

      {/* 좌측 상단: 2x2 스탯 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: '6px' }}>
        {[
          { label: '전체 논', value: `${dashboard?.total_fields ?? 0}개` },
          { label: '전체 기기', value: `${dashboard?.total_nodes ?? 0}대` },
          { label: '미해결 알람', value: `${dashboard?.unresolved_alerts ?? 0}건`, danger: (dashboard?.unresolved_alerts ?? 0) > 0 },
          { label: '최근 측정', value: latestMeasured },
        ].map((card) => (
          <div key={card.label} style={{
            background: 'white',
            border: '0.5px solid #e0e0e0',
            borderRadius: '10px',
            padding: '8px 12px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}>
            <p style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>{card.label}</p>
            <p style={{ fontSize: '16px', fontWeight: 500, color: card.danger ? '#c62828' : '#222' }}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* 중앙 상단: 현재수위 + 24시간통계 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <WaterLevelCard
          level={latestLevel}
          status={latestStatus}
          fieldName={dashboard?.latest_daily_summary ? `Node ${dashboard.latest_daily_summary.node_id}` : '-'}
        />
        <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '14px' }}>
          <p style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>24시간 통계</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
            {[
              { label: '평균', value: `${dashboard?.latest_daily_summary?.avg_inner_level ?? 0}cm` },
              { label: '최고', value: `${dashboard?.latest_daily_summary?.max_inner_level ?? 0}cm` },
              { label: '최저', value: `${dashboard?.latest_daily_summary?.min_inner_level ?? 0}cm` },
              { label: '알람', value: `${dashboard?.unresolved_alerts ?? 0}건` },
            ].map((item) => (
              <div key={item.label} style={{ background: '#f5f5f5', borderRadius: '8px', padding: '6px 10px' }}>
                <p style={{ fontSize: '10px', color: '#888', marginBottom: '2px' }}>{item.label}</p>
                <p style={{ fontSize: '14px', fontWeight: 500 }}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 우측 상단: 논/노드 드롭다운 + 지도 */}
      <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          <select style={{ flex: 1, fontSize: '11px', padding: '5px 6px', borderRadius: '8px', border: '0.5px solid #e0e0e0', background: '#f5f5f5', color: '#222' }}>
            <option>논 고르기</option>
          </select>
          <select style={{ flex: 1, fontSize: '11px', padding: '5px 6px', borderRadius: '8px', border: '0.5px solid #e0e0e0', background: '#f5f5f5', color: '#222' }}>
            <option>노드 고르기</option>
          </select>
        </div>
        <div style={{ flex: 1, background: '#f5f5f5', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '0.5px solid #e0e0e0' }}>
          <div style={{ textAlign: 'center' }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" style={{ display: 'block', margin: '0 auto 6px' }}>
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="#aaa"/>
              <circle cx="12" cy="9" r="2.5" fill="white"/>
            </svg>
            <span style={{ fontSize: '11px', color: '#888' }}>논 {dashboard?.total_fields ?? 0}개 등록됨</span>
          </div>
        </div>
        <p onClick={() => navigate('/map')} style={{ fontSize: '11px', color: '#1D9E75', cursor: 'pointer', margin: 0 }}>
          지도 보기 →
        </p>
      </div>

      {/* 좌측 하단: 알람요약 */}
      <div style={{ overflow: 'hidden' }}>
        <AlarmSummaryCard
          totalCount={dashboard?.total_alerts ?? 0}
          unresolvedCount={dashboard?.unresolved_alerts ?? 0}
          recentAlerts={dashboard?.recent_alerts ?? []}
        />
      </div>

      {/* 중앙 하단: 그래프 */}
        <div style={{ background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '14px', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
        <p style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>수위 추이 (24시간)</p>
        <div style={{ flex: 1, minHeight: 0 }}>
          <TrendChart data={chartData} labels={chartLabels} />
        </div>
      </div>

      {/* 우측 하단: MRV 요약 */}
      <div style={{ overflow: 'hidden' }}>
        <MrvSummaryCard
          report={latestMrv}
          onNavigate={() => navigate('/mrv')}
        />
      </div>

    </div>
  )
}