import React, { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'

export default function Papers() {
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInput = useRef(null)

  const load = () => {
    setLoading(true)
    api.listPapers().then(setPapers).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const onFileSelected = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      await api.uploadPaper(file)
      load()
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Research Papers</h1>
      </div>

      <div
        onClick={() => fileInput.current?.click()}
        className="mt-6 border-2 border-dashed border-gray-300 rounded-xl p-10 text-center cursor-pointer hover:border-brand-400 bg-white"
      >
        <div className="text-3xl">📄</div>
        <p className="mt-2 font-medium">
          {uploading ? 'Processing PDF (extracting text, chunking, embedding)…' : 'Click to upload a research paper (PDF)'}
        </p>
        <p className="text-sm text-gray-500 mt-1">It'll be indexed automatically so you can chat with it right away.</p>
        <input ref={fileInput} type="file" accept="application/pdf" className="hidden" onChange={onFileSelected} />
      </div>

      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

      <div className="mt-8 grid md:grid-cols-2 gap-4">
        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : papers.length === 0 ? (
          <p className="text-sm text-gray-500">No papers uploaded yet.</p>
        ) : (
          papers.map((p) => (
            <Link
              key={p.id}
              to={`/papers/${p.id}`}
              className="bg-white border border-gray-200 rounded-xl p-5 hover:border-brand-400 transition"
            >
              <h3 className="font-semibold">{p.title}</h3>
              <p className="text-xs text-gray-500 mt-1">{p.num_chunks} chunks indexed</p>
              <div className="mt-3 flex gap-2 text-xs">
                <span className="px-2 py-1 rounded bg-brand-50 text-brand-700">Summarize</span>
                <span className="px-2 py-1 rounded bg-brand-50 text-brand-700">Ask Questions</span>
                <span className="px-2 py-1 rounded bg-brand-50 text-brand-700">Find Gaps</span>
                <span className="px-2 py-1 rounded bg-brand-50 text-brand-700">Generate Ideas</span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
