import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function startAnalysis(keyword: string) {
  const { data } = await api.post('/analyze', { keyword })
  return data as { job_id: string; status: string }
}

export async function getJobStatus(jobId: string) {
  const { data } = await api.get(`/job/${jobId}`)
  return data
}

export async function getHistory() {
  const { data } = await api.get('/history')
  return data as Array<{
    id: string
    keyword: string
    status: string
    sheet_url: string
    created_at: string
    error_msg: string | null
  }>
}
