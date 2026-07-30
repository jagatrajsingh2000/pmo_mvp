import React, { useState } from 'react'

const API_BASE = 'http://localhost:8000'

function asArray(value) {
  if (!value) return []
  return Array.isArray(value) ? value : [value]
}

function Section({ title, children }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {children}
    </section>
  )
}

function KeyValueTable({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <th>{label}</th>
              <td>{Array.isArray(value) ? value.join(', ') : String(value ?? '-')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ScheduleTable({ tasks }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Task</th>
            <th>Owner</th>
            <th>Start</th>
            <th>End</th>
            <th>Deps</th>
          </tr>
        </thead>
        <tbody>
          {asArray(tasks).map((task) => (
            <tr key={task.id || task.name}>
              <td>{task.id}</td>
              <td>{task.name}</td>
              <td>{task.owner_role}</td>
              <td>{task.start_date}</td>
              <td>{task.end_date}</td>
              <td>{asArray(task.dependencies).join(', ') || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ListBlock({ items, render }) {
  const list = asArray(items)
  if (!list.length) return <p className="muted">No items generated.</p>
  return (
    <ul className="stack-list">
      {list.map((item, index) => (
        <li key={item.id || item.code || item.name || index}>{render ? render(item) : String(item)}</li>
      ))}
    </ul>
  )
}

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const generated = result?.generated || {}
  const review = result?.review || {}

  async function submit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setError('')
    setResult(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: fd,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setResult(data)
    } catch (err) {
      console.error(err)
      setError(err.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Project Timeline Planner Agent</p>
          <h1>Generate WBS, sprint plan, dependencies, and schedule risks</h1>
        </div>
        <form onSubmit={submit} className="upload-form">
          <input
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button type="submit" disabled={loading || !file}>
            {loading ? 'Planning...' : 'Generate Plan'}
          </button>
        </form>
      </header>

      {error && (
        <div className="workspace">
          <section className="panel error-panel">
            <h2>Upload Failed</h2>
            <p>{error}</p>
          </section>
        </div>
      )}

      {result && (
        <div className="workspace">
          <Section title="Project Summary">
            <KeyValueTable
              rows={[
                ['Project', generated.project_name || result.filename],
                ['Planner mode', generated.planning_mode || 'azure_openai'],
                ['Review confidence', review.confidence || '-'],
              ]}
            />
          </Section>

          <Section title="Work Breakdown Structure">
            <ListBlock
              items={generated.wbs}
              render={(item) => `${item.code || ''} ${item.deliverable || item.name || JSON.stringify(item)}`}
            />
          </Section>

          <Section title="Project Schedule">
            <ScheduleTable tasks={generated.project_schedule} />
          </Section>

          <Section title="Sprint Plan">
            <ListBlock
              items={generated.sprint_plan}
              render={(item) =>
                `Sprint ${item.sprint}: ${item.start_date} to ${item.end_date} (${asArray(item.task_ids).join(', ')})`
              }
            />
          </Section>

          <Section title="Milestones">
            <ListBlock items={generated.milestone_plan} render={(item) => `${item.name}: ${item.date}`} />
          </Section>

          <Section title="Critical Path">
            <KeyValueTable
              rows={[
                ['Tasks', asArray(generated.critical_path?.task_ids)],
                ['Summary', generated.critical_path?.summary || '-'],
              ]}
            />
          </Section>

          <Section title="Resource Allocation">
            <ListBlock
              items={generated.resource_allocation}
              render={(item) =>
                `${item.role}: ${item.available_count || 0} available, tasks ${asArray(item.assigned_task_ids).join(', ') || '-'}`
              }
            />
          </Section>

          <Section title="Risks and Optimizations">
            <h3>Timeline Risks</h3>
            <ListBlock
              items={generated.timeline_risks}
              render={(item) => `${item.risk || item}: ${item.mitigation || ''}`}
            />
            <h3>Recommendations</h3>
            <ListBlock items={generated.schedule_optimizations} />
          </Section>

          <Section title="Effort Estimation">
            <KeyValueTable
              rows={[
                ['Duration days', generated.effort_estimation?.total_duration_days || '-'],
                ['Person days', generated.effort_estimation?.total_person_days || '-'],
                ['Basis', generated.effort_estimation?.basis || '-'],
              ]}
            />
          </Section>

          <Section title="Review">
            <h3>Issues</h3>
            <ListBlock items={review.issues} />
            <h3>Suggestions</h3>
            <ListBlock items={review.suggestions} />
          </Section>
        </div>
      )}
    </main>
  )
}
