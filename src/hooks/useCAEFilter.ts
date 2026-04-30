import { useState, useMemo } from 'react'
import Fuse from 'fuse.js'
import type { CAESystem, CAEDomain } from '../types/cae'

export const DOMAIN_CHIPS = [
  'Crash Safety',
  'NVH',
  'Handling',
  'Ride',
  'Durability',
  'CFD',
  'Open Source',
] as const

export type ChipValue = (typeof DOMAIN_CHIPS)[number]

export function useCAEFilter(data: CAESystem[]) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeChips, setActiveChips] = useState<Set<ChipValue>>(new Set())

  const fuse = useMemo(
    () =>
      new Fuse(data, {
        keys: ['name', 'vendor'],
        threshold: 0.4,
      }),
    [data],
  )

  const filtered = useMemo(() => {
    let results = searchQuery.trim()
      ? fuse.search(searchQuery).map((r) => r.item)
      : [...data]

    if (activeChips.size > 0) {
      results = results.filter((sys) =>
        [...activeChips].some((chip) => {
          if (chip === 'Open Source') return sys.licenseType === 'Open Source'
          return sys.domain.includes(chip as CAEDomain)
        }),
      )
    }

    return results
  }, [searchQuery, activeChips, data, fuse])

  const toggleChip = (chip: ChipValue) => {
    setActiveChips((prev) => {
      const next = new Set(prev)
      if (next.has(chip)) next.delete(chip)
      else next.add(chip)
      return next
    })
  }

  return { filtered, searchQuery, setSearchQuery, activeChips, toggleChip }
}
