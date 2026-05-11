const LOCAL_TIMEOUT_MS = 1500;
const HTML_UNAVAILABLE = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Mini App unavailable</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0f172a;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;padding:24px}.card{max-width:560px;background:#111827;border:1px solid #334155;border-radius:20px;padding:24px;box-shadow:0 20px 60px #0008}h1{margin:0 0 10px;font-size:24px}p{line-height:1.55;color:#cbd5e1}</style></head><body><main class="card"><h1>Mini App temporarily unavailable</h1><p>The local copy and backup copy were both unavailable. Try again in a moment.</p></main></body></html>`;

function isAllowedPath(pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch (_) {
    return false;
  }
  if (decoded.includes('\0')) return false;
  if (decoded === '/' || decoded === '/index.html') return true;
  if (decoded.includes('..') || decoded.includes('//')) return false;
  const parts = decoded.split('/').filter(Boolean);
  if (parts.some((p) => p.startsWith('.') || ['.git', '.env', 'node_modules', 'worker', 'scripts'].includes(p))) {
    return false;
  }
  return /^\/[A-Za-z0-9._\/-]+\.(html|css|js|json|png|jpg|jpeg|webp|svg|gif|ico|txt)$/.test(decoded);
}

async function fetchWithTimeout(url, ms) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort('local-timeout'), ms);
  try {
    return await fetch(url, {
      signal: controller.signal,
      cf: { cacheTtl: 0, cacheEverything: false },
    });
  } finally {
    clearTimeout(timer);
  }
}

function cloneWithSourceHeaders(response, source) {
  const headers = new Headers(response.headers);
  headers.set('x-miniapp-source', source);
  headers.set('access-control-allow-origin', '*');
  if (source === 'local') {
    headers.set('cache-control', 'no-store, max-age=0');
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function buildOriginUrl(origin, requestUrl) {
  const out = new URL(requestUrl.pathname, origin);
  out.search = requestUrl.search;
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (!['GET', 'HEAD'].includes(request.method)) {
      return new Response('Method not allowed', { status: 405 });
    }

    if (!isAllowedPath(url.pathname)) {
      return new Response('Not found', { status: 404 });
    }

    const localOrigin = env.LOCAL_ORIGIN;
    const backupOrigin = env.BACKUP_ORIGIN;
    if (!localOrigin || !backupOrigin) {
      return new Response('Worker is missing LOCAL_ORIGIN or BACKUP_ORIGIN', { status: 500 });
    }

    const localUrl = buildOriginUrl(localOrigin, url);
    const backupUrl = buildOriginUrl(backupOrigin, url);

    let localResponse = null;
    try {
      localResponse = await fetchWithTimeout(localUrl, LOCAL_TIMEOUT_MS);
    } catch (_) {
      localResponse = null;
    }

    // Local is the fast primary source only when successful. Any local 404,
    // 403, 5xx, timeout, or tunnel-down error falls back to backup.
    if (localResponse && localResponse.ok) {
      return cloneWithSourceHeaders(localResponse, 'local');
    }

    let backupResponse = null;
    try {
      backupResponse = await fetch(backupUrl, { cf: { cacheTtl: 60, cacheEverything: false } });
    } catch (_) {
      backupResponse = null;
    }

    if (backupResponse && backupResponse.ok) {
      return cloneWithSourceHeaders(backupResponse, 'backup');
    }

    return new Response(HTML_UNAVAILABLE, {
      status: 404,
      headers: {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'no-store, max-age=0',
        'x-miniapp-source': 'unavailable',
      },
    });
  },
};
