import type { LicenseType } from '../types/cae'

const LICENSE_STYLES: Record<LicenseType, string> = {
  Commercial: 'bg-blue-100 text-blue-700 border-blue-200',
  'Open Source': 'bg-green-100 text-green-700 border-green-200',
  Academic: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  Freemium: 'bg-purple-100 text-purple-700 border-purple-200',
}

export function LicenseBadge({ type }: { type: LicenseType }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap ${LICENSE_STYLES[type]}`}
    >
      {type}
    </span>
  )
}
