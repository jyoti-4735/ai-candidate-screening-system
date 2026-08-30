const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  health: () => fetch(`${BASE_URL}/api/health`).then(handle),
  roles: () => fetch(`${BASE_URL}/api/roles`).then(handle),

  startSession: (role, resumeFile) => {
    const form = new FormData();
    form.append("role", role);
    form.append("resume", resumeFile);
    return fetch(`${BASE_URL}/api/interview/start`, { method: "POST", body: form }).then(handle);
  },

  nextQuestion: (sessionId) =>
    fetch(`${BASE_URL}/api/interview/${sessionId}/next-question`).then(handle),

  submitAnswer: (sessionId, questionId, answerText) =>
    fetch(`${BASE_URL}/api/interview/${sessionId}/questions/${questionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer_text: answerText }),
    }).then(handle),

  finishSession: (sessionId) =>
    fetch(`${BASE_URL}/api/interview/${sessionId}/finish`, { method: "POST" }).then(handle),
};
