import axios from 'axios'

const request = axios.create({
  baseURL: '',
  timeout: 60000,
})

// ===== 会话管理 =====
export function listSessions() {
  return request.get('/api/sessions')
}

export function createSession() {
  return request.post('/api/sessions')
}

export function deleteSession(id) {
  return request.delete(`/api/sessions/${id}`)
}

export function getMessages(id) {
  return request.get(`/api/sessions/${id}/messages`)
}

// ===== 对话 =====
export function sendChat(message, sessionId) {
  return request.post('/api/chat', { message, session_id: sessionId })
}

export function sendAgentChat(message, sessionId) {
  return request.post('/api/agent/chat', { message, session_id: sessionId })
}
