import React, { useMemo, useState } from 'react'
import { requestFile, requestFiles, requestJson, tokenFromLogin } from './api'
import { AgentReportModal, AgentStep, AgentSummaryCard, WorkflowStepper } from './components'
import { AGENT_STEPS, DEFAULT_BRIEF, DEMO_LOGIN } from './constants'
import { buildHtmlReport } from './htmlReport'
import {
  asFileName,
  endpointInput,
  fileInput,
  filesInput,
  responseBrief,
  responseToFile,
} from './utils'
import './workflow.css'

export default function WorkflowPage() {
  const [sourceFile, setSourceFile] = useState(null)
  const [useDefault, setUseDefault] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [steps, setSteps] = useState(AGENT_STEPS.map((step) => ({ ...step, status: 'queued', detail: '' })))
  const [outputs, setOutputs] = useState({})
  const [selectedAgentId, setSelectedAgentId] = useState('')

  const sourceName = useMemo(() => {
    if (sourceFile) return sourceFile.name
    return 'default restaurant web app BRD'
  }, [sourceFile])

  function updateStep(id, patch) {
    setSteps((current) => current.map((step) => (step.id === id ? { ...step, ...patch } : step)))
  }

  function resetRun() {
    setSteps(AGENT_STEPS.map((step) => ({ ...step, status: 'queued', detail: '' })))
    setOutputs({})
    setError('')
    setSelectedAgentId('')
  }

  function acceptFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setSourceFile(file)
    setUseDefault(false)
    resetRun()
  }

  function selectDefaultFile() {
    setSourceFile(null)
    setUseDefault(true)
    resetRun()
  }

  function rememberOutput(id, value) {
    setOutputs((current) => ({ ...current, [id]: value }))
  }

  async function runMeasured(id, task) {
    const startedAt = performance.now()
    updateStep(id, { status: 'running', detail: '' })
    try {
      const result = await task()
      const elapsed = `${Math.max(1, Math.round((performance.now() - startedAt) / 1000))}s`
      updateStep(id, { status: 'done', detail: result.detail || 'Completed' })
      rememberOutput(id, { ...result.report, elapsed, status: 'Complete' })
      return result
    } catch (err) {
      updateStep(id, { status: 'failed', detail: err.message || 'Failed' })
      throw err
    }
  }

  async function buildBrdSource(token) {
    const fields = sourceFile
      ? {
          ...DEFAULT_BRIEF,
          source_document_name: sourceFile.name,
          source_document_type: sourceFile.type || 'document',
          source_document_size_bytes: sourceFile.size,
        }
      : DEFAULT_BRIEF
    const payload = { fields, filename: 'workflow-brd.docx' }
    const generated = await requestJson('/v1/brd/generate', payload, token)
    const brdFile = responseToFile(generated, 'workflow-brd.docx')
    if (!brdFile) throw new Error('BRD agent did not return a usable document.')
    return {
      detail: brdFile.name,
      brdFile,
      report: {
        input: sourceName,
        agentInput: endpointInput('/v1/brd/generate', payload),
        agentOutput: responseBrief(generated, brdFile),
        handoff: fileInput('/v1/userstory/generate-file and /planer/upload', brdFile),
        handoffFile: brdFile,
        file: brdFile,
        data: generated.kind === 'json' ? generated.data : responseBrief(generated, brdFile),
      },
    }
  }

  async function runWorkflow(event) {
    event.preventDefault()
    setRunning(true)
    resetRun()

    try {
      const loginResult = await requestJson('/v1/auth/login', DEMO_LOGIN)
      const token = tokenFromLogin(loginResult.data)
      if (!token) throw new Error('Authentication succeeded but no token was returned.')

      const brd = await runMeasured('brd', () => buildBrdSource(token))

      const stories = await runMeasured('userStories', async () => {
        const generated = await requestFile('/v1/userstory/generate-file', 'file', brd.brdFile, token)
        const download = await requestJson('/v1/userstory/download', generated.data, token)
        const file = responseToFile(download, 'workflow-user-stories.docx')
        if (!file) throw new Error('User Story agent did not return a usable document.')
        return {
          detail: file.name,
          file,
          report: {
            input: brd.brdFile.name,
            agentInput: fileInput('/v1/userstory/generate-file', brd.brdFile),
            agentOutput: responseBrief(generated, file),
            downloadedDocument: responseBrief(download, file),
            handoff: fileInput('/v1/executive-report/generate', file),
            handoffFile: file,
            file,
            data: generated.data,
          },
        }
      })

      const planner = await runMeasured('planner', async () => {
        const generated = await requestFile('/planer/upload', 'file', brd.brdFile, token)
        const download = await requestJson('/planer/download', generated.data, token)
        const file = responseToFile(download, 'workflow-planner.docx')
        if (!file) throw new Error('Planner agent did not return a usable document.')
        return {
          detail: file.name,
          file,
          report: {
            input: brd.brdFile.name,
            agentInput: fileInput('/planer/upload', brd.brdFile),
            agentOutput: responseBrief(generated, file),
            downloadedDocument: responseBrief(download, file),
            handoff: fileInput('/v1/budget/generate-from-file and /v1/executive-report/generate', file),
            handoffFile: file,
            file,
            data: generated.data,
          },
        }
      })

      const budget = await runMeasured('budget', async () => {
        const generated = await requestFile('/v1/budget/generate-from-file', 'file', planner.file, token)
        const download = await requestJson('/v1/budget/download', generated.data, token)
        const file = responseToFile(download, 'workflow-budget.docx')
        if (!file) throw new Error('Budget agent did not return a usable document.')
        return {
          detail: file.name,
          file,
          report: {
            input: planner.file.name,
            agentInput: fileInput('/v1/budget/generate-from-file', planner.file),
            agentOutput: responseBrief(generated, file),
            downloadedDocument: responseBrief(download, file),
            handoff: fileInput('/v1/executive-report/generate', file),
            handoffFile: file,
            file,
            data: generated.data,
          },
        }
      })

      await runMeasured('executive', async () => {
        const generated = await requestFiles(
          '/v1/executive-report/generate',
          'files',
          [brd.brdFile, stories.file, planner.file, budget.file],
          token,
        )
        return {
          detail: 'Executive report generated',
          report: {
            input: 'BRD, user-story, planner, and budget documents',
            agentInput: filesInput('/v1/executive-report/generate', [brd.brdFile, stories.file, planner.file, budget.file]),
            agentOutput: responseBrief(generated, null),
            handoff: null,
            fileName: 'executive-report-json',
            data: generated.data,
          },
        }
      })
    } catch (err) {
      setError(err.message || 'Workflow failed')
    } finally {
      setRunning(false)
    }
  }

  function downloadAgentReport(agentId) {
    const step = AGENT_STEPS.find((agentStep) => agentStep.id === agentId)
    const output = outputs[agentId]
    if (!step || !output) return
    const html = buildHtmlReport({ [agentId]: output }, sourceName)
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${asFileName(step.title, 'html')}`
    link.click()
    URL.revokeObjectURL(url)
  }

  function downloadAgentDocument(agentId, fileType = 'output') {
    const step = AGENT_STEPS.find((agentStep) => agentStep.id === agentId)
    const output = outputs[agentId]
    const file = fileType === 'handoff' ? output?.handoffFile : output?.file
    if (!step || !file) return
    const url = URL.createObjectURL(file)
    const link = document.createElement('a')
    link.href = url
    link.download = file.name || asFileName(`${step.title}-${fileType}`, 'docx')
    link.click()
    URL.revokeObjectURL(url)
  }

  function navigateToPlanner(event) {
    event.preventDefault()
    window.history.pushState({}, '', '/')
    window.dispatchEvent(new Event('pmo:navigate'))
  }

  const completeCount = steps.filter((step) => step.status === 'done').length
  const hasReport = Object.keys(outputs).length > 0
  const selectedStep = AGENT_STEPS.find((step) => step.id === selectedAgentId)
  const selectedOutput = selectedAgentId ? outputs[selectedAgentId] : null

  return (
    <main className="workflow-page">
      <AgentReportModal
        step={selectedStep}
        output={selectedOutput}
        onClose={() => setSelectedAgentId('')}
        onDownload={downloadAgentReport}
        onDownloadDocument={downloadAgentDocument}
      />

      <header className="workflow-hero">
        <div>
          <p className="eyebrow">PMO Multi-Agent Workflow</p>
          <h1>BRD to Executive Report Sequence</h1>
          <p>
            Upload a Word or PDF source document, or run the default restaurant web app BRD. The page sends each agent output into the next agent and keeps a separate report for every stage.
          </p>
        </div>
        <a href="/" className="workflow-link" onClick={navigateToPlanner}>Planner Upload</a>
      </header>

      <section className="workflow-shell">
        <form className="workflow-control-panel" onSubmit={runWorkflow}>
          <div className="workflow-dropzone">
            <span>Source document</span>
            <strong>{useDefault ? 'Default sample selected' : sourceName}</strong>
            <p>Accepted upload formats: PDF, DOC, DOCX.</p>
            <input
              type="file"
              accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={acceptFile}
            />
          </div>
          <div className="workflow-control-row">
            <button type="button" className="ghost-button" onClick={selectDefaultFile} disabled={running}>
              Use Default File
            </button>
            <button type="submit" disabled={running}>
              {running ? 'Running Agents...' : 'Run Full Workflow'}
            </button>
          </div>
          <div className="workflow-progress">
            <span>{completeCount} of {AGENT_STEPS.length} agents complete</span>
            <div>
              <i style={{ width: `${(completeCount / AGENT_STEPS.length) * 100}%` }} />
            </div>
          </div>
          {error && <div className="workflow-error">{error}</div>}
        </form>

        <div className="workflow-steps-panel">
          <WorkflowStepper steps={steps} />
          {steps.map((step) => <AgentStep key={step.id} step={step} />)}
        </div>
      </section>

      <section className="workflow-report">
        <div className="workflow-report-heading">
          <div>
            <p className="eyebrow">Agent Outputs</p>
            <h2>Separate Report For Each Agent</h2>
          </div>
          <span>{hasReport ? sourceName : 'Run the workflow to generate the report'}</span>
        </div>

        {hasReport ? (
          <div className="agent-report-grid">
            {AGENT_STEPS.map((step) => (
              <AgentSummaryCard key={step.id} step={step} output={outputs[step.id]} onOpen={setSelectedAgentId} />
            ))}
          </div>
        ) : (
          <div className="empty-report">
            <h3>Ready for a full PMO pass</h3>
            <p>The report will appear here agent by agent once the sequence starts producing outputs.</p>
          </div>
        )}
      </section>
    </main>
  )
}
