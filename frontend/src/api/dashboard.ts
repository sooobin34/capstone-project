import api from './axios'

export const getDailySummaries = async () => {
  const response = await api.get('/daily-summaries')
  return response.data
}

export const getAlerts = async () => {
  const response = await api.get('/alerts')
  return response.data
}

export const getNodes = async () => {
  const response = await api.get('/nodes')
  return response.data
}

export const getSensorLogs = async (nodeId: number) => {
  const response = await api.get(`/sensor-logs/node/${nodeId}`)
  return response.data
}

export const getMrvReports = async () => {
  const response = await api.get('/mrv-reports')
  return response.data
}