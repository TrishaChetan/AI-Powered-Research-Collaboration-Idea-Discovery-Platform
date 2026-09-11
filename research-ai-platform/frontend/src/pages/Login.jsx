import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-10 bg-white border border-gray-200 rounded-xl p-8">
      <h1 className="text-xl font-bold mb-6">Log in</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="text-sm font-medium">Email</label>
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-sm font-medium">Password</label>
          <input
            type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={loading}
          className="w-full py-2 rounded-md bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="text-sm text-gray-500 mt-4">
        No account? <Link to="/register" className="text-brand-600 font-medium">Register</Link>
      </p>
    </div>
  )
}
