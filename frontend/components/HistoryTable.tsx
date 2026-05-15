const STATUS_BADGE: Record<string, string> = {
  done: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  processing: 'bg-yellow-100 text-yellow-700',
  searching: 'bg-yellow-100 text-yellow-700',
  crawling: 'bg-yellow-100 text-yellow-700',
  analyzing: 'bg-yellow-100 text-yellow-700',
  writing: 'bg-yellow-100 text-yellow-700',
  pending: 'bg-gray-100 text-gray-600',
}

interface HistoryItem {
  id: string
  keyword: string
  status: string
  sheet_url: string
  created_at: string
  error_msg: string | null
}

export default function HistoryTable({ items }: { items: HistoryItem[] }) {
  if (items.length === 0) {
    return <p className="text-gray-500 text-center py-10">尚無查詢記錄</p>
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="pb-3 pr-4">關鍵字</th>
            <th className="pb-3 pr-4">狀態</th>
            <th className="pb-3 pr-4">時間</th>
            <th className="pb-3">結果</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b hover:bg-gray-50">
              <td className="py-3 pr-4 font-medium text-gray-800">{item.keyword}</td>
              <td className="py-3 pr-4">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_BADGE[item.status] || 'bg-gray-100'}`}>
                  {item.status}
                </span>
              </td>
              <td className="py-3 pr-4 text-gray-500">
                {new Date(item.created_at).toLocaleString('zh-TW')}
              </td>
              <td className="py-3">
                {item.sheet_url ? (
                  <a href={item.sheet_url} target="_blank" rel="noopener noreferrer"
                    className="text-blue-600 hover:underline">查看 Sheet</a>
                ) : item.error_msg ? (
                  <span className="text-red-500 text-xs">{item.error_msg.slice(0, 50)}</span>
                ) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
