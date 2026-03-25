import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token from localStorage on startup
const token = localStorage.getItem('token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Response interceptor for auth errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API helper functions
export const videosApi = {
  list: () => api.get('/videos/'),
  get: (id: number) => api.get(`/videos/${id}`),
  create: (data: any) => api.post('/videos/', data),
  update: (id: number, data: any) => api.put(`/videos/${id}`, data),
  delete: (id: number) => api.delete(`/videos/${id}`),
  transcribe: (id: number) => api.post(`/videos/${id}/transcribe`),
  detectConcepts: (id: number) => api.post(`/videos/${id}/detect-concepts`),
  generateQuestions: (id: number, conceptId: number) =>
    api.post(`/videos/${id}/generate-questions`, { concept_id: conceptId }),
  getQuestions: (id: number) => api.get(`/videos/${id}/questions`),
}

export const sessionsApi = {
  list: () => api.get('/sessions/'),
  create: (data: any) => api.post('/sessions/', data),
  get: (id: number) => api.get(`/sessions/${id}`),
  start: (id: number) => api.post(`/sessions/${id}/start`),
  close: (id: number) => api.post(`/sessions/${id}/close`),
  activateQuestion: (id: number, questionId: number) =>
    api.post(`/sessions/${id}/activate-question/${questionId}`),
  getResults: (id: number) => api.get(`/sessions/${id}/results`),
  joinByCode: (code: string, nickname: string) =>
    api.post('/sessions/join', { join_code: code, nickname }),
}

export const answersApi = {
  submit: (data: any) => api.post('/answers/', data),
  getDistribution: (sessionId: number, questionId: number) =>
    api.get(`/answers/session/${sessionId}/question/${questionId}/distribution`),
  getSessionAnswers: (sessionId: number) =>
    api.get(`/answers/session/${sessionId}`),
}

export const exportsApi = {
  csv: (sessionId: number) =>
    api.get(`/exports/session/${sessionId}/csv`, { responseType: 'blob' }),
  json: (sessionId: number) => api.get(`/exports/session/${sessionId}/json`),
  summary: (sessionId: number) => api.get(`/exports/session/${sessionId}/summary`),
}

export const recommendationsApi = {
  get: (sessionId: number) => api.get(`/recommendations/session/${sessionId}`),
  getVideoMisconceptions: (videoId: number) =>
    api.get(`/recommendations/video/${videoId}/misconceptions`),
}
