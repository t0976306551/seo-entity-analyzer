'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { startAnalysis, getJobStatus, api } from '@/lib/api'
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
  const [sheetStatus, setSheetStatus] = useState<string>('pending')
  const [connectingGoogle, setConnectingGoogle] = useState(false)

  useEffect(() => {
    setUserEmail(localStorage.getItem('user_email') || '')
    setSheetStatus(localStorage.getItem('sheet_status') || 'pending')
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('google_connected') === '1') {
      setSheetStatus('active')
      localStorage.setItem('sheet_status', 'active')
      window.history.replaceState({}, '', '/dashboard')
    }
    if (params.get('google_error') === '1') {
      const msg = params.get('msg') || ''
      setError('Google 帳號連結失敗：' + (msg || '請重試'))
      window.history.replaceState({}, '', '/dashboard')
    }
  }, [])

  const handleConnectGoogle = async () => {
    setConnectingGoogle(true)
    try {
      const res = await api.get('/auth/google/url')
      window.location.href = res.data.url
    } catch {
      setError('無法取得 Google 授權網址')
      setConnectingGoogle(false)
    }
  }

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
      <main className="max-w-2xl mx-auto px-6 py-10 space-y-4">

        {sheetStatus !== 'active' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 flex items-center justify-between">
            <div>
              <p className="font-medium text-yellow-800">尚未連結 Google 帳號</p>
              <p className="text-sm text-yellow-600 mt-1">連結後分析結果會自動寫入你的 Google 試算表</p>
            </div>
            <button
              onClick={handleConnectGoogle}
              disabled={connectingGoogle}
              className="bg-white border border-yellow-400 text-yellow-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-50 disabled:opacity-50"
            >
              {connectingGoogle ? '跳轉中...' : '連結 Google 帳號'}
            </button>
          </div>
        )}

        {sheetStatus === 'active' && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-2">
            <span className="text-green-600">✓</span>
            <p className="text-sm text-green-700">Google 帳號已連結，分析結果將寫入你的試算表</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">輸入關鍵字</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="例如：4G 吃到飽"
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !keyword.trim() || sheetStatus !== 'active'}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '分析中...' : '開始分析'}
            </button>
          </div>
          {sheetStatus !== 'active' && (
            <p className="mt-2 text-xs text-gray-400">請先連結 Google 帳號才能開始分析</p>
          )}
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
