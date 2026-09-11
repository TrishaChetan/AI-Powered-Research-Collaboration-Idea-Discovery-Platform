import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ title: '', description: '', required_skills: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = () => {
    setLoading(true)
    api.listProjects().then(setProjects).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api.createProject({
        title: form.title,
        description: form.description,
        required_skills: form.required_skills.split(',').map((s) => s.trim()).filter(Boolean),
        member_ids: [],
      })
      setForm({ title: '', description: '', required_skills: '' })
      load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Project Workspace</h1>
      <p className="text-gray-500 mt-1">Turn an idea and a matched team into a tracked project.</p>

      <form onSubmit={handleCreate} className="mt-6 bg-white border border-gray-200 rounded-xl p-5 space-y-3">
        <div>
          <label className="text-sm font-medium">Project title</label>
          <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-medium">Description</label>
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2} className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-medium">Required skills (comma separated)</label>
          <input value={form.required_skills} onChange={(e) => setForm({ ...form, required_skills: e.target.value })}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={busy} className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60">
          {busy ? 'Creating…' : 'Create Project'}
        </button>
      </form>

      <div className="grid md:grid-cols-2 gap-4 mt-6">
        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : projects.length === 0 ? (
          <p className="text-sm text-gray-500">No projects yet.</p>
        ) : (
          projects.map((p) => (
            <div key={p.id} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{p.title}</h3>
                <span className="text-xs px-2 py-1 rounded bg-brand-50 text-brand-700">{p.status}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">{p.description}</p>
              <p className="text-xs text-gray-500 mt-2">Team: {p.members.join(', ')}</p>
              {p.required_skills.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {p.required_skills.map((s) => (
                    <span key={s} className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">{s}</span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
