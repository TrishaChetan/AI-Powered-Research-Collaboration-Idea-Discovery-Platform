import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '', email: '', password: '', education: '', bio: '',
    skills: '', interests: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register({
        name: form.name,
        email: form.email,
        password: form.password,
        education: form.education,
        bio: form.bio,
        skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
        interests: form.interests.split(',').map((s) => s.trim()).filter(Boolean),
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto mt-6 bg-white border border-gray-200 rounded-xl p-8">
      <h1 className="text-xl font-bold mb-1">Create your profile</h1>
      <p className="text-sm text-gray-500 mb-6">This powers collaborator matching later.</p>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium">Name</label>
            <input required value={form.name} onChange={update('name')}
              className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="text-sm font-medium">Education</label>
            <input value={form.education} onChange={update('education')}
              placeholder="B.Tech CSE, 3rd year"
              className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium">Email</label>
          <input type="email" required value={form.email} onChange={update('email')}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-medium">Password</label>
          <input type="password" required value={form.password} onChange={update('password')}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-medium">Skills (comma separated)</label>
          <input value={form.skills} onChange={update('skills')}
            placeholder="Python, Machine Learning, CNN, OpenCV"
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-medium">Research interests (comma separated)</label>
          <input value={form.interests} onChange={update('interests')}
            placeholder="Healthcare AI, Computer Vision"
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-medium">Short bio</label>
          <textarea value={form.bio} onChange={update('bio')} rows={2}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={loading}
          className="w-full py-2 rounded-md bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="text-sm text-gray-500 mt-4">
        Already have an account? <Link to="/login" className="text-brand-600 font-medium">Log in</Link>
      </p>
    </div>
  )
}
