const API_BASE = 'http://localhost:8000'

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) {
    throw new Error('Failed to connect to backend')
  }
  return res.json()
}

export async function getDocuments() {
  const res = await fetch(`${API_BASE}/documents`)
  if (!res.ok) {
    throw new Error('Failed to fetch documents')
  }
  return res.json()
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(data.detail || 'Upload failed')
  }

  return data
}

export async function askQuestion(question) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(data.detail || 'Question failed')
  }

  return data
}

export async function deleteDocument(filename) {
  const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(data.detail || 'Delete failed')
  }

  return data
}