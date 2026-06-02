import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TrendChart from '../components/dashboard/TrendChart'
import AlarmSummaryCard from '../components/dashboard/AlarmSummaryCard'
import MrvSummaryCard from '../components/dashboard/MrvSummaryCard'
import { getDashboard, getSensorLogsRange, mapWaterStatus, getFields, getNodes, getNodeStatus, getAlerts } from '../api/dashboard'
import FieldMap from '../components/map/FieldMap'

export default function Home() {
  const navigate = useNavigate()
  const [dashboard, setDashboard] = useState<any>(null)
  const [chartData, setChartData] = useState<number[]>([])
  const [chartLabels, setChartLabels] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [fields, setFields] = useState<any[]>([])
  const [nodes, setNodes] = useState<any[]>([])
  const [selectedFieldId, setSelectedFieldId] = useState<number | ''>('')
  const [selectedNodeId, setSelectedNodeId] = useState<number | ''>('')
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null)
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null)
  const [selectedAlerts, setSelectedAlerts] = useState<any[]>([])
  const [selectedAlertTotal, setSelectedAlertTotal] = useState<number | null>(null)
  const [selectedAlertUnresolved, setSelectedAlertUnresolved] = useState<number | null>(null)

  useEffect(() => {
    getFields().then(setFields).catch(console.error)
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

  useEffect(() => {
    if (selectedFieldId) {
      getNodes(Number(selectedFieldId)).then(setNodes).catch(console.error)
      getAlerts(Number(selectedFieldId)).then(alerts => {
        setSelectedAlerts(alerts.slice(0, 3))
        setSelectedAlertTotal(alerts.length)
        setSelectedAlertUnresolved(alerts.filter((a: any) => !a.is_resolved).length)
      }).catch(console.error)
    } else {
      setNodes([])
      setSelectedNodeId('')
      setSelectedLevel(null)
      setSelectedStatus(null)
      setSelectedAlerts([])
      setSelectedAlertTotal(null)
      setSelectedAlertUnresolved(null)
    }
  }, [selectedFieldId])

  useEffect(() => {
    if (selectedNodeId) {
      getNodeStatus(Number(selectedNodeId)).then(status => {
        setSelectedLevel(status?.latest_log?.inner_water_level ?? null)
        setSelectedStatus(status?.current_status ?? null)
      }).catch(console.error)
      getSensorLogsRange(Number(selectedNodeId), '1d').then(logs => {
        setChartData(logs.map((l: any) => l.inner_water_level))
        setChartLabels(logs.map((l: any) =>
          new Date(l.measured_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
        ))
      }).catch(() => {
        setChartData([])
        setChartLabels([])
      })
    } else {
      setSelectedLevel(null)
      setSelectedStatus(null)
    }
  }, [selectedNodeId])

  const latestLevel = selectedLevel !== null
    ? selectedLevel
    : dashboard?.latest_daily_summary?.avg_inner_level
      ? parseFloat(dashboard.latest_daily_summary.avg_inner_level)
      : 0

  const latestStatus = selectedStatus
    ? mapWaterStatus(selectedStatus)
    : dashboard?.latest_daily_summary?.daily_status
      ? mapWaterStatus(dashboard.latest_daily_summary.daily_status)
      : '데이터 없음'

  const fieldName = selectedNodeId
    ? `Node ${selectedNodeId}`
    : dashboard?.latest_daily_summary
      ? `Node ${dashboard.latest_daily_summary.node_id}`
      : '-'

  const alertTotal = selectedAlertTotal !== null ? selectedAlertTotal : dashboard?.total_alerts ?? 0
  const alertUnresolved = selectedAlertUnresolved !== null ? selectedAlertUnresolved : dashboard?.unresolved_alerts ?? 0
  const recentAlerts = selectedAlerts.length > 0 ? selectedAlerts : dashboard?.recent_alerts ?? []

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

  const statusColorMap: Record<string, string> = {
    과담수: '#1565c0', 담수: '#1D9E75', 건조중: '#BA7517', 건조: '#E24B4A', '데이터 없음': '#aaa'
  }
  const statusColor = statusColorMap[latestStatus] ?? '#aaa'

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 48px)', color: '#aaa', fontSize: '14px' }}>
      불러오는 중...
    </div>
  )

  return (
    <div style={{
      padding: '12px 24px',
      maxWidth: '1400px',
      margin: '0 auto',
      height: 'calc(100vh - 48px)',
      display: 'grid',
      gridTemplateColumns: '1fr 1.2fr 1.5fr',
      gridTemplateRows:'auto 1fr',
      gap: '10px',
      boxSizing: 'border-box',
      overflow: 'hidden',
    }}>

      {/* 좌측 상단: 2x2 스탯 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: '6px' }}>
        {[
          { label: '전체 논', value: `${dashboard?.total_fields ?? 0}개` },
          { label: '전체 기기', value: `${dashboard?.total_nodes ?? 0}대` },
          { label: '미해결 알람', value: `${alertUnresolved}건`, danger: alertUnresolved > 0 },
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
            alignItems: 'flex-start',
          }}>
            <p style={{ fontSize: '11px', color: '#888', marginBottom: '6px' }}>{card.label}</p>
            <p style={{ fontSize: '20px', fontWeight: 500, color: card.danger ? '#c62828' : '#222' }}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* 중앙 상단: 현재수위 + 24시간통계 */}
      <div style={{
        background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '16px',
        display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '12px',
      }}>
        {/* 현재 수위 */}
        <div>
          <p style={{ fontSize: '12px', color: '#888', marginBottom: '6px' }}>현재 수위 · {fieldName}</p>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '8px' }}>
            <span style={{ fontSize: '32px', fontWeight: 500 }}>{latestLevel > 0 ? `+${latestLevel}` : latestLevel}</span>
            <span style={{ fontSize: '14px', color: '#888' }}>cm</span>
          </div>
          <span style={{
            display: 'inline-block', fontSize: '12px', padding: '3px 10px', borderRadius: '20px', fontWeight: 500,
            background: statusColor + '20', color: statusColor,
          }}>{latestStatus}</span>
        </div>

        <div style={{ height: '0.5px', background: '#e0e0e0' }} />

        {/* 24시간 통계 */}
        <div>
          <p style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>24시간 통계</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '6px' }}>
            {[
              { label: '평균', value: `${dashboard?.latest_daily_summary?.avg_inner_level ?? 0}cm` },
              { label: '최고', value: `${dashboard?.latest_daily_summary?.max_inner_level ?? 0}cm` },
              { label: '최저', value: `${dashboard?.latest_daily_summary?.min_inner_level ?? 0}cm` },
              { label: '알람', value: `${alertUnresolved}건` },
            ].map((item) => (
              <div key={item.label} style={{ background: '#f5f5f5', borderRadius: '8px', padding: '8px 10px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <p style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>{item.label}</p>
                <p style={{ fontSize: '15px', fontWeight: 500 }}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 우측 상단: 논/노드 드롭다운 + 지도 */}
      <div style={{
        background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '14px',
        display: 'flex', flexDirection: 'column', gap: '8px',
      }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          <select
            value={selectedFieldId}
            onChange={(e) => { setSelectedFieldId(e.target.value ? Number(e.target.value) : ''); setSelectedNodeId('') }}
            style={{ flex: 1, fontSize: '12px', padding: '5px 6px', borderRadius: '8px', border: '0.5px solid #e0e0e0', background: '#f5f5f5', color: '#222' }}
          >
            <option value="">논 선택</option>
            {fields.map((f) => <option key={f.id} value={f.id}>{f.field_name}</option>)}
          </select>
          <select
            value={selectedNodeId}
            onChange={(e) => setSelectedNodeId(e.target.value ? Number(e.target.value) : '')}
            style={{ flex: 1, fontSize: '12px', padding: '5px 6px', borderRadius: '8px', border: '0.5px solid #e0e0e0', background: '#f5f5f5', color: '#222' }}
          >
            <option value="">노드 선택</option>
            {nodes.map((n) => <option key={n.id} value={n.id}>Node {n.id}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, borderRadius: '8px', overflow: 'hidden', minHeight: 0 }}>
          {fields.length > 0 ? (
            <FieldMap
              sensors={[]}
              center={[
                fields.find(f => f.id === Number(selectedFieldId))?.latitude ?? fields[0].latitude,
                fields.find(f => f.id === Number(selectedFieldId))?.longitude ?? fields[0].longitude,
              ]}
            />
          ) : (
            <div style={{ height: '100%', background: '#f5f5f5', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '11px', color: '#888' }}>논 {dashboard?.total_fields ?? 0}개 등록됨</span>
            </div>
          )}
        </div>
        <p onClick={() => navigate('/map')} style={{ fontSize: '11px', color: '#1D9E75', cursor: 'pointer', margin: 0 }}>
          지도 보기 →
        </p>
      </div>

      {/* 좌측 하단: 알람요약 */}
      <div style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <AlarmSummaryCard
          totalCount={alertTotal}
          unresolvedCount={alertUnresolved}
          recentAlerts={recentAlerts}
        />
      </div>

      {/* 중앙 하단: MRV 요약 */}
      <div style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <MrvSummaryCard
          report={latestMrv}
          onNavigate={() => navigate('/mrv')}
        />
      </div>

      {/* 우측 하단: 수위 추이 그래프 */}
      <div style={{
        background: 'white', border: '0.5px solid #e0e0e0', borderRadius: '12px', padding: '14px',
        overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        <p style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>수위 추이 (24시간)</p>
        <div style={{ flex: 1, minHeight: 0 }}>
          <TrendChart data={chartData} labels={chartLabels} />
        </div>
      </div>

    </div>
  )
}