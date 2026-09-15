import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Compare() {
  const [papers, setPapers] = useState([])
  const [selected, setSelected] = useState([])
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listPapers().then(setPapers).catch((e) => setError(e.message))
  }, [])

  const toggle = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    )
  }

  const handleCompare = async () => {
    if (selected.length < 2) {
      setError('Select at least 2 papers to compare.')
      return
    }
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const res = await api.comparePapers(selected)
      setResult(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Compare Papers</h1>
      <p className="text-gray-500 mt-1">Pick 2 or more uploaded papers to compare side-by-side.</p>

      <div className="mt-6 bg-white border border-gray-200 rounded-xl p-5">
        {papers.length === 0 ? (
          <p className="text-sm text-gray-500">Upload at least 2 papers first.</p>
        ) : (
          <div className="space-y-2">
            {papers.map((p) => (
              <label key={p.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selected.includes(p.id)}
                  onChange={() => toggle(p.id)}
                />
                {p.title}
              </label>
            ))}
          </div>
        )}
        <button
          onClick={handleCompare}
          disabled={busy || papers.length < 2}
          className="mt-4 px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-60"
        >
          {busy ? 'Comparing…' : 'Compare Selected'}
        </button>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </div>

      {result && (
        <div className="mt-6 bg-white border border-gray-200 rounded-xl p-5 overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="text-left p-2 border-b border-gray-200 font-semibold">Dimension</th>
                {result.paper_titles.map((t, i) => (
                  <th key={i} className="text-left p-2 border-b border-gray-200 font-semibold">{t}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.rows.map((row, i) => (
                <tr key={i} className="align-top">
                  <td className="p-2 border-b border-gray-100 font-medium text-gray-700">{row.dimension}</td>
                  {row.values.map((v, j) => (
                    <td key={j} className="p-2 border-b border-gray-100 text-gray-600">{v}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
