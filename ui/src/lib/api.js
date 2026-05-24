const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function* readSSE(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';
    for (const part of parts) {
      for (const line of part.split('\n')) {
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6));
          } catch {
            /* skip */
          }
        }
      }
    }
  }
  if (buffer.trim()) {
    for (const line of buffer.split('\n')) {
      if (line.startsWith('data: ')) {
        try {
          yield JSON.parse(line.slice(6));
        } catch {
          /* skip */
        }
      }
    }
  }
}

export async function* streamChat(prompt, model, temperature, jsonMode = false) {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, model, temperature, json_mode: jsonMode }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Chat request failed');
  }

  if (jsonMode) {
    const data = await res.json();
    yield { token: JSON.stringify(data.data, null, 2), done: false };
    yield { token: '', done: true, metrics: data.metrics };
    return;
  }

  for await (const ev of readSSE(res)) {
    if (ev.error) throw new Error(ev.error);
    yield ev;
    if (ev.done) return;
  }
}

export async function* runBenchmark(models, numPrompts) {
  const res = await fetch(`${BASE_URL}/api/benchmark/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ models, num_prompts: numPrompts }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Benchmark failed');
  }

  for await (const ev of readSSE(res)) {
    yield ev;
  }
}

export async function getStatus() {
  const res = await fetch(`${BASE_URL}/api/status`);
  if (!res.ok) throw new Error('Status check failed');
  return res.json();
}

export async function getSettings() {
  const res = await fetch(`${BASE_URL}/api/settings`);
  if (!res.ok) throw new Error('Failed to load settings');
  return res.json();
}

export async function saveSettings(data) {
  const res = await fetch(`${BASE_URL}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to save settings');
  return res.json();
}

export async function getComparisonResults() {
  const res = await fetch(`${BASE_URL}/api/comparison/results`);
  if (!res.ok) throw new Error('Failed to load comparison results');
  return res.json();
}

export async function getComparisonReport() {
  const res = await fetch(`${BASE_URL}/api/comparison/report`);
  if (!res.ok) throw new Error('Failed to load report');
  return res.text();
}

export async function* runComparison() {
  const res = await fetch(`${BASE_URL}/api/comparison/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Comparison run failed');
  }

  for await (const ev of readSSE(res)) {
    yield ev;
  }
}

export async function getLatestBenchmark() {
  const res = await fetch(`${BASE_URL}/api/benchmark/latest`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load benchmark');
  return res.json();
}
