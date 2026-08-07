import React, { useMemo, useRef, useState } from 'react'
import { requestFile, requestFiles, requestJson, tokenFromLogin } from './api'
import { AgentCard, FlowBar, ResultModal } from './components'
import { AGENTS, DEFAULT_SOURCE, DEMO_LOGIN } from './constants'
import { createHandoffArtifacts, groupArtifactsByType, requestFileWithArtifacts, requestFilesWithArtifactGroups } from './handoffArtifacts'
import { StructuredResult } from './resultRenderer'
import { downloadCombinedReportHtml, printCombinedReportPdf } from './reportExport'
import { createDefaultSourceFile } from './utils'
import './workflow-v2.css'

const initialSteps = () => Object.fromEntries(AGENTS.map((agent) => [agent.id, { status: 'queued', detail: '' }]))

export default function WorkflowV2Page() {
  const combinedReportRef = useRef(null)
  const [sourceFile, setSourceFile] = useState(null)
  const [useDefault, setUseDefault] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [steps, setSteps] = useState(initialSteps)
  const [outputs, setOutputs] = useState({})
  const [selectedAgentId, setSelectedAgentId] = useState('brd')
  const [modalAgentId, setModalAgentId] = useState('')

  const sourceName = useMemo(() => sourceFile?.name || 'Default restaurant source brief', [sourceFile])
  const selectedAgent = AGENTS.find((agent) => agent.id === selectedAgentId)
  const modalAgent = AGENTS.find((agent) => agent.id === modalAgentId)
  const completedCount = AGENTS.filter((agent) => steps[agent.id]?.status === 'done').length
  const canDownloadCombined = completedCount === AGENTS.length && AGENTS.every((agent) => outputs[agent.id]?.data)

  function updateStep(id, patch) {
    setSteps((current) => ({ ...current, [id]: { ...current[id], ...patch } }))
  }

  function resetRun() {
    setSteps(initialSteps())
    setOutputs({})
    setError('')
    setModalAgentId('')
    setSelectedAgentId('brd')
  }

  function onFileChange(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setSourceFile(file)
    setUseDefault(false)
    resetRun()
  }

  function useDefaultSource() {
    setSourceFile(null)
    setUseDefault(true)
    resetRun()
  }

  function chooseAgent(agentId) {
    setSelectedAgentId(agentId)
    document.getElementById(`workflow-v2-card-${agentId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  function openAgent(agentId) {
    setSelectedAgentId(agentId)
    if (outputs[agentId]) setModalAgentId(agentId)
  }

  function downloadCombinedReport() {
    if (!canDownloadCombined) return
    downloadCombinedReportHtml(combinedReportRef.current?.innerHTML || '')
  }

  function downloadCombinedPdf() {
    if (!canDownloadCombined) return
    printCombinedReportPdf(combinedReportRef.current?.innerHTML || '')
  }

  async function runMeasured(id, inputFiles, task) {
    const startedAt = performance.now()
    updateStep(id, { status: 'running', detail: 'Calling hosted API' })
    try {
      const result = await task()
      const elapsed = `${Math.max(1, Math.round((performance.now() - startedAt) / 1000))}s`
      const resolvedInputFiles = result.inputFiles || inputFiles
      setOutputs((current) => ({
        ...current,
        [id]: {
          status: 'Complete',
          elapsed,
          inputFiles: resolvedInputFiles,
          data: result.data,
        },
      }))
      updateStep(id, { status: 'done', detail: 'Complete' })
      return result
    } catch (err) {
      updateStep(id, { status: 'failed', detail: err.message || 'Failed' })
      throw err
    }
  }

  async function runWorkflow(event) {
    event.preventDefault()
    setRunning(true)
    resetRun()

    try {
      const tokenResult = await requestJson('/v1/auth/login', DEMO_LOGIN)
      const token = tokenFromLogin(tokenResult.data)
      if (!token) throw new Error('Login did not return a token.')

      const inputFile = sourceFile || createDefaultSourceFile(DEFAULT_SOURCE)

      const brd = await runMeasured('brd', [inputFile], async () => {
        const preview = await requestFile('/v1/brd/preview', 'file', inputFile, token)
        const artifacts = createHandoffArtifacts('BRD Agent', 'workflow-v2-brd', preview.data)
        return { data: preview.data, artifacts }
      })

      const stories = await runMeasured('stories', brd.artifacts.map((artifact) => artifact.file), async () => {
        const { response, artifact } = await requestFileWithArtifacts('/v1/userstory/generate-file', brd.artifacts, requestFile, token)
        const artifacts = createHandoffArtifacts('User Story Agent', 'workflow-v2-user-stories', response.data)
        return { data: response.data, artifacts, inputFiles: [artifact.file] }
      })

      const planner = await runMeasured('planner', brd.artifacts.map((artifact) => artifact.file), async () => {
        const { response, artifact } = await requestFileWithArtifacts('/planer/upload', brd.artifacts, requestFile, token)
        const artifacts = createHandoffArtifacts('Planner Agent', 'workflow-v2-planner', response.data)
        return { data: response.data, artifacts, inputFiles: [artifact.file] }
      })

      const budget = await runMeasured('budget', planner.artifacts.map((artifact) => artifact.file), async () => {
        const { response, artifact } = await requestFileWithArtifacts('/v1/budget/generate-from-file', planner.artifacts, requestFile, token)
        const artifacts = createHandoffArtifacts('Budget Agent', 'workflow-v2-budget', response.data)
        return { data: response.data, artifacts, inputFiles: [artifact.file] }
      })

      const executiveGroups = groupArtifactsByType([brd.artifacts, stories.artifacts, planner.artifacts, budget.artifacts])
      await runMeasured('executive', executiveGroups.flatMap((group) => group.files), async () => {
        const { response, group } = await requestFilesWithArtifactGroups('/v1/executive-report/generate', executiveGroups, requestFiles, token)
        return { data: response.data, inputFiles: group.files }
      })

      setSelectedAgentId('brd')
    } catch (err) {
      setError(err.message || 'Workflow failed')
    } finally {
      setRunning(false)
    }
  }

  return (
    <main className="workflow-v2-page">
      <ResultModal agent={modalAgent} output={modalAgentId ? outputs[modalAgentId] : null} onClose={() => setModalAgentId('')} />
      <div className="v2-combined-report-source" aria-hidden="true" ref={combinedReportRef}>
        {AGENTS.map((agent) => (
          outputs[agent.id]?.data ? (
            <section className="v2-combined-agent-report" key={agent.id}>
              <div className="report-kicker">Agent Report</div>
              <h1>{agent.title}</h1>
              <StructuredResult data={outputs[agent.id].data} agentId={agent.id} />
            </section>
          ) : null
        ))}
      </div>

      {error && <div className="v2-error">{error}</div>}

      <section className="v2-intro-note">
        <p>
          Orchestrates the entire project lifecycle from initial business requirements through planning, budgeting, and executive reporting. By connecting all PMO Helper agents into a single workflow, it helps teams move from idea to delivery intelligence with AI-powered outputs at every stage.
        </p>
      </section>

      <section className="v2-document-card">
        <div className="v2-document-heading">
          <div>
            <h2>Meetings / Documents</h2>
            <p>Upload business documents or meeting records to generate requirements, backlog, timeline, budget, and executive reporting in one workflow.</p>
          </div>
          <div className="v2-progress-chip">
            <span>Progress</span>
            <strong>{completedCount}/{AGENTS.length}</strong>
          </div>
        </div>

        <form className="v2-run-panel" onSubmit={runWorkflow}>
          <label className="v2-upload">
            <strong>{useDefault ? 'Default source selected' : sourceName}</strong>
            <span>Click to choose a different PDF or Word file</span>
            <input
              type="file"
              accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={onFileChange}
            />
          </label>
          <FlowBar agents={AGENTS} steps={steps} selectedId={selectedAgentId} onSelect={chooseAgent} />
          <div className="v2-action-row">
            <button type="submit" className="v2-primary" disabled={running}>
              {running ? 'Running Workflow' : 'Run Workflow'}
            </button>
            <button type="button" className="v2-secondary v2-combined-download" onClick={downloadCombinedReport} disabled={!canDownloadCombined || running}>
              Combined HTML
            </button>
            <button type="button" className="v2-secondary v2-combined-download" onClick={downloadCombinedPdf} disabled={!canDownloadCombined || running}>
              Combined PDF
            </button>
            <button type="button" className="v2-secondary" onClick={useDefaultSource} disabled={running}>
              Reset
            </button>
          </div>
          <div className={`v2-workflow-status ${completedCount === AGENTS.length ? 'complete' : ''}`}>
            <span />
            <strong>{completedCount === AGENTS.length ? 'Workflow complete - Executive Dashboard ready.' : `Ready to run ${selectedAgent?.title || 'workflow'}.`}</strong>
          </div>
        </form>
      </section>

      <section className="v2-agent-heading">
        <span>Agent Details</span>
        <strong>{selectedAgent?.title}</strong>
        <p>Choose an agent below to inspect its role. Completed agents open a result popup with the hosted API response displayed as report sections, tables, and coverage summaries.</p>
      </section>

      <section className="v2-card-grid">
        {AGENTS.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            state={steps[agent.id]}
            output={outputs[agent.id]}
            selected={selectedAgentId === agent.id}
            onOpen={() => openAgent(agent.id)}
          />
        ))}
      </section>
    </main>
  )
}
