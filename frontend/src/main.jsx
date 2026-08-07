import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import WorkflowPage from './workflow/WorkflowPage'
import WorkflowV2Page from './workflow-v2/WorkflowV2Page'
import './style.css'

function Router() {
  const [path, setPath] = useState(window.location.pathname)

  useEffect(() => {
    const syncPath = () => setPath(window.location.pathname)
    window.addEventListener('popstate', syncPath)
    window.addEventListener('pmo:navigate', syncPath)
    return () => {
      window.removeEventListener('popstate', syncPath)
      window.removeEventListener('pmo:navigate', syncPath)
    }
  }, [])

  const isWorkflow = path === '/workflow'
  const isWorkflowV2 = path === '/workflow-v2'
  const isMainApp = !isWorkflow && !isWorkflowV2

  return (
    <>
      <div hidden={!isMainApp}>
        <App />
      </div>
      <div hidden={!isWorkflow}>
        <WorkflowPage />
      </div>
      <div hidden={!isWorkflowV2}>
        <WorkflowV2Page />
      </div>
    </>
  )
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router />
  </React.StrictMode>
)
