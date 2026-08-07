const REPORT_STYLES = `
  body {
    margin: 0;
    background: #f4f5f2;
    color: #151715;
    font-family: Arial, Helvetica, sans-serif;
  }

  main {
    max-width: 1120px;
    margin: 0 auto;
    padding: 32px;
  }

  .report-shell {
    background: #ffffff;
    border: 1px solid #dfe4df;
    border-radius: 8px;
    padding: 28px;
  }

  .report-kicker {
    color: #756100;
    font-size: 12px;
    font-weight: 900;
    text-transform: uppercase;
  }

  h1 {
    margin: 6px 0 22px;
    font-size: 40px;
    line-height: 1;
  }

  .v2-structured-result,
  .v2-section-stack,
  .v2-nested-sections {
    display: grid;
    gap: 12px;
  }

  .v2-title-outline {
    overflow: hidden;
    border: 1px solid #dfe4df;
    border-radius: 8px;
    background: #ffffff;
    break-inside: avoid;
  }

  .v2-title-outline header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    background: #151715;
    color: #ffffff;
    padding: 16px;
  }

  .v2-title-outline h3 {
    margin: 0;
    font-size: 20px;
  }

  .v2-title-outline p {
    margin: 5px 0 0;
    color: #d9ded9;
    line-height: 1.4;
  }

  .v2-title-outline header span {
    border: 1px solid rgba(255, 216, 61, 0.55);
    border-radius: 999px;
    color: #ffd83d;
    font-size: 12px;
    font-weight: 900;
    padding: 7px 10px;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .v2-title-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 10px;
    padding: 14px;
  }

  .v2-title-card {
    display: flex;
    gap: 10px;
    align-items: center;
    min-height: 54px;
    border: 1px solid #e0e5e0;
    border-radius: 8px;
    background: #fbfcfb;
    padding: 10px;
  }

  .v2-title-card span {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 999px;
    background: #ffd83d;
    color: #151715;
    font-size: 13px;
    font-weight: 900;
  }

  .v2-title-card strong {
    color: #252925;
    font-size: 13px;
    line-height: 1.25;
  }

  .v2-planner-visuals {
    overflow: hidden;
    border: 1px solid #dfe4df;
    border-radius: 8px;
    background: #ffffff;
    break-inside: avoid;
  }

  .v2-planner-visuals > header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    background: #151715;
    color: #ffffff;
    padding: 22px 24px;
  }

  .v2-planner-visuals h3,
  .v2-planner-visuals h4 {
    margin: 0;
  }

  .v2-planner-visuals p {
    max-width: 980px;
    margin: 8px 0 0;
    color: #d9ded9;
    font-weight: 700;
  }

  .v2-planner-visuals > header span {
    border: 1px solid rgba(255, 216, 61, 0.55);
    border-radius: 999px;
    color: #ffd83d;
    font-size: 12px;
    font-weight: 900;
    padding: 9px 12px;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .v2-planner-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    gap: 14px;
    align-items: start;
    padding: 14px;
  }

  .v2-visual-panel {
    border: 1px solid #cfdcda;
    border-radius: 8px;
    background:
      linear-gradient(rgba(25, 47, 55, 0.05) 1px, transparent 1px),
      linear-gradient(90deg, rgba(25, 47, 55, 0.05) 1px, transparent 1px),
      #fbfcfb;
    background-size: 36px 36px;
    padding: 18px;
    break-inside: avoid;
  }

  .v2-visual-panel.wide {
    grid-column: 1 / -1;
  }

  .v2-visual-panel h4 {
    font-size: 22px;
    text-align: center;
    margin-bottom: 18px;
  }

  .v2-gantt,
  .v2-gate-grid,
  .v2-risk-bars {
    display: grid;
    gap: 8px;
  }

  .v2-gantt-scale {
    display: flex;
    justify-content: space-between;
    color: #5d6b66;
    font-size: 12px;
    font-weight: 800;
  }

  .v2-gantt-row,
  .v2-risk-row {
    display: grid;
    grid-template-columns: minmax(120px, 220px) minmax(240px, 1fr);
    gap: 10px;
    align-items: center;
  }

  .v2-gantt-label,
  .v2-risk-row span {
    overflow: hidden;
    color: #51625c;
    font-size: 12px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .v2-gantt-track,
  .v2-risk-row div {
    position: relative;
    min-height: 34px;
    overflow: hidden;
    border: 1px solid #b9c7c4;
    background: #ffffff;
  }

  .v2-gantt-bar {
    position: absolute;
    top: 5px;
    height: 24px;
    overflow: hidden;
    border: 2px solid rgba(17, 28, 32, 0.72);
    color: #111c20;
    font-size: 12px;
    font-weight: 900;
    line-height: 20px;
    padding: 0 8px;
    text-align: center;
    white-space: nowrap;
  }

  .v2-gantt-bar.phase-0 { background: #2b9bd8; }
  .v2-gantt-bar.phase-1 { background: #20a53a; }
  .v2-gantt-bar.phase-2 { background: #f0b51b; }
  .v2-gantt-bar.phase-3 { background: #e7651a; }
  .v2-gantt-bar.phase-4 { background: #a12a84; color: #ffffff; }
  .v2-gantt-bar.phase-5 { background: #1d64c8; color: #ffffff; }

  .v2-gate-grid {
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 12px;
  }

  .v2-gate-item {
    display: grid;
    grid-template-rows: auto 1fr auto;
    gap: 10px;
    min-height: 124px;
    border: 1px solid #cad8d4;
    border-left: 7px solid #151715;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.8);
    padding: 14px;
  }

  .v2-gate-item span {
    width: fit-content;
    border-radius: 999px;
    background: #ffd83d;
    color: #151715;
    font-size: 12px;
    font-weight: 900;
    padding: 5px 10px;
  }

  .v2-critical-flow {
    display: flex;
    align-items: center;
    gap: 10px;
    overflow-x: auto;
    padding: 20px 4px;
  }

  .v2-flow-card {
    display: grid;
    place-items: center;
    min-width: 142px;
    min-height: 70px;
    border: 3px solid #151715;
    background: #eef3f1;
    padding: 10px;
    text-align: center;
  }

  .v2-flow-arrow {
    font-size: 24px;
    font-weight: 900;
  }

  .v2-node-map {
    display: grid;
    grid-template-columns: repeat(4, minmax(90px, 1fr));
    gap: 18px;
    padding: 18px 10px;
  }

  .v2-map-node {
    display: grid;
    place-items: center;
    min-height: 54px;
    border: 3px solid #447a2f;
    background: #e9f0df;
    font-size: 12px;
    font-weight: 900;
    padding: 8px;
    text-align: center;
  }

  .v2-effort-bars {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(76px, 1fr));
    gap: 14px;
    align-items: end;
    min-height: 230px;
  }

  .v2-effort-item {
    display: grid;
    grid-template-rows: 150px auto auto;
    gap: 7px;
    align-items: end;
    justify-items: center;
  }

  .v2-effort-bar {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    width: 100%;
    max-width: 70px;
    border: 2px solid rgba(17, 28, 32, 0.72);
    background: #f0b51b;
    padding-top: 5px;
  }

  .v2-effort-bar.level-high,
  .v2-risk-row .severity-high { background: #d91818; color: #ffffff; }
  .v2-effort-bar.level-medium,
  .v2-risk-row .severity-medium { background: #f0b51b; }
  .v2-effort-bar.level-low,
  .v2-risk-row .severity-low { background: #27bb2f; }

  .v2-risk-row {
    grid-template-columns: minmax(140px, 220px) minmax(160px, 1fr) 76px;
  }

  .v2-risk-row em {
    display: block;
    height: 100%;
    min-height: 28px;
  }

  .v2-output-section {
    border: 1px solid #dfe4df;
    border-radius: 8px;
    background: #ffffff;
    overflow: hidden;
    break-inside: avoid;
  }

  .v2-output-section header {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
    background: #f3f5f2;
    border-bottom: 1px solid #dfe4df;
    padding: 12px 14px;
  }

  .v2-output-section.level-1 header,
  .v2-output-section.level-2 header {
    background: #fff8cb;
  }

  .v2-output-section h3 {
    margin: 0;
    font-size: 16px;
  }

  .v2-output-section header span,
  .v2-kv-grid dt {
    color: #626862;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
  }

  .v2-output-text {
    margin: 0;
    line-height: 1.55;
    padding: 14px;
    white-space: pre-wrap;
  }

  .v2-kv-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin: 0;
    padding: 14px;
  }

  .v2-kv-grid div {
    border-left: 4px solid #ffd83d;
    background: #ffffff;
    padding: 8px 10px;
  }

  .v2-kv-grid dd {
    margin: 4px 0 0;
    line-height: 1.45;
  }

  .v2-output-table-wrap {
    overflow-x: auto;
    padding: 14px;
  }

  .v2-output-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .v2-output-table th,
  .v2-output-table td {
    border: 1px solid #dfe4df;
    padding: 9px;
    text-align: left;
    vertical-align: top;
  }

  .v2-output-table th {
    background: #151715;
    color: #ffffff;
    font-size: 10px;
    text-transform: uppercase;
  }

  .v2-output-list {
    display: grid;
    gap: 8px;
    margin: 0;
    padding: 14px 18px 14px 32px;
  }

  .v2-metric-bars {
    display: grid;
    gap: 10px;
    padding: 14px;
  }

  .v2-metric-bar {
    position: relative;
    min-height: 42px;
    overflow: hidden;
    border: 1px solid #e1e5df;
    border-radius: 8px;
    background: #ffffff;
  }

  .v2-metric-bar div {
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 42px;
    padding: 0 12px;
  }

  .v2-metric-bar em {
    position: absolute;
    inset: 0 auto 0 0;
    background: rgba(255, 216, 61, 0.58);
  }

  .v2-muted {
    color: #6a706a;
  }

  @media print {
    body {
      background: #ffffff;
    }

    main {
      max-width: none;
      padding: 0;
    }

    .report-shell {
      border: 0;
      padding: 0;
    }
  }
`

