import api from './axios'

export interface Field {
  id: number
  field_name: string
  latitude: number
  longitude: number
  location_desc: string
}

export interface Node {
  id: number
  field_id: number
  mac_address: string
  latitude: number
  longitude: number
  location_desc: string
  is_active: boolean
}

export interface Alert {
  id: number
  node_id: number
  alert_type: 'HIGH_WATER' | 'LOW_WATER'
  message: string
  is_resolved: boolean
  created_at: string
}

export interface SensorLog {
  id: number
  node_id: number
  inner_water_level: number
  outer_water_level: number
  created_at: string
}

export const getFields = async (): Promise<Field[]> => {
  const res = await api.get('/fields')
  return (res.data as any).data
}

export const getNodes = async (fieldId?: number): Promise<Node[]> => {
  const url = fieldId ? `/nodes?field_id=${fieldId}` : '/nodes'
  const res = await api.get(url)
  return (res.data as any).data
}

export const getNodeStatus = async (nodeId: number) => {
  const res = await api.get(`/nodes/${nodeId}/status`)
  return (res.data as any).data
}

export const getSensorLogs = async (nodeId: number, start?: string, end?: string): Promise<SensorLog[]> => {
  let url = `/sensor-logs/node/${nodeId}`
  if (start && end) url += `?start=${start}&end=${end}`
  const res = await api.get(url)
  return (res.data as any).data
}

export const getAlerts = async (fieldId?: number): Promise<Alert[]> => {
  const url = fieldId ? `/alerts?field_id=${fieldId}` : '/alerts'
  const res = await api.get(url)
  return (res.data as any).data
}

export const resolveAlert = async (alertId: number) => {
  const res = await api.patch(`/alerts/${alertId}/resolve`)
  return (res.data as any).data
}

export const getMrvReports = async (fieldId?: number) => {
  const url = fieldId ? `/mrv-reports?field_id=${fieldId}` : '/mrv-reports'
  const res = await api.get(url)
  return (res.data as any).data
}

export const getDashboard = async () => {
  const res = await api.get('/dashboard')
  return (res.data as any).data
}

export const mapWaterStatus = (status: string): '과담수' | '담수' | '건조중' | '건조' | '데이터 없음' => {
  const statusMap: Record<string, '과담수' | '담수' | '건조중' | '건조' | '데이터 없음'> = {
    OVERFLOODED: '과담수',
    FLOODED: '담수',
    DRYING: '건조중',
    DRY: '건조',
    NO_DATA: '데이터 없음',
  }
  return statusMap[status] ?? '데이터 없음'
}

// 아래는 4.29 추가한 api
// dashboard.ts 에 추가
export const getDailySummaries = async (nodeId?: number) => {
  const url = nodeId ? `/daily-summaries?node_id=${nodeId}` : '/daily-summaries'
  const res = await api.get(url)
  return (res.data as any).data
}

export const getSensorLogsRange = async (nodeId: number, period: '1h' | '1d' | '1w' | '1m') => {
  const res = await api.get(`/sensor-logs/node/${nodeId}/range?period=${period}`)
  return (res.data as any).data.logs  // ← .data 에서 .data.logs 로 변경
}

export const getSensorStats = async (nodeId: number) => {
  const res = await api.get(`/sensor-logs/node/${nodeId}/stats`)
  return (res.data as any).data
}

export const getLatestSensorLog = async (nodeId: number) => {
  const res = await api.get(`/sensor-logs/latest/${nodeId}`)
  return (res.data as any).data
}

export const downloadMrvPdf = (reportId: number) =>
  `https://capstone-project-54l6.onrender.com/mrv-reports/${reportId}/download/pdf`

export const downloadMrvExcel = (reportId: number) =>
  `https://capstone-project-54l6.onrender.com/mrv-reports/${reportId}/download/excel`


//4.29 createMrvReport 함수 추가
export const createMrvReport = async (fieldId: number, reportMonth: string) => {
  const res = await api.post('/mrv-reports', {
    field_id: fieldId,
    report_month: reportMonth,
  })
  return (res.data as any).data
}

//validation API 함수(validation records)
export const uploadValidationRecord = async (formData: FormData) => {
  const res = await api.post('/validation-records/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return (res.data as any).data
}

export const getValidationRecords = async (fieldId?: number) => {
  const url = fieldId ? `/validation-records?field_id=${fieldId}` : '/validation-records'
  const res = await api.get(url)
  return (res.data as any).data
}

export const getValidationSummary = async (fieldId?: number) => {
  const url = fieldId ? `/validation-records/summary?field_id=${fieldId}` : '/validation-records/summary'
  const res = await api.get(url)
  return (res.data as any).data
}

export const analyzeValidationRecord = async (recordId: number) => {
  const res = await api.post(`/validation-records/${recordId}/analyze`)
  return (res.data as any).data
}

export const downloadValidationRecord = (recordId: number) =>
  `https://capstone-project-54l6.onrender.com/validation-records/${recordId}/download`
