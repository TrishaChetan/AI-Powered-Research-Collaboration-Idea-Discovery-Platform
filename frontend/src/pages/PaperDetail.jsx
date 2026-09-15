import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'

const TABS = ['Summary', 'Chat', 'Research Gaps', 'Generate Ideas', 'Related Papers']

export default function PaperDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [tab, setTab] = useState('Summary')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const [gaps, setGaps] = useState('')
  const [messages, setMessages] = useState([]) // {role, text, sources}
  const [question, setQuestion] = useState('')
  const [ideas, setIdeas] = useState([])
  const [related, setRelated] = useState(null)

  useEffect(() => {
    api.getPaper(id).then(setPaper).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  const handleSummarize = async () => {
    setBusy(true)
    setError('')
    try {
      const updated = await api.summarizePaper(id)
      setPaper(updated)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    const q = question
    setMessages((m) => [...m, { role: 'user', text: q }])
    setQuestion('')
    setBusy(true)
    setError('')
    try {
      const res = await api.askPaper(id, q)
      setMessages((m) => [...m, { role: 'ai', text: res.answer, sources: res.sources }])
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const handleGaps = async () => {
    setBusy(true)
    setError('')
    try {
      const res = await api.paperGaps(id)
      setGaps(res.gaps)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const handleGenerateIdeas = async () => {
    setBusy(true)
    setError('')
    try {
      const res = await api.generateIdeas({ paper_id: Number(id), num_ideas: 3 })
      setIdeas(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const handleRelated = async () => {
    setBusy(true)
    setError('')
    setRelated(null)
    try {
      const res = await api.relatedPapers(id)
      setRelated(res)
      if (!res || res.length === 0) {
        setError('arXiv is temporarily unavailable or returned no matching papers. Please try again shortly.')
      }
    } catch (e) {
      setError('Unable to search arXiv right now. Please try again shortly.')
      setRelated(null)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <p className="text-gray-400">Loading…</p>
  if (!paper) return <p className="text-red-600">Paper not found.</p>

  return (
    <div>
      <button onClick={() => navigate('/papers')} className="text-sm text-gray-500 hover:text-brand-600">← Back to papers</button>
      <h1 className="text-2xl font-bold mt-2">{paper.title}</h1>
      <p className="text-sm text-gray-500">{paper.num_chunks} chunks indexed</p>

      <div className="flex gap-2 mt-6 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === t ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {error && (
        <p className="text-sm text-red-600 mt-4 bg-red-50 border border-red-200 rounded-md p-3">{error}</p>
      )}

      <div className="mt-6">
        {tab === 'Summary' && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            {paper.summary ? (
              <pre className="whitespace-pre-wrap text-sm font-sans">{paper.summary}</pre>
            ) : (
              <p className="text-sm text-gray-500">No summary yet.</p>
            )}
            <button
              onClick={handleSummarize}
              disabled={busy}
              className="mt-4 px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? 'Summarizing…' : paper.summary ? 'Re-summarize' : 'Summarize Paper'}
            </button>
          </div>
        )}

        {tab === 'Chat' && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {messages.length === 0 && (
                <p className="text-sm text-gray-500">Ask anything about this paper — e.g. "What dataset was used?"</p>
              )}
              {messages.map((m, i) => (
                <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
                  <div
                    className={`inline-block px-4 py-2 rounded-lg text-sm max-w-lg text-left ${
                      m.role === 'user' ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {m.text}
                  </div>
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-1 text-xs text-gray-400">
                      Sources: {m.sources.map((s) => `p.${s.page}`).join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <form onSubmit={handleAsk} className="mt-4 flex gap-2">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about this paper…"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <button
                disabled={busy}
                className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
              >
                {busy ? '…' : 'Ask'}
              </button>
            </form>
          </div>
        )}

        {tab === 'Research Gaps' && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            {gaps ? (
              <pre className="whitespace-pre-wrap text-sm font-sans">{gaps}</pre>
            ) : (
              <p className="text-sm text-gray-500">No gaps identified yet.</p>
            )}
            <button
              onClick={handleGaps}
              disabled={busy}
              className="mt-4 px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? 'Analyzing…' : 'Find Research Gaps'}
            </button>
          </div>
        )}

        {tab === 'Generate Ideas' && (
          <div>
            <button
              onClick={handleGenerateIdeas}
              disabled={busy}
              className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? 'Generating…' : 'Generate Research Ideas'}
            </button>
            <div className="grid md:grid-cols-2 gap-4 mt-4">
              {ideas.map((idea) => (
                <div key={idea.id} className="bg-white border border-gray-200 rounded-xl p-5">
                  <h3 className="font-semibold">{idea.title}</h3>
                  <p className="text-sm text-gray-600 mt-2"><strong>Problem:</strong> {idea.problem}</p>
                  <p className="text-sm text-gray-600 mt-1"><strong>Approach:</strong> {idea.approach}</p>
                  <p className="text-xs text-gray-500 mt-2">Skills: {idea.required_skills_text}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs px-2 py-1 rounded bg-brand-50 text-brand-700">{idea.difficulty}</span>
                    <a
                      href={api.exportIdeaUrl(idea.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
                    >
                      Export PDF
                    </a>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-3">
              Saved ideas also appear on the <strong>Ideas</strong> page, where you can build follow-up ideas on top of them.
            </p>
          </div>
        )}

        {tab === 'Related Papers' && (
          <div>
            <button
              onClick={handleRelated}
              disabled={busy}
              className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? 'Searching arXiv…' : 'Find Related Papers'}
            </button>
            <div className="grid md:grid-cols-2 gap-4 mt-4">
              {related && related.length === 0 && (
                <p className="text-sm text-gray-500">No related papers found on arXiv for this topic.</p>
              )}
              {related && related.map((r, i) => (
                <a
                  key={i}
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-white border border-gray-200 rounded-xl p-5 hover:border-brand-400 transition"
                >
                  <h3 className="font-semibold text-sm">{r.title}</h3>
                  <p className="text-xs text-gray-500 mt-1">{r.authors.slice(0, 3).join(', ')}{r.authors.length > 3 ? ' et al.' : ''} · {r.published}</p>
                  <p className="text-sm text-gray-600 mt-2">{r.summary}</p>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

