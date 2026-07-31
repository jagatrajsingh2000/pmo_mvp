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

function derivedTaskStatus(task) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = toDate(task?.start_date)
  const explicit = task?.status || 'Not Started'

  if (explicit === 'Done' || explicit === 'At Risk') return explicit
  if (start && start <= today) return 'In Progress'
  return explicit
}

function taskLabel(taskMap, taskId) {
  const task = taskMap.get(taskId)
  if (!task) return taskId
  return `${taskId} - ${task.name || taskId}`
}

function exportPdf() {
  window.print()
}

function scoreTone(score) {
  if (score >= 80) return 'strong'
  if (score >= 60) return 'watch'
  return 'weak'
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
          {asArray(tasks).map((task) => {
            const status = derivedTaskStatus(task)
            return (
              <tr key={task.id || task.name}>
                <td>{task.id}</td>
                <td>{task.name}</td>
                <td>
                  <span className={`status ${statusClass(status)}`}>{status}</span>
                </td>
                <td>{task.owner_role || '-'}</td>
                <td>{task.start_date || '-'}</td>
                <td>{task.end_date || '-'}</td>
                <td>{asArray(task.dependencies).join(', ') || '-'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function SprintTable({ sprints, tasks }) {
  const taskMap = new Map(asArray(tasks).map((task) => [task.id, task]))
  const list = asArray(sprints)
  if (!list.length) return <p className="muted">No sprints generated.</p>
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Sprint</th>
            <th>Start</th>
            <th>End</th>
            <th>Tasks</th>
          </tr>
        </thead>
        <tbody>
          {list.map((item) => (
            <tr key={item.sprint || `${item.start_date}-${item.end_date}`}>
              <td><strong>Sprint {item.sprint || '-'}</strong></td>
              <td>{item.start_date || 'TBD'}</td>
              <td>{item.end_date || 'TBD'}</td>
              <td>
                <div className="task-chip-list">
                  {asArray(item.task_ids).map((taskId) => (
                    <span className="task-chip" key={taskId}>{taskLabel(taskMap, taskId)}</span>
                  ))}
                </div>
              </td>
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

function ChartShell({ title, children }) {
  return (
    <div className="chart-shell">
      <h3>{title}</h3>
      {children}
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
    <ChartShell title="Estimated Project Schedule">
      <div className="gantt">
        <div className="gantt-scale">
          <span>{minDate.toISOString().slice(0, 10)}</span>
          <span>{maxDate.toISOString().slice(0, 10)}</span>
        </div>
        {datedTasks.map((task, index) => {
          const offset = (daysBetween(minDate, task.start) / totalDays) * 100
          const width = Math.max(8, ((daysBetween(task.start, task.end) + 1) / totalDays) * 100)
          return (
            <div className="gantt-row" key={task.id}>
              <span className="gantt-label">{task.name || task.id}</span>
              <div className="gantt-track">
                <div
                  className={`gantt-bar phase-${index % 6} ${statusClass(derivedTaskStatus(task))}`}
                  style={{ left: `${offset}%`, width: `${width}%` }}
                >
                  {task.duration_days ? `${task.duration_days}d` : task.id}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </ChartShell>
  )
}

function MilestoneTimeline({ milestones }) {
  const list = asArray(milestones)
  if (!list.length) return <p className="muted">No milestones generated.</p>
  return (
    <ChartShell title="Milestone Plan Based on Gate Model">
      <div className="gate-grid">
        {list.map((milestone, index) => (
          <div className="gate-item" key={milestone.name || index}>
            <span className="gate-index">Gate {index}</span>
            <strong>{milestone.name || `Milestone ${index + 1}`}</strong>
            <small>{milestone.date || 'Date TBD'}</small>
          </div>
        ))}
      </div>
    </ChartShell>
  )
}

function CriticalPathFlow({ criticalPath, tasks }) {
  const ids = asArray(criticalPath?.task_ids)
  const taskMap = new Map(asArray(tasks).map((task) => [task.id, task]))
  const pathItems = ids.length ? ids.map((id) => taskMap.get(id) || { id, name: id }) : asArray(tasks).slice(0, 6)
  if (!pathItems.length) return <p className="muted">No critical path generated.</p>

  return (
    <ChartShell title="Critical Path Analysis">
      <div className="critical-flow">
        {pathItems.map((task, index) => (
          <React.Fragment key={task.id || index}>
            <div className="flow-node">
              <strong>{task.id}</strong>
              <span>{task.name || task.id}</span>
            </div>
            {index < pathItems.length - 1 && <span className="flow-arrow">→</span>}
          </React.Fragment>
        ))}
      </div>
      {criticalPath?.summary && <p className="chart-note">{criticalPath.summary}</p>}
    </ChartShell>
  )
}

function DependencyMap({ dependencies }) {
  const list = asArray(dependencies)
  if (!list.length) return <p className="muted">No dependencies generated.</p>
  const nodes = Array.from(new Set(list.flatMap((item) => [item.task_id, ...asArray(item.depends_on), ...asArray(item.blocks)]).filter(Boolean)))
  return (
    <>
      <ChartShell title="Dependency Map">
        <div className="node-map">
          {nodes.slice(0, 12).map((node, index) => (
            <div className={`map-node node-${index % 4}`} key={node}>
              {node}
            </div>
          ))}
        </div>
      </ChartShell>
      <div className="dependency-map">
        {list.map((item, index) => (
          <div className="dependency-card" key={item.task_id || index}>
            <span>{asArray(item.depends_on).join(', ') || 'Start'}</span>
            <strong>{item.task_id}</strong>
            <span>{asArray(item.blocks).join(', ') || 'Finish'}</span>
          </div>
        ))}
      </div>
    </>
  )
}

function EffortWorkstreamChart({ rows }) {
  const list = asArray(rows)
  if (!list.length) return <p className="muted">No effort by workstream generated.</p>
  const max = Math.max(...list.map((row) => Number(row.person_days || 0)), 1)
  return (
    <ChartShell title="Effort Estimation by Workstream">
      <div className="vertical-bars">
        {list.map((row, index) => {
          const value = Number(row.person_days || 0)
          const level = value / max > 0.66 ? 'High' : value / max > 0.33 ? 'Medium' : 'Low'
          return (
            <div className="vertical-bar-item" key={row.role || index}>
              <div className={`vertical-bar level-${level.toLowerCase()}`} style={{ height: `${Math.max(18, (value / max) * 100)}%` }}>
                <span>{level}</span>
              </div>
              <strong>{row.role}</strong>
              <small>{value}d</small>
            </div>
          )
        })}
      </div>
    </ChartShell>
  )
}

function RiskMatrix({ risks }) {
  const list = asArray(risks)
  if (!list.length) return <p className="muted">No timeline risks generated.</p>
  return (
    <>
      <ChartShell title="Timeline Risk Severity">
        <div className="severity-bars">
          {list.map((risk, index) => {
            const likelihood = Number(risk.likelihood || 3)
            const impact = Number(risk.impact || 3)
            const score = likelihood * impact
            const severity = score >= 16 ? 'High' : score >= 8 ? 'Medium' : 'Low'
            return (
              <div className="severity-row" key={risk.risk || index}>
                <span>{risk.risk || `Risk ${index + 1}`}</span>
                <div className="severity-track">
                  <div className={`severity-fill severity-${severity.toLowerCase()}`} style={{ width: `${Math.max(10, (score / 25) * 100)}%` }} />
                </div>
                <strong>{severity}</strong>
              </div>
            )
          })}
        </div>
      </ChartShell>
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
    </>
  )
}

function DependencySummary({ dependencies }) {
  const list = asArray(dependencies)
  const rows = [
    {
      type: 'Upstream',
      examples: list.filter((item) => asArray(item.depends_on).length).map((item) => `${asArray(item.depends_on).join(', ')} → ${item.task_id}`),
    },
    {
      type: 'Downstream',
      examples: list.filter((item) => asArray(item.blocks).length).map((item) => `${item.task_id} → ${asArray(item.blocks).join(', ')}`),
    },
    {
      type: 'Standalone',
      examples: list.filter((item) => !asArray(item.depends_on).length && !asArray(item.blocks).length).map((item) => item.task_id),
    },
  ]
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Dependency Type</th>
            <th>Count</th>
            <th>Examples</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.type}>
              <td>{row.type}</td>
              <td>{row.examples.length}</td>
              <td>{row.examples.slice(0, 4).join('; ') || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
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

function ScoreGauge({ label, score }) {
  const value = Math.max(0, Math.min(100, Number(score || 0)))
  return (
    <div className={`score-card ${scoreTone(value)}`}>
      <div className="score-ring" style={{ '--score': `${value * 3.6}deg` }}>
        <strong>{value}</strong>
      </div>
      <span>{label}</span>
    </div>
  )
}

function QualityScoresTab({ review }) {
  const scores = asArray(review?.quality_scores)
  const overall = Number(review?.overall_quality_score || 0)
  if (!scores.length) {
    return (
      <div className="workspace">
        <Section title="Quality Scores" wide>
          <p className="muted">Quality scores were not returned by the reviewer.</p>
        </Section>
      </div>
    )
  }

  return (
    <div className="workspace">
      <Section title="Quality Score Summary" subtitle="Independent audit scoring for the generated planning output." wide>
        <div className="quality-hero">
          <ScoreGauge label="Overall Quality" score={overall} />
          <div className="quality-grid">
            {scores.map((item) => (
              <ScoreGauge key={item.category} label={item.category} score={item.score} />
            ))}
          </div>
        </div>
      </Section>

      <Section title="Quality Audit Details" wide>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Score</th>
                <th>Rationale</th>
                <th>Evidence</th>
                <th>Improvement</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((item) => (
                <tr key={item.category}>
                  <td>{item.category}</td>
                  <td>
                    <span className={`score-pill ${scoreTone(Number(item.score || 0))}`}>{item.score}</span>
                  </td>
                  <td>{item.rationale || '-'}</td>
                  <td>{item.evidence || '-'}</td>
                  <td>{item.improvement || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  )
}

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('report')
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
      const res = await fetch(`${API_BASE}/planer/upload`, {
        method: 'POST',
        body: fd,
      })
      const contentType = res.headers.get('content-type') || ''
      const data = contentType.includes('application/json') ? await res.json() : { detail: await res.text() }
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setResult(data)
      setActiveTab('report')
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
          <div className="tabs no-print">
            <button className={activeTab === 'report' ? 'active' : ''} type="button" onClick={() => setActiveTab('report')}>
              PMO Report
            </button>
            <button className={activeTab === 'quality' ? 'active' : ''} type="button" onClick={() => setActiveTab('quality')}>
              Quality Scores
            </button>
          </div>

          {activeTab === 'quality' ? (
            <QualityScoresTab review={review} />
          ) : (
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
              <SprintTable sprints={generated.sprint_plan} tasks={generated.project_schedule} />
            </Section>

            <Section title="Milestone Plan">
              <MilestoneTimeline milestones={generated.milestone_plan} />
            </Section>

            <Section title="Critical Path Analysis">
              <CriticalPathFlow criticalPath={generated.critical_path} tasks={generated.project_schedule} />
            </Section>

            <Section title="Dependency Map">
              <DependencyMap dependencies={generated.dependency_map} />
              <DependencySummary dependencies={generated.dependency_map} />
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
              <EffortWorkstreamChart rows={effortByRole} />
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
          )}
        </div>
      )}
    </main>
  )
}
