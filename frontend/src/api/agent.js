import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 120000
})

export function optimizeQuestion(payload) {
  return api.post('/api/optimize', payload)
}

export function reportUrl(reportId) {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/api/report/${reportId}`
}
