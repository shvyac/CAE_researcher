import { useState, useEffect } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table'
import type { CAESystem } from '../types/cae'
import { LicenseBadge } from './StatusBadge'
import { SearchBar } from './SearchBar'
import { DomainFilter } from './DomainFilter'
import { useCAEFilter } from '../hooks/useCAEFilter'
import bundledData from '../data/caeSystems.json'

// Domain chip colors used inside table rows
const DOMAIN_ROW_STYLES: Record<string, string> = {
  'Crash Safety': 'bg-red-50 text-red-700 border-red-200',
  NVH: 'bg-blue-50 text-blue-700 border-blue-200',
  Handling: 'bg-violet-50 text-violet-700 border-violet-200',
  Ride: 'bg-cyan-50 text-cyan-700 border-cyan-200',
  Durability: 'bg-orange-50 text-orange-700 border-orange-200',
  CFD: 'bg-sky-50 text-sky-700 border-sky-200',
  Thermal: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  Multibody: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  General: 'bg-gray-100 text-gray-600 border-gray-200',
}

function NameCell({ system }: { system: CAESystem }) {
  const [expanded, setExpanded] = useState(false)
  const news = system.latestNews ?? []
  return (
    <div>
      <div className="flex items-center gap-2 flex-wrap">
        <a
          href={system.vendorUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-blue-600 hover:text-blue-800 hover:underline whitespace-nowrap"
        >
          {system.name}
        </a>
        {news.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs bg-blue-50 text-blue-600 border border-blue-200 px-1.5 py-0.5 rounded-full hover:bg-blue-100 whitespace-nowrap cursor-pointer"
          >
            {news.length} news {expanded ? '▲' : '▼'}
          </button>
        )}
      </div>
      {expanded && (
        <ul className="mt-1.5 space-y-1">
          {news.map((item, i) => (
            <li key={i}>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-500 hover:text-blue-600 hover:underline line-clamp-1"
              >
                {item.title}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

const columnHelper = createColumnHelper<CAESystem>()

const columns = [
  columnHelper.accessor('name', {
    header: 'Name',
    cell: (info) => <NameCell system={info.row.original} />,
  }),
  columnHelper.accessor('vendor', {
    header: 'Vendor',
    cell: (info) => (
      <span className="text-gray-700 whitespace-nowrap">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('domain', {
    header: 'Domain',
    enableSorting: false,
    cell: (info) => (
      <div className="flex flex-wrap gap-1 min-w-[120px]">
        {info.getValue().map((d) => (
          <span
            key={d}
            className={`inline-block px-1.5 py-0.5 rounded text-xs border ${
              DOMAIN_ROW_STYLES[d] ?? 'bg-gray-100 text-gray-600 border-gray-200'
            }`}
          >
            {d}
          </span>
        ))}
      </div>
    ),
  }),
  columnHelper.accessor('solverType', {
    header: 'Solver',
    cell: (info) => (
      <span className="font-mono text-xs text-gray-600 whitespace-nowrap">
        {info.getValue()}
      </span>
    ),
  }),
  columnHelper.accessor('licenseType', {
    header: 'License',
    cell: (info) => <LicenseBadge type={info.getValue()} />,
  }),
  columnHelper.accessor('os', {
    header: 'OS',
    enableSorting: false,
    cell: (info) => (
      <span className="text-xs text-gray-500 whitespace-nowrap">
        {info.getValue().join(' / ')}
      </span>
    ),
  }),
  columnHelper.accessor('hpcSupported', {
    header: 'HPC',
    cell: (info) =>
      info.getValue() ? (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-teal-700 bg-teal-50 border border-teal-200 px-1.5 py-0.5 rounded">
          ✓ HPC
        </span>
      ) : (
        <span className="text-gray-300 text-sm">—</span>
      ),
  }),
  columnHelper.accessor('gpuSupported', {
    header: 'GPU',
    cell: (info) =>
      info.getValue() ? (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-purple-700 bg-purple-50 border border-purple-200 px-1.5 py-0.5 rounded">
          ✓ GPU
        </span>
      ) : (
        <span className="text-gray-300 text-sm">—</span>
      ),
  }),
  columnHelper.accessor('version', {
    header: 'Version',
    cell: (info) => (
      <span className="font-mono text-xs text-gray-500">
        {info.getValue() ?? '—'}
      </span>
    ),
  }),
]

export function CAETable() {
  const [data, setData] = useState<CAESystem[]>(bundledData as CAESystem[])
  const [sorting, setSorting] = useState<SortingState>([])

  useEffect(() => {
    fetch('/user/data/cae_systems.json')
      .then((r) => r.json())
      .then((d: CAESystem[]) => setData(d))
      .catch(() => {/* keep bundled data */})
  }, [])

  const { filtered, searchQuery, setSearchQuery, activeChips, toggleChip } =
    useCAEFilter(data)

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <SearchBar value={searchQuery} onChange={setSearchQuery} />
        <div className="flex-1">
          <DomainFilter activeChips={activeChips} onToggle={toggleChip} />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
        <table className="w-full text-sm border-collapse">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-gray-50 border-b border-gray-200">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className={`px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap ${
                      header.column.getCanSort()
                        ? 'cursor-pointer select-none hover:text-gray-800 hover:bg-gray-100'
                        : ''
                    }`}
                  >
                    <span className="inline-flex items-center gap-1">
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                      {header.column.getIsSorted() === 'asc' && (
                        <span className="text-blue-500">↑</span>
                      )}
                      {header.column.getIsSorted() === 'desc' && (
                        <span className="text-blue-500">↓</span>
                      )}
                      {header.column.getCanSort() &&
                        !header.column.getIsSorted() && (
                          <span className="text-gray-300">↕</span>
                        )}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-gray-50 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2.5 align-middle">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="py-16 text-center text-gray-400 text-sm">
            No systems match your filters.
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 mt-2 text-right">
        {filtered.length} of {data.length} systems
      </p>
    </div>
  )
}
