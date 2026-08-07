import React from 'react'

export function PlannerVisuals({ data }) {
  const planner = plannerData(data)
  const tasks = asArray(planner.project_schedule)
  const milestones = asArray(planner.milestone_plan)
  const dependencies = asArray(planner.dependency_map)
  const risks = asArray(planner.timeline_risks)
  const effortRows = effortByRole(planner)
  const hasGantt = hasDatedTasks(tasks)
  const hasCriticalPath = hasCriticalPathVisual(planner.critical_path, tasks)
  const totalVisuals = [hasGantt, milestones.length, hasCriticalPath, dependencies.length, effortRows.length, risks.length].filter(Boolean).length
  const hasVisuals = tasks.length || milestones.length || dependencies.length || risks.length || effortRows.length

  if (!hasVisuals) return null

  return (
    <section className="v2-planner-visuals">
      <header>
        <div>
          <h3>Planner Visual Dashboard</h3>
          <p>Timeline, gate plan, critical path, dependencies, effort, and risk views generated from the planner output.</p>
        </div>
        <span>{totalVisuals} visuals</span>
      </header>

      <div className="v2-planner-grid">
        <GanttChart tasks={tasks} />
        <MilestoneTimeline milestones={milestones} wide={!hasGantt} />
        <CriticalPathFlow criticalPath={planner.critical_path} tasks={tasks} />
        <DependencyMap dependencies={dependencies} />
        <EffortChart rows={effortRows} />
        <RiskChart risks={risks} />
      </div>
    </section>
  )
}

export function plannerData(data) {
  if (!data || typeof data !== 'object') return {}
  return (
    data.generated ||
    data.result?.generated ||
    data.output?.generated ||
    data.data?.generated ||
    data.report?.generated ||
    data
  )
}

