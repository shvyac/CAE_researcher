import { useState } from 'react'
import { CAETable } from './components/CAETable'
import { NewsPage } from './components/NewsPage'
import type { CAESystem } from './types/cae'

function App() {
  const [newsTarget, setNewsTarget] = useState<CAESystem | null>(null)

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-screen-xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">CAE System List</h1>
          <p className="text-gray-500 text-sm mt-1">
            Automotive engineering simulation software directory
          </p>
        </header>

        {newsTarget ? (
          <NewsPage system={newsTarget} onBack={() => setNewsTarget(null)} />
        ) : (
          <CAETable onViewNews={setNewsTarget} />
        )}
      </div>
    </main>
  )
}

export default App
