import React from 'react'
import { downloadReportHtml, printReportPdf } from './reportExport'
import { StructuredResult } from './resultRenderer'

export function FlowBar({ agents, steps, selectedId, onSelect }) {
  const states = agents.map((agent) => steps[agent.id]?.status || 'queued')
  const runningIndex = states.findIndex((status) => status === 'running')
  const doneCount = states.filter((status) => status === 'done').length
  const progress = flowProgress(agents.length, runningIndex, doneCount)

  return (
    <div
      className={`v2-flow ${runningIndex >= 0 ? 'running' : ''} ${doneCount === agents.length ? 'complete' : ''}`}
      aria-label="Agent flow"
      style={{
        '--v2-flow-progress': `${progress.line}%`,
        '--v2-flow-runner': `${progress.runner}%`,
      }}
    >
      <span className="v2-flow-track" aria-hidden="true">
        <span className="v2-flow-progress" />
        {runningIndex >= 0 && <span className="v2-flow-runner" />}
      </span>
      {agents.map((agent, index) => {
        const state = states[index]
        return (
          <React.Fragment key={agent.id}>
            {index > 0 && <span className={`v2-flow-line ${state}`} />}
            <button
              type="button"
              className={`v2-flow-node ${state} ${selectedId === agent.id ? 'selected' : ''}`}
              onClick={() => onSelect(agent.id)}
              title={agent.title}
            >
              <span className="v2-flow-circle">{agent.number}</span>
              <strong>{shortAgentTitle(agent.title)}</strong>
            </button>
          </React.Fragment>
        )
      })}
    </div>
  )
}

export function AgentCard({ agent, state, output, selected, onOpen }) {
  const status = state?.status || 'queued'
  const completion = completionState(status, Boolean(output))
  return (
    <article
      id={`workflow-v2-card-${agent.id}`}
      className={`v2-agent-card ${status} ${selected ? 'selected' : ''}`}
    >
      <div className="v2-card-top">
        <span className="v2-card-number">{shortAgentTitle(agent.title)}</span>
        <span className={`v2-status ${status}`}>{statusLabel(status)}</span>
      </div>
      <h2>{agent.title}</h2>
      <p>{agent.summary}</p>
      <div className="v2-card-completion">
        <div>
          <span>Completion</span>
          <strong>{completion.label}</strong>
        </div>
        <div className="v2-card-progress" aria-label={`${completion.percent}% complete`}>
          <span style={{ width: `${completion.percent}%` }} />
        </div>
      </div>
      <button type="button" className="v2-card-action" onClick={onOpen} disabled={!output}>
        {output ? 'Open Report' : completion.button}
      </button>
    </article>
  )
}

export function ResultModal({ agent, output, onClose }) {
  const reportRef = React.useRef(null)
  if (!agent || !output) return null

  function exportHtml() {
    downloadReportHtml(agent, reportRef.current?.innerHTML || '')
  }

  function exportPdf() {
    printReportPdf(agent, reportRef.current?.innerHTML || '')
  }

  return (
    <div className="v2-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="v2-modal" role="dialog" aria-modal="true" aria-labelledby="v2-modal-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="v2-modal-header">
          <div>
            <p>Agent Result</p>
            <h2 id="v2-modal-title">{agent.title}</h2>
          </div>
          <div className="v2-modal-actions">
            <button type="button" className="v2-export" onClick={exportPdf}>PDF</button>
            <button type="button" className="v2-export" onClick={exportHtml}>HTML</button>
            <button type="button" className="v2-close" onClick={onClose}>Close</button>
          </div>
        </header>

        <section className="v2-modal-section" ref={reportRef}>
          <h3>Agent Output</h3>
          <StructuredResult data={output.data} />
        </section>
      </section>
    </div>
  )
}

function statusLabel(status) {
  if (status === 'done') return 'Complete'
  if (status === 'running') return 'Running'
  if (status === 'failed') return 'Failed'
  return 'Queued'
}

function completionState(status, hasOutput) {
  if (hasOutput || status === 'done') return { label: '100% complete', percent: 100, button: 'Open Report' }
  if (status === 'running') return { label: 'In progress', percent: 58, button: 'Running' }
  if (status === 'failed') return { label: 'Needs attention', percent: 100, button: 'Failed' }
  return { label: 'Waiting to start', percent: 0, button: 'Waiting' }
}

function flowProgress(agentCount, runningIndex, doneCount) {
  if (agentCount <= 1) return { line: doneCount ? 100 : 0, runner: 0 }
  if (doneCount === agentCount) return { line: 100, runner: 100 }
  if (runningIndex >= 0) {
    const percent = (runningIndex / (agentCount - 1)) * 100
    return { line: percent, runner: percent }
  }
  const completedIndex = Math.max(0, doneCount - 1)
  const percent = (completedIndex / (agentCount - 1)) * 100
  return { line: percent, runner: percent }
}

function shortAgentTitle(title) {
  return String(title || '').replace(/\s+Agent$/i, '').replace(/\s+Report$/i, '')
}
