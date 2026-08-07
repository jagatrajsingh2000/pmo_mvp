import React from 'react'
import { PlannerVisuals, plannerData } from './plannerVisuals'
import { labelize } from './utils'

const HIDDEN_FIELD_PATTERN = /(base64|binary|blob|bytes|content_base64|docx_base64|document_base64|file_base64|^source_text$|^extracted_text$|^raw_text$|^document_text$|^input_text$|^full_text$|^ocr_text$|^text_content$|^document_content$|^sourceText$|^extractedText$|^rawText$|^documentText$|^inputText$|^fullText$|^ocrText$|^textContent$|^documentContent$)/i
const LONG_TEXT_LIMIT = 520
const RESPONSE_META_KEYS = ['demand_id', 'filename', 'ingestion_metadata']
const EXECUTIVE_HIDDEN_KEYS = ['file_ids', 'source_files', 'files', 'uploaded_files', 'input_files']
const BUDGET_HIDDEN_KEYS = ['file_id', 'source_text_chars', 'source_text', 'extracted_text']
const SECTION_LABELS = {
  non_functional_requirements: 'Non-Functional Requirements',
  raid: 'Risks, Assumptions, Issues, Decisions',
  acceptance_criteria_testing: 'Acceptance Criteria & Testing',
  rollout_change_management: 'Rollout & Change Management',
  governance_signoff: 'Governance & Sign-off',
}

