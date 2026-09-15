import React, { useEffect, useState } from 'react'
import api from '../api'

function IdeaCard({ idea, onBuildOn, busyId, childCount }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold">{idea.title}</h3>
        {idea.parent_idea_id && (
          <span className="shrink-0 text-xs px-2 py-1 rounded bg-purple-50 text-purple-700">
            builds on #{idea.parent_idea_id}
          </span>
        )}
      </div>
      <p className="text-sm text-gray-600 mt-2"><strong>Problem:</strong> {idea.problem}</p>
      <p className="text-sm text-gray-600 mt-1"><strong>Approach:</strong> {idea.approach}</p>
      <p className="text-xs text-gray-500 mt-2">Skills: {idea.required_skills_text}</p>
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <span className="text-xs px-2 py-1 rounded bg-brand-50 text-brand-700">{idea.difficulty}</span>
        {childCount > 0 && (
          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-500">
            {childCount} follow-up idea{childCount > 1 ? 's' : ''}
          </span>
        )}
      </div>
      <div className="mt-4 flex gap-2">
        <button
          onClick={() => onBuildOn(idea.id)}
          disabled={busyId === idea.id}
          className="text-sm px-3 py-1.5 rounded-md border border-brand-300 text-brand-600 hover:bg-brand-50 disabled:opacity-60"
        >
          {busyId === idea.id ? 'Generating…' : 'Build on this idea'}
        </button>
        <a
          href={api.exportIdeaUrl(idea.id)}
          target="_blank"
          rel="noreferrer"
          className="text-sm px-3 py-1.5 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50"
        >
          Export as PDF
        </a>
      </div>
    </div>
  )
}

export default function Ideas() {
  const [ideas, setIdeas] = useState([])
  const [loading, setLoading] = useState(true)
  const [interests, setInterests] = useState('')
  const [busy, setBusy] = useState(false)
  const [busyBuildOnId, setBusyBuildOnId] = useState(null)
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

  const handleBuildOn = async (ideaId) => {
    setBusyBuildOnId(ideaId)
    setError('')
    try {
      await api.buildOnIdea(ideaId, 2)
      load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusyBuildOnId(null)
    }
  }

  // Group ideas by lineage: top-level (no parent) first, followed by their children.
  const topLevel = ideas.filter((i) => !i.parent_idea_id)
  const childCountFor = (id) => ideas.filter((i) => i.parent_idea_id === id).length
  const childrenOf = (id) => ideas.filter((i) => i.parent_idea_id === id)

  return (
    <div>
      <h1 className="text-2xl font-bold">Research Ideas</h1>
      <p className="text-gray-500 mt-1">
        Generate ideas from your uploaded papers or from scratch, then build on any idea to
        create a lineage of follow-up ideas — or export one as a proposal PDF.
      </p>

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

      <div className="mt-6 space-y-6">
        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : topLevel.length === 0 ? (
          <p className="text-sm text-gray-500">No ideas saved yet.</p>
        ) : (
          topLevel.map((idea) => (
            <div key={idea.id}>
              <IdeaCard idea={idea} onBuildOn={handleBuildOn} busyId={busyBuildOnId} childCount={childCountFor(idea.id)} />
              {childrenOf(idea.id).length > 0 && (
                <div className="mt-3 ml-8 pl-4 border-l-2 border-brand-100 space-y-3">
                  {childrenOf(idea.id).map((child) => (
                    <IdeaCard
                      key={child.id}
                      idea={child}
                      onBuildOn={handleBuildOn}
                      busyId={busyBuildOnId}
                      childCount={childCountFor(child.id)}
                    />
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
