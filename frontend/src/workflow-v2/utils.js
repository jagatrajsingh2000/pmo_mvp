export function createDefaultSourceFile(source) {
  const lines = [
    'Default PMO Source Brief',
    '',
    ...Object.entries(source).map(([key, value]) => {
      if (Array.isArray(value)) return `${labelize(key)}:\n${value.map((item) => `- ${item}`).join('\n')}`
      return `${labelize(key)}: ${value}`
    }),
  ]
  return new File([lines.join('\n\n')], 'workflow-v2-default-source.txt', { type: 'text/plain' })
}

export function labelize(key) {
  return String(key || '')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function formatBytes(bytes) {
  const size = Number(bytes)
  if (!Number.isFinite(size)) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

export function fileBrief(file) {
  if (!file) return null
  return {
    name: file.name,
    type: file.type || 'document',
    size: formatBytes(file.size),
  }
}

export function stringifyJson(value) {
  return JSON.stringify(value, null, 2)
}

export function getPayloadSize(value) {
  try {
    return formatBytes(new Blob([JSON.stringify(value)]).size)
  } catch {
    return '-'
  }
}

export function resultSummary(data) {
  if (!data || typeof data !== 'object') return []
  return Object.entries(data)
    .slice(0, 6)
    .map(([key, value]) => {
      let display = '-'
      if (Array.isArray(value)) display = `${value.length} items`
      else if (value && typeof value === 'object') display = `${Object.keys(value).length} fields`
      else if (value != null) display = String(value)
      return [labelize(key), display]
    })
}
