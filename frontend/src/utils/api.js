import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 60000 })
api.interceptors.response.use(r => r.data,
  err => Promise.reject(new Error(err.response?.data?.detail || err.message || 'Request failed')))

export const workflowAPI = {
  list: (params) => api.get('/workflows/', { params }),
  get: (id) => api.get(`/workflows/${id}`),
  create: (data) => api.post('/workflows/', data),
  update: (id, data) => api.put(`/workflows/${id}`, data),
  toggle: (id) => api.patch(`/workflows/${id}/toggle`),
  delete: (id) => api.delete(`/workflows/${id}`),
  run: (id, data) => api.post(`/workflows/${id}/run_sync`, data),
  getRuns: (id, limit) => api.get(`/workflows/${id}/runs`, { params: { limit } }),
  getAllRuns: (limit) => api.get('/workflows/runs/all', { params: { limit } }),
}

export const connectionAPI = {
  listApps: () => api.get('/connections/apps'),
  getApp: (key) => api.get(`/connections/apps/${key}`),
  list: () => api.get('/connections/'),
  create: (data) => api.post('/connections/', data),
  analyzeResume: (file, jobTitle = '', jobDescription = '') => {
    const form = new FormData()
    form.append('file', file)
    form.append('job_title', jobTitle)
    form.append('job_description', jobDescription)
    return api.post('/connections/resume-screen', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  test: (id) => api.post(`/connections/${id}/test`),
  delete: (id) => api.delete(`/connections/${id}`),
}

export const webhookAPI = {
  create: (workflowId) => api.post(`/webhooks/create?workflow_id=${workflowId}`),
  list: () => api.get('/webhooks/list'),
}

export const analyticsAPI = {
  summary: () => api.get('/analytics/summary'),
}

export const aiAPI = {
  inferDepartment: (task) => api.get('/auto-config/infer-department', { params: { task } }),
  configureAgent: (task, department, userId) => api.post('/auto-config/configure-agent', null, {
    params: { task, department, user_id: userId },
  }),
  processVoiceCommand: (voiceText, autoExecute = true) =>
    api.post('/auto-config/voice-command', null, {
      params: { voice_text: voiceText, auto_execute: autoExecute },
    }),
  transcribeAudio: (audioBase64, language = 'en', audioFormat = 'webm') =>
    api.post('/auto-config/voice-transcribe', {
      audio_base64: audioBase64,
      language,
      audio_format: audioFormat,
    }),
  listSupportedDepartments: () => api.get('/auto-config/supported-departments'),
}

export const knowledgeBaseAPI = {
  list: (companyId = 'default') => api.get(`/knowledge-base/list/${companyId}`),
  create: (data) => api.post('/knowledge-base/create', data),
  uploadDocument: (kbId, file, docType = 'text') => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/knowledge-base/upload-document/${kbId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { doc_type: docType },
    })
  },
  search: (kbId, query, topK = 5) => api.get(`/knowledge-base/search/${kbId}`, { params: { query, top_k: topK } }),
  export: (kbId) => api.post(`/knowledge-base/export/${kbId}`),
  delete: (kbId) => api.delete(`/knowledge-base/${kbId}`),
}

export const voiceAPI = {
  transcribe: async (blob, language = 'en') => {
    const base64Audio = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result
        if (typeof result !== 'string') {
          reject(new Error('Unable to read audio input'))
          return
        }
        resolve(result.split(',')[1])
      }
      reader.onerror = () => reject(new Error('Unable to read audio input'))
      reader.readAsDataURL(blob)
    })

    const response = await aiAPI.transcribeAudio(base64Audio, language, blob.type?.includes('wav') ? 'wav' : 'webm')
    return { transcript: response.transcribed_text || '' }
  },
}

export default api
