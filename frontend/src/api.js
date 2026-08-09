const DEFAULT_BASE_URL = 'http://127.0.0.1:8000/api';

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL
).replace(/\/$/, '');

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...options.headers,
    },
  });

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof payload === 'object'
      ? payload.error || payload.detail || payload.message
      : payload;
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (payload && typeof payload === 'object' && payload.error) {
    throw new Error(payload.error);
  }

  return payload;
}

export function fetchBackendStatus() {
  return apiRequest('/status');
}

export function fetchConfig() {
  return apiRequest('/config');
}

export function saveConfig(configData) {
  return apiRequest('/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(configData),
  });
}

export function triggerSetupSession() {
  return apiRequest('/run-setup', { method: 'POST' });
}

export function triggerSniperRun() {
  return apiRequest('/run-sniper', { method: 'POST' });
}

export function fetchSniperRunStatus() {
  return apiRequest('/run-sniper/status');
}
