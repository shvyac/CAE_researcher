import type { CAESystem, NewsItem } from '../types/cae'

function formatDate(dateStr?: string): string {
  if (!dateStr) return 'Date unknown'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function sortedByDate(news: NewsItem[]): NewsItem[] {
  return [...news].sort((a, b) => {
    if (!a.date && !b.date) return 0
    if (!a.date) return 1
    if (!b.date) return -1
    return new Date(b.date).getTime() - new Date(a.date).getTime()
  })
}

interface NewsPageProps {
  system: CAESystem
  onBack: () => void
}

export function NewsPage({ system, onBack }: NewsPageProps) {
  const news = sortedByDate(system.latestNews ?? [])

  return (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 mb-6"
      >
        ← Back to list
      </button>

      <h2 className="text-xl font-bold text-gray-900 mb-1">
        {system.name} — News
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        {system.vendor} · {news.length} {news.length === 1 ? 'article' : 'articles'}
      </p>

      {news.length === 0 ? (
        <p className="text-gray-400 text-sm">No news available.</p>
      ) : (
        <ol className="space-y-4">
          {news.map((item, i) => (
            <li key={i} className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
              <p className="text-xs text-gray-400 mb-1">{formatDate(item.date)}</p>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 font-medium hover:text-blue-800 hover:underline leading-snug block"
              >
                {item.title}
              </a>
              {item.summary && (
                <p className="text-sm text-gray-500 mt-1.5 leading-relaxed">{item.summary}</p>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
