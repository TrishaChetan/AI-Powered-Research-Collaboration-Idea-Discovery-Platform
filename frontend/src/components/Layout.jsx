import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/papers', label: 'Papers' },
  { to: '/compare', label: 'Compare' },
  { to: '/ideas', label: 'Ideas' },
  { to: '/collaborators', label: 'Collaborators' },
  { to: '/projects', label: 'Projects' },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2 font-bold text-lg text-brand-700">
            <span className="inline-block w-7 h-7 rounded-md bg-brand-600 text-white text-sm flex items-center justify-center">R</span>
            ResearchAI
          </Link>

          {user && (
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={
                    location.pathname.startsWith(item.to)
                      ? 'text-brand-600'
                      : 'text-gray-600 hover:text-brand-600'
                  }
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          )}

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-gray-500 hidden sm:inline">{user.name}</span>
                <button
                  onClick={() => { logout(); navigate('/') }}
                  className="text-sm px-3 py-1.5 rounded-md border border-gray-300 hover:bg-gray-100"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm px-3 py-1.5 rounded-md hover:bg-gray-100">Log in</Link>
                <Link to="/register" className="text-sm px-3 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700">
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">{children}</main>
    </div>
  )
}
