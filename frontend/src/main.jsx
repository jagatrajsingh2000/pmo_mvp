import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import WorkflowPage from './workflow/WorkflowPage'
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

  return (
    <>
      <div hidden={isWorkflow}>
        <App />
      </div>
      <div hidden={!isWorkflow}>
        <WorkflowPage />
      </div>
    </>
  )
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router />
  </React.StrictMode>
)
