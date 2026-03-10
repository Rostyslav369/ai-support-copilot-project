import { useEffect, useState } from 'react'
import {
  askQuestion,
  deleteDocument,
  getDocuments,
  getHealth,
  uploadDocument,
} from './api'

export default function App() {
  const [backendStatus, setBackendStatus] = useState('Checking...')
  const [documents, setDocuments] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [question, setQuestion] = useState('')
  const [uploadMessage, setUploadMessage] = useState('')
  const [answerData, setAnswerData] = useState(null)
  const [loadingUpload, setLoadingUpload] = useState(false)
  const [loadingAsk, setLoadingAsk] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadInitial()
  }, [])

  async function loadInitial() {
    try {
      const health = await getHealth()
      setBackendStatus(`Connected: ${health.app}`)
      await refreshDocuments()
    } catch (err) {
      setBackendStatus('Backend not connected')
      setError(err.message)
    }
  }

  async function refreshDocuments() {
    try {
      const data = await getDocuments()
      setDocuments(data.documents || [])
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleUpload(e) {
    e.preventDefault()
    setError('')
    setUploadMessage('')

    if (!selectedFile) {
      setError('Please choose a file first.')
      return
    }

    try {
      setLoadingUpload(true)
      const result = await uploadDocument(selectedFile)
      setUploadMessage(`${result.filename} uploaded. ${result.chunks_added} chunks indexed.`)
      setSelectedFile(null)
      document.getElementById('file-input').value = ''
      await refreshDocuments()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingUpload(false)
    }
  }

  async function handleAsk(e) {
    e.preventDefault()
    setError('')
    setAnswerData(null)

    if (!question.trim()) {
      setError('Please enter a support question.')
      return
    }

    try {
      setLoadingAsk(true)
      const result = await askQuestion(question)
      setAnswerData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingAsk(false)
    }
  }

  async function handleDelete(filename) {
    setError('')
    try {
      await deleteDocument(filename)
      await refreshDocuments()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">AI-powered support workflow</p>
          <h1>AI Support Copilot</h1>
          <p className="subtitle">
            Upload support docs, ask customer questions, and generate grounded answers with cited sources.
          </p>
        </div>
        <div className="status-card">
          <span className="status-label">Backend status</span>
          <strong>{backendStatus}</strong>
        </div>
      </header>

      {error && <div className="alert error">{error}</div>}
      {uploadMessage && <div className="alert success">{uploadMessage}</div>}

      <main className="grid">
        <section className="card">
          <h2>Upload Knowledge Base</h2>
          <p className="muted">Supported formats: .txt, .md, .pdf</p>

          <form onSubmit={handleUpload} className="stack">
            <input
              id="file-input"
              type="file"
              accept=".txt,.md,.pdf"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
            <button type="submit" disabled={loadingUpload}>
              {loadingUpload ? 'Uploading...' : 'Upload Document'}
            </button>
          </form>

          <div className="doc-list">
            <h3>Indexed Documents</h3>

            {documents.length === 0 ? (
              <p className="muted">No uploaded documents yet. Sample policy documents load automatically on backend startup.</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.filename} className="doc-item">
                  <div>
                    <strong>{doc.filename}</strong>
                    <p>{doc.chunks} chunk(s)</p>
                  </div>
                  <button className="danger" onClick={() => handleDelete(doc.filename)}>
                    Remove
                  </button>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="card">
          <h2>Ask a Customer Support Question</h2>

          <form onSubmit={handleAsk} className="stack">
            <textarea
              rows="6"
              placeholder="Example: Can I get a refund if my item arrived damaged?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button type="submit" disabled={loadingAsk}>
              {loadingAsk ? 'Generating...' : 'Generate Answer'}
            </button>
          </form>

          {answerData && (
            <div className="answer-box">
              <div className="answer-top">
                <div>
                  <h3>AI Answer</h3>
                  <p className="confidence">
                    Confidence: <strong>{answerData.confidence}</strong>
                  </p>
                </div>

                <span className={answerData.needs_human_review ? 'badge review' : 'badge ok'}>
                  {answerData.needs_human_review ? 'Needs Human Review' : 'Ready to Use'}
                </span>
              </div>

              <p className="answer-text">{answerData.answer}</p>

              <h4>Sources</h4>
              <div className="sources">
                {answerData.sources.map((source, index) => (
                  <div key={`${source.filename}-${index}`} className="source-card">
                    <strong>{source.filename}</strong>
                    <p>Chunk: {source.chunk_index}</p>
                    <p>Similarity: {source.similarity}</p>
                    <p>{source.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}