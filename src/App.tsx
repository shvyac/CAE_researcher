import { CAETable } from './components/CAETable'

function App() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-screen-xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">CAE System List</h1>
          <p className="text-gray-500 text-sm mt-1">
            Automotive engineering simulation software directory
          </p>
        </header>
        <CAETable />
      </div>
    </main>
  )
}

export default App
