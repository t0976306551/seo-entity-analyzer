'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getHistory } from '@/lib/api'
import HistoryTable from '@/components/HistoryTable'

export default function HistoryPage() {
  const router = useRouter()
  const [items, setItems] = useState<Parameters<typeof HistoryTable>[0]['items']>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHistory()
      .then(setItems)
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false))
  }, [router])

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-800">查詢歷史</h1>
        <a href="/dashboard" className="text-sm text-blue-600 hover:underline">← 回到分析</a>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-10">
        <div className="bg-white rounded-xl shadow-md p-6">
          {loading ? (
            <p className="text-center text-gray-400 py-10">載入中...</p>
          ) : (
            <HistoryTable items={items} />
          )}
        </div>
      </main>
    </div>
  )
}
