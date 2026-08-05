import { humanizeKey, isPlainObject, shortValue } from './utils'

export function normalizeRows(value) {
  if (!Array.isArray(value)) return []
  return value
    .map((row) => {
      if (isPlainObject(row)) return row
      return { value: row }
    })
    .filter(Boolean)
}

export function getLabelFromRow(row, fallback = 'Item') {
  return shortValue(
    row.name ||
      row.title ||
      row.task ||
      row.activity ||
      row.phase ||
      row.milestone ||
      row.category ||
      row.workstream ||
      row.role ||
      row.id ||
      fallback,
    72,
  )
}

export function collectCollections(value, path = '', depth = 0, results = []) {
  if (!value || depth > 4) return results
  if (Array.isArray(value) && value.length > 0) {
    results.push({ path, label: humanizeKey(path.split('.').pop() || 'Items'), rows: normalizeRows(value) })
    return results
  }
  if (isPlainObject(value)) {
    Object.entries(value).forEach(([key, nestedValue]) => {
      collectCollections(nestedValue, path ? `${path}.${key}` : key, depth + 1, results)
    })
  }
  return results
}

export function getPrimitiveEntries(value) {
  if (!isPlainObject(value)) return []
  return Object.entries(value)
    .filter(([, nestedValue]) => nestedValue == null || ['string', 'number', 'boolean'].includes(typeof nestedValue))
    .slice(0, 10)
}

export function findNumberByKeys(row, keys) {
  const match = Object.entries(row).find(([key, value]) => {
    const normalizedKey = key.toLowerCase()
    const parsed = Number(value)
    return keys.some((candidate) => normalizedKey.includes(candidate)) && Number.isFinite(parsed)
  })
  return match ? Number(match[1]) : null
}

export function findScoreRows(data) {
  return collectCollections(data)
    .flatMap((collection) =>
      collection.rows.map((row, index) => {
        const score = findNumberByKeys(row, ['score', 'percent', 'rating', 'confidence', 'health'])
        if (score == null) return null
        return {
          label: getLabelFromRow(row, `${collection.label} ${index + 1}`),
          value: Math.max(0, Math.min(100, score)),
        }
      }),
    )
    .filter(Boolean)
    .slice(0, 8)
}

export function findRiskRows(data) {
  return collectCollections(data)
    .flatMap((collection) =>
      collection.rows.map((row, index) => {
        const score = findNumberByKeys(row, ['severity', 'impact', 'risk', 'probability'])
        const level = row.level || row.severity || row.impact || row.rating || row.priority
        if (score == null && !level) return null
        const normalized = String(level || '').toLowerCase()
        const value = score ?? (normalized.includes('high') ? 90 : normalized.includes('medium') ? 58 : 28)
        return {
          label: getLabelFromRow(row, `${collection.label} ${index + 1}`),
          value: Math.max(0, Math.min(100, value)),
          level: level || `${value}`,
        }
      }),
    )
    .filter(Boolean)
    .slice(0, 8)
}

export function findTimelineRows(data) {
  return collectCollections(data)
    .flatMap((collection) =>
      collection.rows.map((row, index) => {
        const start = row.start || row.start_date || row.startDate || row.from || row.date
        const end = row.end || row.end_date || row.endDate || row.to || row.target_date || row.due_date
        const duration = findNumberByKeys(row, ['duration', 'weeks', 'days', 'effort'])
        const hasTimelineSignal = start || end || duration || /schedule|timeline|milestone|sprint|phase|plan/i.test(collection.path)
        if (!hasTimelineSignal) return null
        return {
          label: getLabelFromRow(row, `${collection.label} ${index + 1}`),
          start: shortValue(start || `Step ${index + 1}`, 28),
          end: shortValue(end || '', 28),
          duration: duration || index + 1,
          index,
        }
      }),
    )
    .filter(Boolean)
    .slice(0, 8)
}

export function findDependencyRows(data) {
  return collectCollections(data)
    .flatMap((collection) =>
      collection.rows.map((row) => {
        const source = row.source || row.from || row.predecessor || row.depends_on || row.dependency || row.upstream
        const target = row.target || row.to || row.successor || row.dependent || row.task || row.downstream
        if (!source || !target) return null
        return { source: shortValue(source, 48), target: shortValue(target, 48) }
      }),
    )
    .filter(Boolean)
    .slice(0, 8)
}

export function firstUsefulTables(data) {
  return collectCollections(data)
    .filter((collection) => collection.rows.length > 0)
    .slice(0, 3)
}
