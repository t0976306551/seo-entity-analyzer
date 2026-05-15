'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { startAnalysis, getJobStatus } from '@/lib/api'
import AnalysisProgress from '@/components/AnalysisProgress'

export default function DashboardPage() {
  const router = useRouter()
  const [keyword, setKeyword] = useState('4G 吃到飽')
  const [loading, setLoading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [userEmail, setUserEmail] = useState('')

  useEffect(() => {
    setUserEmail(localStorage.getItem('user_email') || '')
  }, [])

  const handleLogout = () => {
    localStorage.clear()
    document.cookie = 'sb-access-token=; path=/; max-age=0'
    router.push('/login')
  }

  const handleAnalyze = async () => {
    if (!keyword.trim()) return
    setLoading(true)
    setError('')
    setJobStatus(null)
    try {
      const result = await startAnalysis(keyword.trim())
      setJobId(result.job_id)
      setJobStatus({ status: 'pending' })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || '分析啟動失敗')
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!jobId) return
    pollingRef.current = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId)
        setJobStatus(status)
        if (status.status === 'done' || status.status === 'failed') {
          clearInterval(pollingRef.current!)
          setLoading(false)
        }
      } catch {
        clearInterval(pollingRef.current!)
        setLoading(false)
      }
    }, 3000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [jobId])

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-800">SEO Entity 分析</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{userEmail}</span>
          <a href="/history" className="text-sm text-blue-600 hover:underline">查詢歷史</a>
          <button onClick={handleLogout} className="text-sm text-red-500 hover:underline">登出</button>
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-6 py-10">
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">輸入關鍵字</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="例如：4G 吃到飽"
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !keyword.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '分析中...' : '開始分析'}
            </button>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
          {jobStatus && (
            <AnalysisProgress
              status={jobStatus.status as string}
              sheetUrl={jobStatus.sheet_url as string | undefined}
              errorMsg={jobStatus.error_msg as string | undefined}
            />
          )}
        </div>
      </main>
    </div>
  )
}
