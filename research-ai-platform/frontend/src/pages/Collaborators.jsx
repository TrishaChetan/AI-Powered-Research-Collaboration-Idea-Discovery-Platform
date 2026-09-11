import React, { useState } from 'react'
import api from '../api'

export default function Collaborators() {
  const [skillsInput, setSkillsInput] = useState('')
  const [results, setResults] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  const handleSearch = async () => {
    const required_skills = skillsInput.split(',').map((s) => s.trim()).filter(Boolean)
    if (required_skills.length === 0) return
    setBusy(true)
    setError('')
    try {
      const res = await api.matchCollaborators({ required_skills, top_n: 8 })
      setResults(res)
      setSearched(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Find Collaborators</h1>
      <p className="text-gray-500 mt-1">Enter the skills a project needs and we'll rank registered users by fit.</p>

      <div className="mt-6 bg-white border border-gray-200 rounded-xl p-5">
        <label className="text-sm font-medium">Required skills (comma separated)</label>
        <div className="mt-2 flex gap-2">
          <input
            value={skillsInput}
            onChange={(e) => setSkillsInput(e.target.value)}
            placeholder="Python, Computer Vision, React"
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <button
            onClick={handleSearch}
            disabled={busy}
            className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
          >
            {busy ? 'Searching…' : 'Find Matches'}
          </button>
        </div>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </div>

      <div className="grid md:grid-cols-2 gap-4 mt-6">
        {searched && results.length === 0 && (
          <p className="text-sm text-gray-500">No matches found for those skills.</p>
        )}
        {results.map((r) => (
          <div key={r.user_id} className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{r.name}</h3>
              <span className="text-sm font-bold text-brand-600">{r.match_score}% match</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">{r.explanation}</p>
            {r.matched_skills.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {r.matched_skills.map((s) => (
                  <span key={s} className="text-xs px-2 py-1 rounded bg-green-50 text-green-700">{s}</span>
                ))}
              </div>
            )}
            {r.missing_skills.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {r.missing_skills.map((s) => (
                  <span key={s} className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-500">missing: {s}</span>
                ))}
              </div>
            )}
            <button className="mt-4 text-sm px-3 py-1.5 rounded-md border border-brand-300 text-brand-600 hover:bg-brand-50">
              Connect
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
