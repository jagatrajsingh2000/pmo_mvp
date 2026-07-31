import React, { useMemo, useState } from 'react'

const API_BASE = `http://${window.location.hostname || 'localhost'}:8000`

function asArray(value) {
  if (!value) return []
  return Array.isArray(value) ? value : [value]
}

function toDate(value) {
  const parsed = value ? new Date(value) : null
  return parsed && !Number.isNaN(parsed.getTime()) ? parsed : null
}

function daysBetween(start, end) {
  const ms = 24 * 60 * 60 * 1000
  return Math.max(0, Math.round((end - start) / ms))
}

function statusClass(status = '') {
  return status.toLowerCase().replace(/\s+/g, '-') || 'not-started'
}

function exportPdf() {
  window.print()
}

function Section({ title, subtitle, children, wide = false }) {
  return (
    <section className={`panel ${wide ? 'wide' : ''}`}>
      <div className="section-heading">
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
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
            <th>Status</th>
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
              <td>
                <span className={`status ${statusClass(task.status)}`}>{task.status || 'Not Started'}</span>
              </td>
              <td>{task.owner_role || '-'}</td>
              <td>{task.start_date || '-'}</td>
              <td>{task.end_date || '-'}</td>
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
        <li key={item.id || item.code || item.name || index}>{render ? render(item, index) : String(item)}</li>
      ))}
    </ul>
  )
}

