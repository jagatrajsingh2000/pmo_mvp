const PDF_LINE_LIMIT = 92
const PDF_LINES_PER_PAGE = 58
const HIDDEN_FIELD_PATTERN = /(base64|binary|blob|bytes|content_base64|docx_base64|document_base64|file_base64)/i

export function createHandoffArtifacts(agentTitle, baseName, data) {
  const safeData = stripBinaryFields(data)
  const jsonText = JSON.stringify(safeData, null, 2)
  return [
    {
      type: 'json',
      label: 'JSON',
      file: new File([jsonText], `${baseName}.json`, { type: 'application/json' }),
    },
    {
      type: 'pdf',
      label: 'PDF',
      file: createPdfFile(`${baseName}.pdf`, agentTitle, jsonText),
    },
    {
      type: 'html',
      label: 'HTML',
      file: new File([createHtmlReport(agentTitle, jsonText)], `${baseName}.html`, { type: 'text/html' }),
    },
  ]
}

export async function requestFileWithArtifacts(path, artifacts, requestFile, token) {
  const errors = []
  for (const artifact of artifacts) {
    try {
      const response = await requestFile(path, 'file', artifact.file, token)
      return { response, artifact }
    } catch (error) {
      errors.push(`${artifact.label}: ${error.message || 'failed'}`)
    }
  }
  throw new Error(`${path} failed for JSON, PDF, and HTML inputs. ${errors.join(' | ')}`)
}

export async function requestFilesWithArtifactGroups(path, artifactGroups, requestFiles, token) {
  const errors = []
  for (const group of artifactGroups) {
    try {
      const response = await requestFiles(path, 'files', group.files, token)
      return { response, group }
    } catch (error) {
      errors.push(`${group.label}: ${error.message || 'failed'}`)
    }
  }
  throw new Error(`${path} failed for JSON, PDF, and HTML inputs. ${errors.join(' | ')}`)
}

export function groupArtifactsByType(artifactSets) {
  return ['json', 'pdf', 'html'].map((type) => ({
    type,
    label: type.toUpperCase(),
    files: artifactSets.map((artifacts) => artifacts.find((artifact) => artifact.type === type)?.file).filter(Boolean),
  }))
}

function createHtmlReport(title, jsonText) {
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(title)}</title>
  </head>
  <body>
    <main>
      <h1>${escapeHtml(title)}</h1>
      <pre>${escapeHtml(jsonText)}</pre>
    </main>
  </body>
</html>`
}

function createPdfFile(fileName, title, text) {
  const lines = wrapLines([title, '', ...text.split(/\r?\n/)])
  const pages = chunk(lines, PDF_LINES_PER_PAGE)
  const objects = []

  const addObject = (body) => {
    objects.push(body)
    return objects.length
  }

  const fontId = addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
  const pageIds = []

  pages.forEach((pageLines) => {
    const content = [
      'BT',
      '/F1 9 Tf',
      '40 780 Td',
      '12 TL',
      ...pageLines.map((line) => `(${escapePdfText(line)}) Tj T*`),
      'ET',
    ].join('\n')
    const contentId = addObject(`<< /Length ${byteLength(content)} >>\nstream\n${content}\nendstream`)
    const pageId = addObject(`<< /Type /Page /Parent __PAGES__  /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`)
    pageIds.push(pageId)
  })

  const pagesId = addObject(`<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}] /Count ${pageIds.length} >>`)
  const catalogId = addObject(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`)

  const renderedObjects = objects.map((body) => body.replace('__PAGES__', `${pagesId} 0 R`))
  let pdf = '%PDF-1.4\n'
  const offsets = [0]
  renderedObjects.forEach((body, index) => {
    offsets.push(byteLength(pdf))
    pdf += `${index + 1} 0 obj\n${body}\nendobj\n`
  })

  const xrefOffset = byteLength(pdf)
  pdf += `xref\n0 ${renderedObjects.length + 1}\n0000000000 65535 f \n`
  offsets.slice(1).forEach((offset) => {
    pdf += `${String(offset).padStart(10, '0')} 00000 n \n`
  })
  pdf += `trailer\n<< /Size ${renderedObjects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`

  return new File([pdf], fileName, { type: 'application/pdf' })
}

function stripBinaryFields(value) {
  if (Array.isArray(value)) return value.map(stripBinaryFields)
  if (!value || typeof value !== 'object') return value
  return Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => !HIDDEN_FIELD_PATTERN.test(key))
      .map(([key, entryValue]) => [key, stripBinaryFields(entryValue)]),
  )
}

function wrapLines(lines) {
  return lines.flatMap((line) => {
    const clean = asciiOnly(String(line || ''))
    if (clean.length <= PDF_LINE_LIMIT) return [clean]
    const wrapped = []
    for (let index = 0; index < clean.length; index += PDF_LINE_LIMIT) {
      wrapped.push(clean.slice(index, index + PDF_LINE_LIMIT))
    }
    return wrapped
  })
}

function chunk(items, size) {
  const chunks = []
  for (let index = 0; index < items.length; index += size) chunks.push(items.slice(index, index + size))
  return chunks.length ? chunks : [[]]
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function escapePdfText(value) {
  return asciiOnly(value).replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)')
}

function asciiOnly(value) {
  return String(value).replace(/[^\x20-\x7E]/g, '?')
}

function byteLength(value) {
  return new Blob([value]).size
}
