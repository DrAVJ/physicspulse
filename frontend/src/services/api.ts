import axios from 'axios';

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

// ====================== AUTH ======================
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(r => r.data),

  register: (name: string, email: string, password: string) =>
    api.post('/auth/register', { name, email, password }).then(r => r.data),

  me: () => api.get('/auth/me').then(r => r.data),
};

// ====================== VIDEOS ======================
export const videosApi = {
  list: () => api.get('/videos/').then(r => r.data),
  get: (id: number) => api.get(`/videos/${id}`).then(r => r.data),
  create: (data: { title: string; youtube_id?: string }) =>
    api.post('/videos/', data).then(r => r.data),
  update: (id: number, data: any) => api.patch(`/videos/${id}`, data).then(r => r.data),
  delete: (id: number) => api.delete(`/videos/${id}`),
  transcribe: (id: number) => api.post(`/videos/${id}/transcribe`).then(r => r.data),
  detectConcepts: (id: number) => api.post(`/videos/${id}/concept-detection`).then(r => r.data),
  generateQuestions: (id: number) => api.post(`/videos/${id}/generate-questions`).then(r => r.data),
  getQuestions: (id: number) => api.get(`/videos/${id}/questions`).then(r => r.data),
  getConcepts: (id: number) => api.get(`/videos/${id}/concepts`).then(r => r.data),
  updateQuestion: (id: number, qId: number, data: any) =>
    api.patch(`/videos/${id}/questions/${qId}`, data).then(r => r.data),
  deleteQuestion: (qId: number) => api.delete(`/videos/questions/${qId}`),
};

// ====================== SESSIONS ======================
export const sessionsApi = {
  list: () => api.get('/sessions/').then(r => r.data),
  create: (data: { video_id: number; class_name?: string }) =>
    api.post('/sessions/', data).then(r => r.data),
  get: (id: number) => api.get(`/sessions/${id}`).then(r => r.data),
  start: (id: number) => api.post(`/sessions/${id}/start`).then(r => r.data),
  close: (id: number) => api.post(`/sessions/${id}/close`).then(r => r.data),
  activateQuestion: (id: number, questionId: number) =>
    api.post(`/sessions/${id}/activate-question`, { question_id: questionId }).then(r => r.data),
  closeQuestion: (id: number) => api.post(`/sessions/${id}/close-question`).then(r => r.data),
  getResults: (id: number) => api.get(`/sessions/${id}/results`).then(r => r.data),
  getRecommendations: (id: number) => api.get(`/sessions/${id}/pedagogical-recommendations`).then(r => r.data),
  generateRecommendations: (id: number) =>
    api.post(`/sessions/${id}/pedagogical-recommendations`).then(r => r.data),
  joinByCode: (code: string, name: string) =>
    api.post(`/sessions/join`, { join_code: code, student_name: name }).then(r => r.data),
};

// ====================== ANSWERS ======================
export const answersApi = {
  submit: (data: { session_id: number; question_id: number; student_id: number; chosen_index: number }) =>
    api.post('/answers/', data).then(r => r.data),
};

// ====================== EXPORTS ======================
export const exportsApi = {
  sessionCSV: (id: number) =>
    api.get(`/exports/sessions/${id}/csv`, { responseType: 'blob' }).then(r => r.data),
  sessionJSON: (id: number) =>
    api.get(`/exports/sessions/${id}/json`).then(r => r.data),
};

// ====================== CONVENIENCE API OBJECT ======================
// Used by components that do api.xxx()
export const apiClient = {
  // Auth
  login: authApi.login,
  register: authApi.register,
  me: authApi.me,

  // Videos
  listVideos: videosApi.list,
  getVideo: videosApi.get,
  createVideo: videosApi.create,
  transcribeVideo: videosApi.transcribe,
  detectConcepts: videosApi.detectConcepts,
  generateQuestions: videosApi.generateQuestions,
  getQuestions: videosApi.getQuestions,
  getConcepts: videosApi.getConcepts,

  // Sessions
  listSessions: sessionsApi.list,
  createSession: sessionsApi.create,
  getSession: sessionsApi.get,
  startSession: sessionsApi.start,
  closeSession: sessionsApi.close,
  activateQuestion: sessionsApi.activateQuestion,
  closeQuestion: sessionsApi.closeQuestion,
  getSessionResults: sessionsApi.getResults,
  getRecommendations: sessionsApi.getRecommendations,
  generateRecommendations: sessionsApi.generateRecommendations,
  joinSession: sessionsApi.joinByCode,

  // Answers
  submitAnswer: answersApi.submit,

  // Exports
  exportSessionCSV: exportsApi.sessionCSV,
  exportSessionJSON: exportsApi.sessionJSON,
};

export { api };
export default apiClient;