function BarChart({ rows, valueKey, labelKey, suffix = '' }) {
  const normalized = asArray(rows).map((row) => ({
    label: row[labelKey],
    value: Number(row[valueKey] || 0),
  }))
  const max = Math.max(...normalized.map((row) => row.value), 1)
  return (
    <div className="bar-chart">
      {normalized.map((row) => (
        <div className="bar-row" key={row.label}>
          <span>{row.label || 'Unassigned'}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.max(6, (row.value / max) * 100)}%` }} />
          </div>
          <strong>
            {row.value}
            {suffix}
          </strong>
        </div>
      ))}
    </div>
  )
}

function GanttChart({ tasks }) {
  const datedTasks = asArray(tasks)
    .map((task) => ({ ...task, start: toDate(task.start_date), end: toDate(task.end_date) }))
    .filter((task) => task.start && task.end)

  if (!datedTasks.length) return <p className="muted">Schedule dates are needed for the Gantt chart.</p>

  const minDate = new Date(Math.min(...datedTasks.map((task) => task.start.getTime())))
  const maxDate = new Date(Math.max(...datedTasks.map((task) => task.end.getTime())))
  const totalDays = Math.max(daysBetween(minDate, maxDate) + 1, 1)

  return (
    <div className="gantt">
      <div className="gantt-scale">
        <span>{minDate.toISOString().slice(0, 10)}</span>
        <span>{maxDate.toISOString().slice(0, 10)}</span>
      </div>
      {datedTasks.map((task) => {
        const offset = (daysBetween(minDate, task.start) / totalDays) * 100
        const width = Math.max(8, ((daysBetween(task.start, task.end) + 1) / totalDays) * 100)
        return (
          <div className="gantt-row" key={task.id}>
            <span className="gantt-label">{task.id}</span>
            <div className="gantt-track">
              <div className={`gantt-bar ${statusClass(task.status)}`} style={{ left: `${offset}%`, width: `${width}%` }}>
                {task.name}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function MilestoneTimeline({ milestones }) {
  const list = asArray(milestones)
  if (!list.length) return <p className="muted">No milestones generated.</p>
  return (
    <div className="milestone-line">
      {list.map((milestone, index) => (
        <div className="milestone-item" key={milestone.name || index}>
          <span className="milestone-dot" />
          <strong>{milestone.name}</strong>
          <small>{milestone.date || 'Date TBD'}</small>
        </div>
      ))}
    </div>
  )
}

function DependencyMap({ dependencies }) {
  const list = asArray(dependencies)
  if (!list.length) return <p className="muted">No dependencies generated.</p>
  return (
    <div className="dependency-map">
      {list.map((item, index) => (
        <div className="dependency-card" key={item.task_id || index}>
          <span>{asArray(item.depends_on).join(', ') || 'Start'}</span>
          <strong>{item.task_id}</strong>
          <span>{asArray(item.blocks).join(', ') || 'Finish'}</span>
        </div>
      ))}
    </div>
  )
}

function RiskMatrix({ risks }) {
  const list = asArray(risks)
  if (!list.length) return <p className="muted">No timeline risks generated.</p>
  return (
    <div className="risk-list">
      {list.map((risk, index) => {
        const likelihood = Number(risk.likelihood || 3)
        const impact = Number(risk.impact || 3)
        const score = likelihood * impact
        return (
          <div className="risk-card" key={risk.risk || index}>
            <div className="risk-score">
              <strong>{score}</strong>
              <span>L{likelihood} x I{impact}</span>
            </div>
            <div>
              <h3>{risk.risk || `Risk ${index + 1}`}</h3>
              <p>{risk.mitigation || 'Mitigation to be confirmed.'}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ReportActions({ filename }) {
  return (
    <div className="report-actions">
      <div>
        <p className="eyebrow">Generated Report</p>
        <h2>{filename}</h2>
      </div>
      <button type="button" onClick={exportPdf}>
        Export PDF
      </button>
    </div>
  )
}

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const generated = result?.generated || {}
  const review = result?.review || {}

  const effortByRole = useMemo(() => {
    const explicit = asArray(generated.effort_estimation?.by_role)
    if (explicit.length) return explicit
    const totals = {}
    asArray(generated.project_schedule).forEach((task) => {
      const role = task.owner_role || 'unassigned'
      totals[role] = (totals[role] || 0) + Number(task.duration_days || 0)
    })
    return Object.entries(totals).map(([role, person_days]) => ({ role, person_days }))
  }, [generated.effort_estimation, generated.project_schedule])

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
      const contentType = res.headers.get('content-type') || ''
      const data = contentType.includes('application/json') ? await res.json() : { detail: await res.text() }
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
      <header className="topbar no-print">
        <div>
          <p className="eyebrow">Project Timeline Planner Agent</p>
          <h1>Generate WBS, schedule, sprint plan, risks, and visual PMO report</h1>
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
        <div className="report">
          <ReportActions filename={generated.project_name || result.filename} />
          <div className="workspace">
            <Section title="Project Summary">
              <KeyValueTable
                rows={[
                  ['Project', generated.project_name || result.filename],
                  ['Source file', result.filename],
                  ['Planner mode', generated.planning_mode || 'azure_openai'],
                  ['Review confidence', review.confidence || '-'],
                ]}
              />
            </Section>

            <Section title="Work Breakdown Status Structure">
              <ListBlock
                items={generated.wbs}
                render={(item) => (
                  <>
                    <span className={`status ${statusClass(item.status)}`}>{item.status || 'Not Started'}</span>
                    <strong>{item.code || item.task_id}</strong> {item.deliverable || item.name || JSON.stringify(item)}
                  </>
                )}
              />
            </Section>

            <Section title="Project Schedule" subtitle="Gantt-style view generated from task dates." wide>
              <GanttChart tasks={generated.project_schedule} />
              <ScheduleTable tasks={generated.project_schedule} />
            </Section>

            <Section title="Sprint Plan">
              <ListBlock
                items={generated.sprint_plan}
                render={(item) =>
                  `Sprint ${item.sprint}: ${item.start_date || 'TBD'} to ${item.end_date || 'TBD'} (${asArray(item.task_ids).join(', ')})`
                }
              />
            </Section>

            <Section title="Milestone Plan">
              <MilestoneTimeline milestones={generated.milestone_plan} />
            </Section>

            <Section title="Critical Path Analysis">
              <KeyValueTable
                rows={[
                  ['Critical tasks', asArray(generated.critical_path?.task_ids)],
                  ['Analysis', generated.critical_path?.summary || '-'],
                ]}
              />
            </Section>

            <Section title="Dependency Map">
              <DependencyMap dependencies={generated.dependency_map} />
            </Section>

            <Section title="Resource Allocation Plan">
              <BarChart rows={generated.resource_allocation} labelKey="role" valueKey="available_count" suffix=" ppl" />
              <ListBlock
                items={generated.resource_allocation}
                render={(item) =>
                  `${item.role}: ${item.available_count || 0} available, assigned tasks ${asArray(item.assigned_task_ids).join(', ') || '-'}`
                }
              />
            </Section>

            <Section title="Timeline Risk">
              <RiskMatrix risks={generated.timeline_risks} />
            </Section>

            <Section title="Effort Estimation">
              <BarChart rows={effortByRole} labelKey="role" valueKey="person_days" suffix="d" />
              <KeyValueTable
                rows={[
                  ['Duration days', generated.effort_estimation?.total_duration_days || '-'],
                  ['Person days', generated.effort_estimation?.total_person_days || '-'],
                  ['Basis', generated.effort_estimation?.basis || '-'],
                ]}
              />
            </Section>

            <Section title="Schedule Optimization Recommendations">
              <ListBlock items={generated.schedule_optimizations} />
            </Section>

            <Section title="Review">
              <h3>Issues</h3>
              <ListBlock items={review.issues} />
              <h3>Suggestions</h3>
              <ListBlock items={review.suggestions} />
            </Section>
          </div>
        </div>
      )}
    </main>
  )
}
