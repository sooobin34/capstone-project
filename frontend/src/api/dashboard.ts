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