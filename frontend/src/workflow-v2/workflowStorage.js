const STORAGE_KEY = 'pmo.workflowV2.latestRun'

export function loadWorkflowSnapshot() {
  if (!canUseStorage()) return null
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const snapshot = JSON.parse(raw)
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
  if (!canUseStorage() || !hasPersistableRun(steps, outputs)) return
  const snapshot = {
    version: 1,
    savedAt: new Date().toISOString(),
    selectedAgentId,
    steps: normalizeStoredSteps(steps),
    outputs: normalizeStoredOutputs(outputs),
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot))
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
  }
}

export function clearWorkflowSnapshot() {
  if (!canUseStorage()) return
  window.localStorage.removeItem(STORAGE_KEY)
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

function canUseStorage() {
  try {
    return typeof window !== 'undefined' && Boolean(window.localStorage)
  } catch {
    return false
  }
}
