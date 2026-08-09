// Set this to your deployed backend URL before shipping. Kept as a plain
// const (not an env var baked at build time) so it's obvious and easy to
// point at localhost during dev.
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

// Every request carries the same candidate_id everywhere — set once here.
export const CANDIDATE_ID = import.meta.env.VITE_CANDIDATE_ID || "uday.jhariyaa@gmail.com";

async function request(path, options = {}) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export function generateSampleEmails(n = 250) {
  return request(`/api/sample-emails?n=${n}`);
}

export function ingestEmails(emails) {
  return request(`/ingest`, {
    method: "POST",
    body: JSON.stringify({ candidate_id: CANDIDATE_ID, emails }),
  });
}

export function getStats() {
  return request(`/api/stats?candidate_id=${encodeURIComponent(CANDIDATE_ID)}`);
}

export function askChat(query) {
  return request(`/api/chat`, {
    method: "POST",
    body: JSON.stringify({ candidate_id: CANDIDATE_ID, query }),
  });
}