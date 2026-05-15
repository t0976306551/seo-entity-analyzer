const STATUS_LABELS: Record<string, string> = {
  pending: '準備中...',
  searching: '正在搜尋 Google...',
  crawling: '正在爬取文章...',
  analyzing: '正在分析 Entity...',
  writing: '正在寫入 Google Sheet...',
  done: '分析完成！',
  failed: '分析失敗',
}

const STATUS_STEPS = ['pending', 'searching', 'crawling', 'analyzing', 'writing', 'done']

interface Props {
  status: string
  sheetUrl?: string
  errorMsg?: string
}

export default function AnalysisProgress({ status, sheetUrl, errorMsg }: Props) {
  const currentStep = STATUS_STEPS.indexOf(status)

  return (
    <div className="mt-6 p-4 bg-blue-50 rounded-xl">
      <p className="text-blue-700 font-medium mb-3">{STATUS_LABELS[status] || status}</p>
      <div className="flex items-center gap-2 mb-3">
        {STATUS_STEPS.slice(0, -1).map((step, i) => (
          <div key={step} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              i < currentStep ? 'bg-blue-600' :
              i === currentStep ? 'bg-blue-400 animate-pulse' :
              'bg-gray-300'
            }`} />
            {i < STATUS_STEPS.length - 2 && <div className="w-8 h-0.5 bg-gray-300" />}
          </div>
        ))}
      </div>
      {status === 'done' && sheetUrl && (
        <a href={sheetUrl} target="_blank" rel="noopener noreferrer"
          className="inline-block mt-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
          查看 Google Sheet 結果 →
        </a>
      )}
      {status === 'failed' && errorMsg && (
        <p className="text-red-600 text-sm mt-2">錯誤：{errorMsg}</p>
      )}
    </div>
  )
}