function GanttChart({ tasks }) {
  const datedTasks = asArray(tasks)
    .map((task) => ({ ...task, start: toDate(task.start_date), end: toDate(task.end_date) }))
    .filter((task) => task.start && task.end)

  if (!datedTasks.length) return null

  const minDate = new Date(Math.min(...datedTasks.map((task) => task.start.getTime())))
  const maxDate = new Date(Math.max(...datedTasks.map((task) => task.end.getTime())))
  const totalDays = Math.max(daysBetween(minDate, maxDate) + 1, 1)

  return (
    <VisualPanel title="Estimated Project Schedule" wide>
      <div className="v2-gantt">
        <div className="v2-gantt-scale">
          <span>{dateText(minDate)}</span>
          <span>{dateText(maxDate)}</span>
        </div>
        {datedTasks.slice(0, 12).map((task, index) => {
          const offset = (daysBetween(minDate, task.start) / totalDays) * 100
          const width = Math.max(8, ((daysBetween(task.start, task.end) + 1) / totalDays) * 100)
          return (
            <div className="v2-gantt-row" key={task.id || task.name || index}>
              <span className="v2-gantt-label">{task.name || task.id || `Task ${index + 1}`}</span>
              <div className="v2-gantt-track">
                <div
                  className={`v2-gantt-bar phase-${index % 6} ${statusClass(derivedTaskStatus(task))}`}
                  style={{ left: `${offset}%`, width: `${width}%` }}
                >
                  {task.duration_days ? `${task.duration_days}d` : task.id || index + 1}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </VisualPanel>
  )
}

function MilestoneTimeline({ milestones, wide = false }) {
  const list = asArray(milestones)
  if (!list.length) return null
  return (
    <VisualPanel title="Milestone Gate Plan" wide={wide}>
      <div className="v2-gate-grid">
        {list.slice(0, 8).map((milestone, index) => (
          <div className="v2-gate-item" key={milestone.name || milestone.milestone || index}>
            <span>Gate {index}</span>
            <strong>{milestone.name || milestone.milestone || `Milestone ${index + 1}`}</strong>
            <small>{milestone.date || milestone.target_date || 'Date TBD'}</small>
          </div>
        ))}
      </div>
    </VisualPanel>
  )
}

function CriticalPathFlow({ criticalPath, tasks }) {
  const taskMap = new Map(asArray(tasks).map((task) => [task.id, task]))
  const ids = asArray(criticalPath?.task_ids || criticalPath?.tasks || criticalPath?.path)
  const pathItems = ids.length ? ids.map((id) => taskMap.get(id) || { id, name: id }) : asArray(tasks).slice(0, 6)
  if (!pathItems.length) return null

  return (
    <VisualPanel title="Critical Path Analysis" wide>
      <div className="v2-critical-flow">
        {pathItems.slice(0, 8).map((task, index) => (
          <React.Fragment key={task.id || task.name || index}>
            <div className="v2-flow-card">
              <strong>{task.id || index + 1}</strong>
              <span>{task.name || task.title || task.id || `Step ${index + 1}`}</span>
            </div>
            {index < Math.min(pathItems.length, 8) - 1 && <span className="v2-flow-arrow">→</span>}
          </React.Fragment>
        ))}
      </div>
      {criticalPath?.summary && <p className="v2-visual-note">{criticalPath.summary}</p>}
    </VisualPanel>
  )
}

function DependencyMap({ dependencies }) {
  const list = asArray(dependencies)
  if (!list.length) return null
  const nodes = Array.from(new Set(list.flatMap((item) => [item.task_id, item.id, ...asArray(item.depends_on), ...asArray(item.blocks)]).filter(Boolean)))

  return (
    <VisualPanel title="Dependency Map">
      <div className="v2-node-map">
        {nodes.slice(0, 10).map((node, index) => (
          <div className={`v2-map-node node-${index % 4}`} key={node}>
            {node}
          </div>
        ))}
      </div>
    </VisualPanel>
  )
}

function EffortChart({ rows }) {
  const list = asArray(rows)
  if (!list.length) return null
  const max = Math.max(...list.map((row) => Number(row.person_days || row.effort || 0)), 1)

  return (
    <VisualPanel title="Effort By Workstream">
      <div className="v2-effort-bars">
        {list.slice(0, 8).map((row, index) => {
          const value = Number(row.person_days || row.effort || 0)
          const level = value / max > 0.66 ? 'High' : value / max > 0.33 ? 'Medium' : 'Low'
          return (
            <div className="v2-effort-item" key={row.role || row.workstream || index}>
              <div className={`v2-effort-bar level-${level.toLowerCase()}`} style={{ height: `${Math.max(18, (value / max) * 100)}%` }}>
                <span>{level}</span>
              </div>
              <strong>{row.role || row.workstream || `Workstream ${index + 1}`}</strong>
              <small>{value}d</small>
            </div>
          )
        })}
      </div>
    </VisualPanel>
  )
}

function RiskChart({ risks }) {
  const list = asArray(risks)
  if (!list.length) return null

  return (
    <VisualPanel title="Timeline Risk Severity" wide>
      <div className="v2-risk-bars">
        {list.slice(0, 8).map((risk, index) => {
          const likelihood = Number(risk.likelihood || risk.likelihood_score || 3)
          const impact = Number(risk.impact || risk.impact_score || 3)
          const score = likelihood * impact
          const severity = score >= 16 ? 'High' : score >= 8 ? 'Medium' : 'Low'
          return (
            <div className="v2-risk-row" key={risk.risk || risk.name || index}>
              <span>{risk.risk || risk.name || `Risk ${index + 1}`}</span>
              <div>
                <em className={`severity-${severity.toLowerCase()}`} style={{ width: `${Math.max(10, (score / 25) * 100)}%` }} />
              </div>
              <strong>{severity}</strong>
            </div>
          )
        })}
      </div>
    </VisualPanel>
  )
}

function VisualPanel({ title, children, wide = false }) {
  if (!children) return null
  return (
    <article className={`v2-visual-panel ${wide ? 'wide' : ''}`}>
      <h4>{title}</h4>
      {children}
    </article>
  )
}

function effortByRole(planner) {
  const explicit = asArray(planner.effort_estimation?.by_role || planner.effort_estimation?.workstreams)
  if (explicit.length) return explicit
  const totals = {}
  asArray(planner.project_schedule).forEach((task) => {
    const role = task.owner_role || task.role || 'Unassigned'
    totals[role] = (totals[role] || 0) + Number(task.duration_days || 0)
  })
  return Object.entries(totals).map(([role, person_days]) => ({ role, person_days }))
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

function dateText(date) {
  return date.toISOString().slice(0, 10)
}

function statusClass(status = '') {
  return status.toLowerCase().replace(/\s+/g, '-') || 'not-started'
}

function hasDatedTasks(tasks) {
  return asArray(tasks).some((task) => toDate(task.start_date) && toDate(task.end_date))
}

function hasCriticalPathVisual(criticalPath, tasks) {
  return Boolean(asArray(criticalPath?.task_ids || criticalPath?.tasks || criticalPath?.path).length || asArray(tasks).length)
}
