# Agent Mini App

Telegram Mini App artifacts and low-latency delivery setup.

## Current hosting modes

1. **Immediate local path**: this repo is served by a safe local Python server on `127.0.0.1:8788`, then exposed through Cloudflare Tunnel.
2. **Cloudflare Worker router**: tries local tunnel first; if local returns `404`, `5xx`, times out, or the tunnel is down, falls back to backup hosting.
3. **Backup hosting**: Cloudflare Pages or GitHub Pages can serve the same committed files for durable old links.

## Local safe server

```bash
cd /Users/sluan/Projects/agent-miniapp
scripts/start-local-server.sh
```

The server intentionally blocks dotfiles, `.git`, `node_modules`, `worker`, `scripts`, path traversal, and arbitrary extensions.

## Worker

Worker entrypoint:

```text
worker/src/index.js
```

Worker config:

```text
wrangler.toml
```

Required Worker secrets:

```bash
wrangler secret put LOCAL_ORIGIN
wrangler secret put BACKUP_ORIGIN
```

Example values:

```text
LOCAL_ORIGIN=https://agent-miniapp-local.example.com
BACKUP_ORIGIN=https://lsuper.github.io/agent-miniapp/
```

## Artifact naming

Write generated Mini Apps directly into this repo root, e.g.

```text
simo-earnings-analysis-2026-05-10.html
mind-offload-organizer-2026-05-10.html
assets/example.png
```

The same path should work through local tunnel and backup origin.

## Telegram URL shape

```text
https://<worker-host>/<artifact>.html?v=<timestamp>
```

Always append `?v=<timestamp>` to avoid Telegram WebView cache.
