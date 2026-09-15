const BASE_URL = 'http://localhost:8001'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, { method = 'GET', body, auth = true, isForm = false } = {}) {
  const headers = {}
  if (!isForm) headers['Content-Type'] = 'application/json'
  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch (_) {}
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  register: (data) => request('/auth/register', { method: 'POST', body: data, auth: false }),
  login: (data) => request('/auth/login', { method: 'POST', body: data, auth: false }),
  me: () => request('/auth/me'),
  listUsers: () => request('/users'),

  listPapers: () => request('/papers'),
  getPaper: (id) => request(`/papers/${id}`),
  uploadPaper: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/papers/upload', { method: 'POST', body: form, isForm: true })
  },
  summarizePaper: (id) => request(`/papers/${id}/summarize`, { method: 'POST' }),
  askPaper: (id, question) => request(`/papers/${id}/ask`, { method: 'POST', body: { paper_id: id, question } }),
  paperGaps: (id) => request(`/papers/${id}/gaps`),

  generateIdeas: (payload) => request('/ideas/generate', { method: 'POST', body: payload }),
  listIdeas: () => request('/ideas'),
  buildOnIdea: (ideaId, numIdeas = 2) =>
    request(`/ideas/${ideaId}/build-on`, { method: 'POST', body: { num_ideas: numIdeas } }),
  exportIdeaUrl: (ideaId) => `${BASE_URL}/ideas/${ideaId}/export`,

  relatedPapers: (paperId) => request(`/papers/${paperId}/related`),
  comparePapers: (paperIds) => request('/papers/compare', { method: 'POST', body: { paper_ids: paperIds } }),

  matchCollaborators: (payload) => request('/match', { method: 'POST', body: payload }),

  createProject: (payload) => request('/projects', { method: 'POST', body: payload }),
  listProjects: () => request('/projects'),
}

export default api
