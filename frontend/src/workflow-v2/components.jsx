import React from 'react'
import { StructuredResult } from './resultRenderer'

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
  if (!agent || !output) return null
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

        <section className="v2-modal-section">
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

function shortAgentTitle(title) {
  return String(title || '').replace(/\s+Agent$/i, '').replace(/\s+Report$/i, '')
}
