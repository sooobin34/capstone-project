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
  inner_level: number
  outer_level: number
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

/*아래는 api 연결 전까지 코드
import api from './axios'

export const getFields = async () => {
  const response = await api.get('/fields')
  return response.data
}

export const getDashboard = async (fieldId?: number) => {
  const url = fieldId ? `/dashboard?field_id=${fieldId}` : '/dashboard'
  const response = await api.get(url)
  return response.data
}

export const getNodes = async (fieldId?: number) => {
  const url = fieldId ? `/nodes?field_id=${fieldId}` : '/nodes'
  const response = await api.get(url)
  return response.data
}

export const getNodeStatus = async (nodeId: number) => {
  const response = await api.get(`/nodes/${nodeId}/status`)
  return response.data
}

export const getSensorLogs = async (nodeId: number, start?: string, end?: string) => {
  let url = `/sensor-logs/node/${nodeId}`
  if (start && end) url += `?start=${start}&end=${end}`
  const response = await api.get(url)
  return response.data
}

export const getAlerts = async (fieldId?: number) => {
  const url = fieldId ? `/alerts?field_id=${fieldId}` : '/alerts'
  const response = await api.get(url)
  return response.data
}

export const resolveAlert = async (alertId: number) => {
  const response = await api.patch(`/alerts/${alertId}/resolve`)
  return response.data
}

export const getMrvReports = async (fieldId?: number) => {
  const url = fieldId ? `/mrv-reports?field_id=${fieldId}` : '/mrv-reports'
  const response = await api.get(url)
  return response.data
}
  */