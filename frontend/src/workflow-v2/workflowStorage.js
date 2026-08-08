let workflowSnapshot = null

export function loadWorkflowSnapshot() {
  try {
    const snapshot = workflowSnapshot ? cloneSnapshot(workflowSnapshot) : null
    if (!snapshot || typeof snapshot !== 'object') return null
    const outputs = normalizeStoredOutputs(snapshot.outputs)
    const steps = normalizeRestoredSteps(snapshot.steps, outputs)
    return {
      steps,
      outputs,
      selectedAgentId: typeof snapshot.selectedAgentId === 'string' ? snapshot.selectedAgentId : 'brd',
      savedAt: snapshot.savedAt || '',
    }
  } catch {
    clearWorkflowSnapshot()
    return null
  }
}

export function saveWorkflowSnapshot({ steps, outputs, selectedAgentId }) {
  if (!hasPersistableRun(steps, outputs)) return
  workflowSnapshot = {
    version: 1,
    savedAt: new Date().toISOString(),
    selectedAgentId,
    steps: normalizeStoredSteps(steps),
    outputs: normalizeStoredOutputs(outputs),
  }
}

export function clearWorkflowSnapshot() {
  workflowSnapshot = null
}

export function hasPersistableRun(steps, outputs) {
  return Object.keys(outputs || {}).length > 0 || Object.values(steps || {}).some((step) => step?.status && step.status !== 'queued')
}

function normalizeStoredSteps(steps) {
  if (!steps || typeof steps !== 'object') return {}
  return Object.fromEntries(
    Object.entries(steps).map(([id, step]) => [
      id,
      {
        status: step?.status === 'running' ? 'queued' : step?.status || 'queued',
        detail: step?.status === 'running' ? '' : step?.detail || '',
      },
    ]),
  )
}

function normalizeRestoredSteps(steps, outputs) {
  const restoredSteps = normalizeStoredSteps(steps)
  Object.keys(outputs || {}).forEach((id) => {
    restoredSteps[id] = {
      ...restoredSteps[id],
      status: 'done',
      detail: 'Complete',
    }
  })
  return restoredSteps
}

function normalizeStoredOutputs(outputs) {
  if (!outputs || typeof outputs !== 'object') return {}
  return Object.fromEntries(
    Object.entries(outputs)
      .filter(([, output]) => output?.data !== undefined)
      .map(([id, output]) => [
        id,
        {
          status: output.status || 'Complete',
          elapsed: output.elapsed || '',
          data: output.data,
        },
      ]),
  )
}

function cloneSnapshot(snapshot) {
  return JSON.parse(JSON.stringify(snapshot))
}
