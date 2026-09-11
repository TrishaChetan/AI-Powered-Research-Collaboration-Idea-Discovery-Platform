import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Ideas() {
  const [ideas, setIdeas] = useState([])
  const [loading, setLoading] = useState(true)
  const [interests, setInterests] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = () => {
    setLoading(true)
    api.listIdeas().then(setIdeas).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleGenerate = async () => {
    setBusy(true)
    setError('')
    try {
      await api.generateIdeas({
        interests: interests.split(',').map((s) => s.trim()).filter(Boolean),
        num_ideas: 3,
      })
      load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Research Ideas</h1>
      <p className="text-gray-500 mt-1">Generated from your uploaded papers, or from scratch based on your interests.</p>

      <div className="mt-6 bg-white border border-gray-200 rounded-xl p-5">
        <label className="text-sm font-medium">Generate new ideas based on interests</label>
        <div className="mt-2 flex gap-2">
          <input
            value={interests}
            onChange={(e) => setInterests(e.target.value)}
            placeholder="e.g. Healthcare AI, Computer Vision"
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <button
            onClick={handleGenerate}
            disabled={busy}
            className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
          >
            {busy ? 'Generating…' : 'Generate'}
          </button>
        </div>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </div>

      <div className="grid md:grid-cols-2 gap-4 mt-6">
        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : ideas.length === 0 ? (
          <p className="text-sm text-gray-500">No ideas saved yet.</p>
        ) : (
          ideas.map((idea) => (
            <div key={idea.id} className="bg-white border border-gray-200 rounded-xl p-5">
              <h3 className="font-semibold">{idea.title}</h3>
              <p className="text-sm text-gray-600 mt-2"><strong>Problem:</strong> {idea.problem}</p>
              <p className="text-sm text-gray-600 mt-1"><strong>Approach:</strong> {idea.approach}</p>
              <p className="text-xs text-gray-500 mt-2">Skills: {idea.required_skills_text}</p>
              <span className="inline-block mt-2 text-xs px-2 py-1 rounded bg-brand-50 text-brand-700">{idea.difficulty}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
