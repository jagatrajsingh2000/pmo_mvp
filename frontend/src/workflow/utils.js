import { base64ToFile } from './api'

export function asFileName(name, extension) {
  const clean = String(name || 'pmo-workflow-output')
    .replace(/[^a-z0-9._-]+/gi, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  return clean.toLowerCase().endsWith(`.${extension}`) ? clean : `${clean}.${extension}`
}

export function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function printable(value) {
  return JSON.stringify(
    value,
    (key, nestedValue) => {
      if (nestedValue instanceof File) {
        return { name: nestedValue.name, type: nestedValue.type, size: nestedValue.size }
      }
      if (nestedValue instanceof Blob) {
        return { type: nestedValue.type, size: nestedValue.size }
      }
      return nestedValue
    },
    2,
  )
}

export function previewText(value, maxLength = 3600) {
  const text = printable(value)
  if (!text) return 'No JSON payload returned.'
  return text.length > maxLength ? `${text.slice(0, maxLength)}\n... trimmed for preview` : text
}

export function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Blob)
}

export function humanizeKey(key) {
  return String(key || '')
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function shortValue(value, maxLength = 180) {
  if (value == null) return '-'
  if (typeof value === 'string') return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return previewText(value, maxLength)
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
    file_name: file.name,
    file_type: file.type || 'document',
    file_size: formatBytes(file.size),
  }
}

export function responseBrief(result, file) {
  if (!result) return null
  if (result.kind === 'blob') {
    return {
      response_kind: 'document',
      content_type: result.contentType || file?.type || 'application/octet-stream',
      content_disposition: result.disposition || '-',
      document: fileBrief(file),
    }
  }
  return {
    response_kind: 'json',
    content_type: result.contentType || 'application/json',
    payload: result.data,
    downloaded_document: fileBrief(file),
  }
}

export function endpointInput(endpoint, payload) {
  return { endpoint, payload }
}

export function fileInput(endpoint, file) {
  return { endpoint, multipart_field: 'file', file: fileBrief(file) }
}

export function filesInput(endpoint, files) {
  return { endpoint, multipart_field: 'files', files: files.map(fileBrief) }
}

export function fileFromJson(json, filename, mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
  const base64 =
    json?.file_base64 ||
    json?.docx_base64 ||
    json?.document_base64 ||
    json?.content_base64 ||
    json?.data?.file_base64 ||
    json?.data?.docx_base64 ||
    json?.data?.document_base64
  if (base64) return base64ToFile(base64, filename, mimeType)

  const text =
    json?.content ||
    json?.document ||
    json?.text ||
    json?.markdown ||
    json?.data?.content ||
    json?.data?.document ||
    json?.data?.text
  if (typeof text === 'string' && text.trim()) {
    return new File([text], asFileName(filename.replace(/\.docx$/i, ''), 'txt'), { type: 'text/plain' })
  }
  return null
}

export function blobToFile(blob, fallbackName) {
  return new File([blob], fallbackName, {
    type: blob.type || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
}

export function responseToFile(result, fallbackName) {
  if (result.kind === 'blob') return blobToFile(result.data, fallbackName)
  return fileFromJson(result.data, fallbackName)
}

export function statusLabel(status) {
  if (status === 'done') return 'Complete'
  if (status === 'running') return 'Running'
  if (status === 'failed') return 'Failed'
  return 'Queued'
}

export function getTopLevelCount(data) {
  if (!data || typeof data !== 'object') return 0
  if (Array.isArray(data)) return data.length
  return Object.keys(data).length
}
