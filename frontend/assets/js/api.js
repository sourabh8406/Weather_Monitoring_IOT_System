const API_BASE = 'http://localhost:8000';

function getToken() { return localStorage.getItem('weather_token'); }

function authHeaders() {
  return { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' };
}

async function apiGet(path) {
  const r = await fetch(API_BASE + path, { headers: authHeaders() });
  if (r.status === 401) { localStorage.clear(); window.location.href = '../login.html'; return null; }
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function apiPost(path, body) {
  return fetch(API_BASE + path, { method: 'POST', headers: authHeaders(), body: JSON.stringify(body) });
}

async function apiPatch(path, body) {
  return fetch(API_BASE + path, { method: 'PATCH', headers: authHeaders(), body: JSON.stringify(body) });
}

async function apiPut(path, body) {
  return fetch(API_BASE + path, { method: 'PUT', headers: authHeaders(), body: JSON.stringify(body) });
}

function logout() { localStorage.clear(); window.location.href = '../login.html'; }
