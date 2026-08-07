import React from 'react'
import { fileBrief, getPayloadSize, resultSummary, stringifyJson } from './utils'

export function FlowBar({ agents, steps, selectedId, onSelect }) {
  return (
    <div className="v2-flow" aria-label="Agent flow">
      {agents.map((agent, index) => {
        const state = steps[agent.id]?.status || 'queued'
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
  return (
    <button
      id={`workflow-v2-card-${agent.id}`}
      type="button"
      className={`v2-agent-card ${status} ${selected ? 'selected' : ''}`}
      onClick={onOpen}
    >
      <div className="v2-card-top">
        <span className="v2-card-number">{shortAgentTitle(agent.title)}</span>
        <span className={`v2-status ${status}`}>{statusLabel(status)}</span>
      </div>
      <h2>{agent.title}</h2>
      <p>{agent.summary}</p>
      <dl>
        <div>
          <dt>Stage</dt>
          <dd>Runs after {agent.after || 'source intake'}</dd>
        </div>
        <div>
          <dt>Input</dt>
          <dd>{agent.input}</dd>
        </div>
        <div>
          <dt>Result</dt>
          <dd>{output ? `${getPayloadSize(output.data)} JSON` : state?.detail || 'Waiting'}</dd>
        </div>
      </dl>
    </button>
  )
}

export function ResultModal({ agent, output, onClose }) {
  if (!agent || !output) return null
  const summaryRows = resultSummary(output.data)
  return (
    <div className="v2-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="v2-modal" role="dialog" aria-modal="true" aria-labelledby="v2-modal-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="v2-modal-header">
          <div>
            <p>Agent Result</p>
            <h2 id="v2-modal-title">{agent.title}</h2>
          </div>
          <button type="button" className="v2-close" onClick={onClose}>Close</button>
        </header>

        <div className="v2-modal-meta">
          <InfoBox label="Status" value={output.status} />
          <InfoBox label="Elapsed" value={output.elapsed || '-'} />
          <InfoBox label="Agent" value={agent.title} />
          <InfoBox label="Payload" value={getPayloadSize(output.data)} />
        </div>

        <section className="v2-modal-section">
          <h3>Inputs</h3>
          <div className="v2-file-list">
            {output.inputFiles?.length ? (
              output.inputFiles.map((file) => <FilePill key={`${file.name}-${file.size}`} file={file} />)
            ) : (
              <span className="v2-muted">No file metadata available.</span>
            )}
          </div>
        </section>

        <section className="v2-modal-section">
          <h3>Result Overview</h3>
          <div className="v2-result-grid">
            {summaryRows.length ? (
              summaryRows.map(([label, value]) => <InfoBox key={label} label={label} value={value} />)
            ) : (
              <span className="v2-muted">No summary fields available.</span>
            )}
          </div>
        </section>

        <section className="v2-modal-section">
          <h3>Raw Agent JSON</h3>
          <pre className="v2-json">{stringifyJson(output.data)}</pre>
        </section>
      </section>
    </div>
  )
}

function InfoBox({ label, value }) {
  return (
    <div className="v2-info-box">
      <span>{label}</span>
      <strong>{String(value ?? '-')}</strong>
    </div>
  )
}

function FilePill({ file }) {
  const brief = fileBrief(file)
  return (
    <span className="v2-file-pill">
      {brief?.name || 'file'}
      <small>{brief?.size || '-'}</small>
    </span>
  )
}

function statusLabel(status) {
  if (status === 'done') return 'Complete'
  if (status === 'running') return 'Running'
  if (status === 'failed') return 'Failed'
  return 'Queued'
}

function shortAgentTitle(title) {
  return String(title || '').replace(/\s+Agent$/i, '').replace(/\s+Report$/i, '')
}
