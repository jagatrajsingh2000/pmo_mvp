import { AGENT_STEPS } from './constants'
import {
  findDependencyRows,
  findRiskRows,
  findScoreRows,
  findTimelineRows,
  firstUsefulTables,
  getPrimitiveEntries,
} from './jsonReportModel'
import { escapeHtml, humanizeKey, previewText, shortValue } from './utils'

function renderHtmlFacts(data) {
  const primitives = getPrimitiveEntries(data)
  if (!primitives.length) return ''
  return `<div class="json-facts">${primitives.map(([key, value]) => `
    <div><small>${escapeHtml(humanizeKey(key))}</small><strong>${escapeHtml(shortValue(value, 130))}</strong></div>
  `).join('')}</div>`
}

function renderHtmlBars(rows, title) {
  if (!rows.length) return ''
  return `<div class="json-visual-block"><h3>${escapeHtml(title)}</h3><div class="mini-bars">${rows.map((row) => `
    <div class="mini-bar-row">
      <span>${escapeHtml(row.label)}</span>
      <div><i style="width:${row.value}%"></i></div>
      <b>${escapeHtml(Math.round(row.value))}</b>
    </div>
  `).join('')}</div></div>`
}

function renderHtmlTimeline(rows) {
  if (!rows.length) return ''
  const maxDuration = Math.max(...rows.map((row) => Number(row.duration) || 1), 1)
  return `<div class="json-visual-block"><h3>Timeline View</h3><div class="workflow-timeline-chart">${rows.map((row) => {
    const width = Math.max(18, ((Number(row.duration) || 1) / maxDuration) * 100)
    return `
      <div class="workflow-timeline-row">
        <span>${escapeHtml(row.label)}</span>
        <div><i style="width:${width}%">${escapeHtml(row.duration || '')}</i></div>
        <small>${escapeHtml(row.end ? `${row.start} - ${row.end}` : row.start)}</small>
      </div>
    `
  }).join('')}</div></div>`
}

function renderHtmlDependencies(rows) {
  if (!rows.length) return ''
  return `<div class="json-visual-block"><h3>Dependency Map</h3><div class="workflow-dependency-map">${rows.map((row) => `
    <div class="workflow-dependency-edge">
      <span>${escapeHtml(row.source)}</span>
      <b>to</b>
      <span>${escapeHtml(row.target)}</span>
    </div>
  `).join('')}</div></div>`
}

function renderHtmlTable(collection) {
  const rows = collection.rows.slice(0, 8)
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row)))).slice(0, 5)
  if (!rows.length || !columns.length) return ''
  return `<div class="json-visual-block"><h3>${escapeHtml(collection.label)}</h3><table><thead><tr>${columns
    .map((column) => `<th>${escapeHtml(humanizeKey(column))}</th>`)
    .join('')}</tr></thead><tbody>${rows
    .map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(shortValue(row[column], 160))}</td>`).join('')}</tr>`)
    .join('')}</tbody></table></div>`
}

function renderHtmlVisualReport(data) {
  const scoreRows = findScoreRows(data)
  const riskRows = findRiskRows(data)
  const timelineRows = findTimelineRows(data)
  const dependencyRows = findDependencyRows(data)
  const tables = firstUsefulTables(data)
  const visualHtml = [
    renderHtmlFacts(data),
    renderHtmlBars(scoreRows, 'Score Snapshot'),
    renderHtmlBars(riskRows, 'Risk Severity'),
    renderHtmlTimeline(timelineRows),
    renderHtmlDependencies(dependencyRows),
    ...tables.map(renderHtmlTable),
  ].join('')
  return `${visualHtml}<details><summary>View JSON</summary><pre>${escapeHtml(previewText(data, 16000))}</pre></details>`
}

function renderHtmlHandoff(input, handoff) {
  return `
    <div class="agent-handoff-panel">
      <div>
        <h3>Agent Input</h3>
        <pre>${escapeHtml(previewText(input, 12000))}</pre>
      </div>
      <div>
        <h3>Input Given To Next Agent</h3>
        <pre>${escapeHtml(previewText(handoff || { message: 'Final workflow output; no next agent handoff.' }, 12000))}</pre>
      </div>
    </div>
  `
}