export function downloadReportHtml(agent, html) {
  const reportHtml = buildReportHtml(agent, html)
  const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${fileSlug(agent?.title || 'agent-report')}.html`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function downloadCombinedReportHtml(html) {
  const reportHtml = buildReportHtml({ title: 'Combined PMO Workflow Report' }, html)
  const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'combined-pmo-workflow-report.html'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function printCombinedReportPdf(html) {
  printReportPdf({ title: 'Combined PMO Workflow Report' }, html)
}

export function printReportPdf(agent, html) {
  const reportWindow = window.open('', '_blank')
  if (!reportWindow) {
    window.alert('Please allow popups to export the report as PDF.')
    return
  }

  reportWindow.document.open()
  reportWindow.document.write(buildReportHtml(agent, html, true))
  reportWindow.document.close()
}

function buildReportHtml(agent, html, autoPrint = false) {
  const title = escapeHtml(agent?.title || 'Agent Report')
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title}</title>
    <style>${REPORT_STYLES}</style>
  </head>
  <body>
    <main>
      <section class="report-shell">
        <div class="report-kicker">Agent Report</div>
        <h1>${title}</h1>
        ${html || '<p class="v2-muted">No report content available.</p>'}
      </section>
    </main>
    ${autoPrint ? '<script>window.addEventListener("load", function () { setTimeout(function () { window.focus(); window.print(); }, 250); });</script>' : ''}
  </body>
</html>`
}

function fileSlug(value) {
  return String(value || 'agent-report')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}
