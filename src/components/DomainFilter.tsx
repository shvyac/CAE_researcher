import { DOMAIN_CHIPS, type ChipValue } from '../hooks/useCAEFilter'

// Full class names so Tailwind v4 scanner can detect them at build time
const CHIP_STYLES: Record<ChipValue, { active: string; inactive: string }> = {
  'Crash Safety': {
    active: 'bg-red-500 text-white border-red-500',
    inactive: 'text-red-700 border-red-300 hover:bg-red-50',
  },
  NVH: {
    active: 'bg-blue-500 text-white border-blue-500',
    inactive: 'text-blue-700 border-blue-300 hover:bg-blue-50',
  },
  Handling: {
    active: 'bg-violet-500 text-white border-violet-500',
    inactive: 'text-violet-700 border-violet-300 hover:bg-violet-50',
  },
  Ride: {
    active: 'bg-cyan-500 text-white border-cyan-500',
    inactive: 'text-cyan-700 border-cyan-300 hover:bg-cyan-50',
  },
  Durability: {
    active: 'bg-orange-500 text-white border-orange-500',
    inactive: 'text-orange-700 border-orange-300 hover:bg-orange-50',
  },
  CFD: {
    active: 'bg-sky-500 text-white border-sky-500',
    inactive: 'text-sky-700 border-sky-300 hover:bg-sky-50',
  },
  'Open Source': {
    active: 'bg-green-500 text-white border-green-500',
    inactive: 'text-green-700 border-green-300 hover:bg-green-50',
  },
}

interface Props {
  activeChips: Set<ChipValue>
  onToggle: (chip: ChipValue) => void
}

export function DomainFilter({ activeChips, onToggle }: Props) {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">Filter:</span>
      {DOMAIN_CHIPS.map((chip) => {
        const isActive = activeChips.has(chip)
        const styles = CHIP_STYLES[chip]
        return (
          <button
            key={chip}
            onClick={() => onToggle(chip)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors cursor-pointer ${
              isActive ? styles.active : `bg-white ${styles.inactive}`
            }`}
          >
            {chip}
          </button>
        )
      })}
      {activeChips.size > 0 && (
        <button
          onClick={() => DOMAIN_CHIPS.forEach((c) => activeChips.has(c) && onToggle(c))}
          className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 underline"
        >
          Clear
        </button>
      )}
    </div>
  )
}
