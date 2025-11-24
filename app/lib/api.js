// app/lib/api.js
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export async function apiFetch(path, opts = {}) {
  const url = API_BASE + path;
  const res = await fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
    ...opts,
  });

  if (!res.ok) {
    let body;
    try { body = await res.json(); } catch (e) { body = { detail: 'Unknown error' }; }
    const err = new Error(body.detail || `${res.status} ${res.statusText}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }

  return res.status === 204 ? null : res.json();
}
