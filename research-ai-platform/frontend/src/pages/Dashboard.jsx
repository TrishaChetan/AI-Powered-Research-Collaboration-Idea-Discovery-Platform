import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import api from '../api'

function StatCard({ label, value, to }) {
  return (
    <Link to={to} className="bg-white border border-gray-200 rounded-xl p-5 hover:border-brand-400 transition">
      <div className="text-3xl font-bold text-brand-600">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </Link>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [papers, setPapers] = useState([])
  const [ideas, setIdeas] = useState([])
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.listPapers(), api.listIdeas(), api.listProjects()])
      .then(([p, i, pr]) => { setPapers(p); setIdeas(i); setProjects(pr) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold">Welcome back, {user?.name?.split(' ')[0]}!</h1>
      <p className="text-gray-500 mt-1">Here's where your research stands.</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <StatCard label="Research Papers" value={papers.length} to="/papers" />
        <StatCard label="Saved Ideas" value={ideas.length} to="/ideas" />
        <StatCard label="Projects" value={projects.length} to="/projects" />
        <StatCard label="Skills Listed" value={user?.skills?.length || 0} to="/collaborators" />
      </div>

      <div className="mt-10 grid md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="font-semibold mb-3">Recent papers</h2>
          {loading ? (
            <p className="text-sm text-gray-400">Loading…</p>
          ) : papers.length === 0 ? (
            <p className="text-sm text-gray-500">No papers yet. <Link to="/papers" className="text-brand-600">Upload one</Link>.</p>
          ) : (
            <ul className="space-y-2">
              {papers.slice(0, 5).map((p) => (
                <li key={p.id} className="text-sm">
                  <Link to={`/papers/${p.id}`} className="text-gray-800 hover:text-brand-600">{p.title}</Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="font-semibold mb-3">Recent ideas</h2>
          {loading ? (
            <p className="text-sm text-gray-400">Loading…</p>
          ) : ideas.length === 0 ? (
            <p className="text-sm text-gray-500">No ideas yet. <Link to="/ideas" className="text-brand-600">Generate some</Link>.</p>
          ) : (
            <ul className="space-y-2">
              {ideas.slice(0, 5).map((idea) => (
                <li key={idea.id} className="text-sm text-gray-800">{idea.title}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
