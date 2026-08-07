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
