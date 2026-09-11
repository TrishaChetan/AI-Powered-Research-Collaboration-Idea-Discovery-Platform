import React from 'react'
import { Link } from 'react-router-dom'

const STEPS = [
  { icon: '📄', title: 'Upload a paper', desc: 'Drop in any research PDF.' },
  { icon: '🔎', title: 'Understand it', desc: 'Ask questions, get grounded answers with page citations.' },
  { icon: '🧠', title: 'Find gaps', desc: 'AI surfaces limitations and open problems.' },
  { icon: '💡', title: 'Generate ideas', desc: 'Turn gaps into concrete project ideas.' },
  { icon: '👥', title: 'Find people', desc: 'Match with collaborators who have the right skills.' },
  { icon: '🚀', title: 'Build it', desc: 'Spin up a project workspace with your team.' },
]

export default function Landing() {
  return (
    <div>
      <section className="text-center py-16">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900">
          Discover research. <span className="text-brand-600">Find opportunities.</span> Build teams.
        </h1>
        <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
          Upload research papers, chat with them using RAG, uncover research gaps,
          generate new project ideas, and get matched with collaborators who have
          complementary skills — all running on a free local LLM.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link to="/register" className="px-6 py-3 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700">
            Get Started
          </Link>
          <Link to="/login" className="px-6 py-3 rounded-lg border border-gray-300 font-semibold hover:bg-gray-100">
            Log in
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-2 md:grid-cols-3 gap-6 py-10">
        {STEPS.map((s) => (
          <div key={s.title} className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="text-3xl">{s.icon}</div>
            <h3 className="mt-3 font-semibold">{s.title}</h3>
            <p className="mt-1 text-sm text-gray-600">{s.desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
