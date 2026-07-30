import React, { useState } from 'react'

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: fd,
      })
      const data = await res.json()
      setResult(data)
    } catch (err) {
      console.error(err)
      alert('Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>PMO Timeline Planner</h1>
      <form onSubmit={submit}>
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit" disabled={loading}>{loading ? 'Uploading...' : 'Upload'}</button>
      </form>

      {result && (
        <div className="result">
          <h2>Result</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
