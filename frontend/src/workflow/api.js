import { HOSTED_API_BASE } from './constants'

export function tokenFromLogin(data) {
  return data?.access_token || data?.token || data?.jwt || data?.data?.access_token || ''
}

function authHeader(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function base64ToFile(base64, filename, mimeType) {
  const raw = base64.includes(',') ? base64.split(',').pop() : base64
  const bytes = atob(raw)
  const buffer = new Uint8Array(bytes.length)
  for (let index = 0; index < bytes.length; index += 1) {
    buffer[index] = bytes.charCodeAt(index)
  }
  return new File([buffer], filename, { type: mimeType })
}

export async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  const disposition = response.headers.get('content-disposition') || ''
  if (contentType.includes('application/json')) {
    const json = await response.json()
    if (!response.ok) throw new Error(json.detail || json.message || response.statusText)
    return { kind: 'json', data: json, contentType, disposition }
  }

  const blob = await response.blob()
  if (!response.ok) throw new Error(await blob.text())
  return { kind: 'blob', data: blob, contentType, disposition }
}

export async function requestJson(path, payload, token) {
  const response = await fetch(`${HOSTED_API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token),
    },
    body: JSON.stringify(payload),
  })
  return parseResponse(response)
}

export async function requestFile(path, fieldName, file, token) {
  const formData = new FormData()
  formData.append(fieldName, file)
  const response = await fetch(`${HOSTED_API_BASE}${path}`, {
    method: 'POST',
    headers: authHeader(token),
    body: formData,
  })
  return parseResponse(response)
}

export async function requestFiles(path, fieldName, files, token) {
  const formData = new FormData()
  files.forEach((file) => formData.append(fieldName, file))
  const response = await fetch(`${HOSTED_API_BASE}${path}`, {
    method: 'POST',
    headers: authHeader(token),
    body: formData,
  })
  return parseResponse(response)
}