export function StructuredResult({ data, agentId }) {
  const { main, meta } = normalizeResult(data, agentId)
  const sections = renderableEntries(filterAgentSections(main, agentId))
  const titles = agentId === 'brd' ? displayedSectionTiles(sections) : []
  const metaRows = renderableEntries(omitKeys(meta, ['titles']))
  const metrics = sectionMetrics(main)

  if (!sections.length && !metaRows.length && !titles.length) {
    return <p className="v2-muted">No displayable agent output returned.</p>
  }

  return (
    <div className="v2-structured-result">
      {titles.length > 0 && <TitleOutline titles={titles} />}
      {agentId === 'planner' && <PlannerVisuals data={data} />}

      {metaRows.length > 0 && (
        <section className="v2-output-section compact">
          <header>
            <h3>Response Details</h3>
            <span>{metaRows.length} fields</span>
          </header>
          <KeyValueGrid entries={metaRows} />
        </section>
      )}

      {metrics.length > 0 && (
        <section className="v2-output-section compact">
          <header>
            <h3>Output Coverage</h3>
            <span>{metrics.length} populated sections</span>
          </header>
          <div className="v2-metric-bars">
            {metrics.map((metric) => (
              <div className="v2-metric-bar" key={metric.label}>
                <div>
                  <strong>{metric.label}</strong>
                  <span>{metric.count} items</span>
                </div>
                <em style={{ width: `${metric.width}%` }} />
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="v2-section-stack">
        {sections.map(([key, value]) => (
          <SectionBlock key={key} name={key} value={value} level={0} />
        ))}
      </div>
    </div>
  )
}

function filterAgentSections(main, agentId) {
  if (agentId === 'executive') return omitKeys(main, EXECUTIVE_HIDDEN_KEYS)
  if (agentId === 'budget') return omitKeys(main, BUDGET_HIDDEN_KEYS)
  return main
}

function normalizeResult(data, agentId) {
  if (!data || typeof data !== 'object') return { main: { output: data }, meta: {} }
  if (Array.isArray(data)) return { main: { output: data }, meta: {} }

  if (agentId === 'planner') {
    return {
      main: omitKeys(plannerData(data), RESPONSE_META_KEYS),
      meta: {},
    }
  }

  if (isPlainObject(data.resolved)) {
    return {
      main: data.resolved,
      meta: omitKeys(data, ['resolved', 'source', ...RESPONSE_META_KEYS]),
    }
  }

  const candidate =
    firstPlainObject(data.report) ||
    firstPlainObject(data.output) ||
    firstPlainObject(data.result) ||
    firstPlainObject(data.data)

  if (candidate) {
    return {
      main: omitKeys(candidate, RESPONSE_META_KEYS),
      meta: omitKeys(data, ['report', 'output', 'result', 'data', 'source', ...RESPONSE_META_KEYS]),
    }
  }

  return { main: omitKeys(data, RESPONSE_META_KEYS), meta: {} }
}

function TitleOutline({ titles }) {
  return (
    <section className="v2-title-outline">
      <header>
        <div>
          <h3>Displayed Sections</h3>
          <p>Only sections currently rendered in this report.</p>
        </div>
        <span>{titles.length} sections</span>
      </header>
      <div className="v2-title-grid">
        {titles.map((item) => (
          <article className="v2-title-card" key={`${item.number}-${item.title}`}>
            <span>{item.number}</span>
            <strong>{item.title}</strong>
          </article>
        ))}
      </div>
    </section>
  )
}

function SectionBlock({ name, value, level }) {
  return (
    <section className={`v2-output-section level-${Math.min(level, 2)}`}>
      <header>
        <h3>{sectionLabel(name)}</h3>
        <span>{describeValue(value)}</span>
      </header>
      <ValueBlock value={value} level={level} />
    </section>
  )
}

function ValueBlock({ value, level }) {
  if (isEmptyValue(value)) return <p className="v2-muted">No entries returned.</p>

  if (isSimpleValue(value)) return <p className="v2-output-text">{formatSimple(value)}</p>

  if (Array.isArray(value)) {
    if (!value.length) return <p className="v2-muted">No entries returned.</p>
    if (value.every(isPlainObject)) return <ObjectTable rows={value} />
    return <PrimitiveList items={value} />
  }

  if (isPlainObject(value)) {
    const entries = renderableEntries(value)
    const simpleEntries = entries.filter(([, entryValue]) => isCompactValue(entryValue))
    const complexEntries = entries.filter(([, entryValue]) => !isCompactValue(entryValue))

    return (
      <>
        {simpleEntries.length > 0 && <KeyValueGrid entries={simpleEntries} />}
        {complexEntries.length > 0 && (
          <div className="v2-nested-sections">
            {complexEntries.map(([key, entryValue]) => (
              <SectionBlock key={key} name={key} value={entryValue} level={level + 1} />
            ))}
          </div>
        )}
      </>
    )
  }

  return <p className="v2-output-text">{String(value)}</p>
}

function ObjectTable({ rows }) {
  const columns = Array.from(
    rows.reduce((keys, row) => {
      renderableEntries(row).forEach(([key]) => keys.add(key))
      return keys
    }, new Set()),
  )

  if (!columns.length) return <p className="v2-muted">No displayable fields returned.</p>

  return (
    <div className="v2-output-table-wrap">
      <table className="v2-output-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{labelize(column)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={stableRowKey(row, index)}>
              {columns.map((column) => (
                <td key={column}>{formatCell(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function KeyValueGrid({ entries }) {
  return (
    <dl className="v2-kv-grid">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{labelize(key)}</dt>
          <dd>{formatCell(value)}</dd>
        </div>
      ))}
    </dl>
  )
}

function PrimitiveList({ items }) {
  return (
    <ul className="v2-output-list">
      {items.map((item, index) => (
        <li key={`${String(item).slice(0, 40)}-${index}`}>{formatCell(item)}</li>
      ))}
    </ul>
  )
}

function sectionMetrics(value) {
  if (!isPlainObject(value)) return []
  const metrics = renderableEntries(value)
    .map(([key, entryValue]) => [sectionLabel(key), countEntries(entryValue)])
    .filter(([, count]) => count > 0)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 8)

  const max = Math.max(...metrics.map(([, count]) => count), 1)
  return metrics.map(([label, count]) => ({
    label,
    count,
    width: Math.max(8, Math.round((count / max) * 100)),
  }))
}

function countEntries(value) {
  if (Array.isArray(value)) return value.length
  if (isPlainObject(value)) return renderableEntries(value).reduce((total, [, entryValue]) => total + countEntries(entryValue), 0)
  return isEmptyValue(value) ? 0 : 1
}

function formatCell(value) {
  if (isEmptyValue(value)) return '-'
  if (isSimpleValue(value)) return formatSimple(value)
  if (Array.isArray(value)) {
    if (!value.length) return '-'
    if (value.every(isSimpleValue)) return value.map(formatSimple).join(', ')
    return `${value.length} items`
  }
  if (isPlainObject(value)) {
    const entries = renderableEntries(value)
    if (!entries.length) return '-'
    if (entries.every(([, entryValue]) => isCompactValue(entryValue))) {
      return entries.map(([key, entryValue]) => `${labelize(key)}: ${formatCell(entryValue)}`).join(' | ')
    }
    return `${entries.length} fields`
  }
  return String(value)
}

function formatSimple(value) {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  const text = String(value)
  if (text.length <= LONG_TEXT_LIMIT) return text
  return `${text.slice(0, LONG_TEXT_LIMIT).trim()}...`
}

function describeValue(value) {
  if (Array.isArray(value)) return `${value.length} items`
  if (isPlainObject(value)) return `${renderableEntries(value).length} fields`
  if (isEmptyValue(value)) return 'Empty'
  return 'Value'
}

function renderableEntries(value) {
  if (!isPlainObject(value)) return []
  return Object.entries(value).filter(([key, entryValue]) => !HIDDEN_FIELD_PATTERN.test(key) && !isEmptyValue(entryValue))
}

function displayedSectionTiles(sections) {
  return sections.map(([key], index) => ({
    number: index + 1,
    title: sectionLabel(key),
  }))
}

function sectionLabel(key) {
  return SECTION_LABELS[key] || labelize(key)
}

function omitKeys(value, keys) {
  if (!isPlainObject(value)) return {}
  const skipped = new Set(keys)
  return Object.fromEntries(Object.entries(value).filter(([key]) => !skipped.has(key) && !HIDDEN_FIELD_PATTERN.test(key)))
}

function firstPlainObject(value) {
  return isPlainObject(value) ? value : null
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function isSimpleValue(value) {
  return ['string', 'number', 'boolean'].includes(typeof value)
}

function isCompactValue(value) {
  return isSimpleValue(value) || (Array.isArray(value) && value.every(isSimpleValue))
}

function isEmptyValue(value) {
  if (value == null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (isPlainObject(value)) return renderableEntries(value).length === 0
  return false
}

function stableRowKey(row, index) {
  return row.id || row.req_id || row.nfr_id || row.task_id || row.name || row.title || index
}