function renderHtmlAgentOutput(output) {
  return `
    <div class="agent-output-panel">
      <h3>Agent Output</h3>
      <pre>${escapeHtml(previewText(output?.agentOutput || output?.data, 16000))}</pre>
    </div>
  `
}

export function buildHtmlReport(outputs, sourceName) {
  const generatedAt = new Date().toLocaleString()
  const sections = AGENT_STEPS.map((step) => {
    const output = outputs[step.id]
    if (!output) return ''
    return `
      <section>
        <h2>${escapeHtml(step.title)}</h2>
        <p class="muted">${escapeHtml(step.summary)}</p>
        <dl>
          <dt>Input</dt><dd>${escapeHtml(output.input)}</dd>
          <dt>Output file</dt><dd>${escapeHtml(output.file?.name || output.fileName || 'JSON response')}</dd>
          <dt>Status</dt><dd>${escapeHtml(output.status)}</dd>
          <dt>Elapsed</dt><dd>${escapeHtml(output.elapsed)}</dd>
        </dl>
        ${renderHtmlHandoff(output.agentInput, output.handoff)}
        ${renderHtmlAgentOutput(output)}
        ${renderHtmlVisualReport(output.data)}
      </section>
    `
  }).join('')

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PMO Agent Workflow Report</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; color: #17211d; background: #f4f7f5; }
    main { max-width: 1100px; margin: 0 auto; padding: 32px; }
    h1 { margin: 0 0 8px; font-size: 34px; }
    h2 { margin: 0 0 8px; color: #12352e; }
    section { margin: 18px 0; padding: 20px; background: #fff; border: 1px solid #dbe5e1; border-radius: 8px; page-break-inside: avoid; }
    .muted { color: #5d6c67; }
    dl { display: grid; grid-template-columns: 150px 1fr; gap: 8px 14px; }
    dt { font-weight: 700; color: #31574f; }
    dd { margin: 0; }
    h3 { margin: 0 0 10px; color: #24443d; }
    .json-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 14px 0; }
    .agent-handoff-panel { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
    .json-facts div, .json-visual-block, .agent-output-panel { padding: 12px; background: #f6faf8; border: 1px solid #dbe5e1; border-radius: 8px; }
    .agent-handoff-panel div { padding: 12px; background: #f9fbfa; border: 1px solid #dbe5e1; border-radius: 8px; }
    .json-facts small { display: block; color: #5c6b66; font-weight: 700; }
    .json-facts strong { display: block; margin-top: 4px; overflow-wrap: anywhere; }
    .json-visual-block { margin-top: 12px; }
    .mini-bar-row, .workflow-timeline-row { display: grid; grid-template-columns: 180px minmax(0, 1fr) 70px; gap: 10px; align-items: center; margin: 8px 0; }
    .mini-bar-row div, .workflow-timeline-row div { overflow: hidden; height: 24px; background: #dde9e5; border-radius: 6px; }
    .mini-bar-row i, .workflow-timeline-row i { display: block; height: 100%; background: #2f6f62; color: #fff; font-style: normal; font-weight: 700; text-align: center; line-height: 24px; border-radius: inherit; }
    .workflow-timeline-row i { background: #ec2c6f; }
    .workflow-dependency-edge { display: inline-grid; grid-template-columns: minmax(130px, 1fr) 38px minmax(130px, 1fr); gap: 8px; align-items: center; margin: 6px; }
    .workflow-dependency-edge span { padding: 8px; background: #eaf3ef; border: 1px solid #c9dcd5; border-radius: 6px; }
    .workflow-dependency-edge b { text-align: center; color: #ec2c6f; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    th, td { padding: 8px; border: 1px solid #d2dfda; text-align: left; vertical-align: top; }
    th { background: #dcebe6; }
    pre { max-height: 560px; overflow: auto; padding: 14px; color: #eaf7f3; background: #14221f; border-radius: 8px; white-space: pre-wrap; }
    @media (max-width: 760px) { .json-facts, .agent-handoff-panel, .mini-bar-row, .workflow-timeline-row { grid-template-columns: 1fr; } main { padding: 14px; } }
  </style>
</head>
<body>
  <main>
    <h1>PMO Agent Workflow Report</h1>
    <p class="muted">Generated ${escapeHtml(generatedAt)} from ${escapeHtml(sourceName)}.</p>
    ${sections}
  </main>
</body>
</html>`
}
