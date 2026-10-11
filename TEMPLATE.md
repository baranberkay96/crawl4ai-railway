# Crawl4AI v0.9 LLM-Ready Web Crawler: Railway template spec

## Listing

| Field | Value |
|---|---|
| Name | **Crawl4AI v0.9 LLM-Ready Web Crawler** (LISTINGS_ROUND2 base name; 0.x release → major.minor label, project tags use `v`) |
| Description | Turn websites into clean markdown for LLMs with a headless browser. (67 chars, unchanged) |
| Category | AI/ML |
| Tags | crawl4ai, crawler, scraper, markdown, llm, rag, mcp, playwright |
| Icon | `https://cdn.jsdelivr.net/gh/unclecode/crawl4ai@v0.9.4/deploy/docker/static/assets/crawl4ai-logo.png` (official asset, 200 OK; homarr dashboard-icons has no Crawl4AI icon) |

## Base market template

- **Base: `Owzyy8` "Crawl4AI"** (126 active / 300 total, the market leader). Kept: the official `unclecode/crawl4ai` image, port 11235, a generated `CRAWL4AI_API_TOKEN`, optional LLM keys. Problems fixed: `unclecode/crawl4ai:latest` (floating), no healthcheck, no shared memory setting for Chromium, no `SECRET_KEY` (MCP tool calls and JWTs use a random key that changes on every restart), README with unverifiable superlatives.
- `crawl4ai-1` (`salmanalfariz24/crawl4ai-railway`, Apache-2.0, 0 active): good hygiene ideas re-used as configuration only (digest pin, `/health` healthcheck, `RAILWAY_SHM_SIZE_BYTES`, `SECRET_KEY`). No files copied. Its claim that job state lives only in the container is addressed here by an external Redis.
- `crawl4ai` (7 active): pinned 0.9.4 with `/health`; nothing else taken.
- No README text was reused.

## Pinned versions

| Service | Image / source | Version | Released | Checked |
|---|---|---|---|---|
| Crawl4AI | `unclecode/crawl4ai:0.9.4@sha256:9021b3cb5c6f12570bbcd5395638495e0a06969b3148e377b953d174af2ebc9b` (Dockerfile in `services/crawl4ai`) | 0.9.4 (latest stable; `latest` points to the same digest) | 2026-09-23 | 2026-10-11 |
| Redis | `redis:8.2` (Railway base definition) | 8.2 | Railway base | 2026-10-11 |

Upgrade: change the `FROM` tag and digest in `services/crawl4ai/Dockerfile` (`docker buildx imagetools inspect unclecode/crawl4ai:{version}` shows the digest), read upstream `deploy/docker/MIGRATION.md`, redeploy. `render_config.py` only overrides named keys, so new upstream config keys flow through untouched.

## Architecture

```
 Clients / n8n / agents ── HTTPS + Bearer token ──► Crawl4AI :11235 (public)
 MCP clients ── /mcp/sse or /mcp/ws (Bearer) ─────┘   │  /health = healthcheck
                                                      │
 ┌────────────────────────────────────────────────────┴───────────┐
 │ Crawl4AI (Dockerfile: official image + railway-start.sh)        │
 │ railway-start.sh (root): render config.yml, wait for Redis      │
 │ → upstream entrypoint.sh → supervisord                           │
 │     ├─ gunicorn [::]:11235, 1 uvicorn worker (user appuser)      │
 │     │    FastAPI + browser pool (headless Chromium) + job queue  │
 │     └─ bundled redis-server 127.0.0.1 (user appuser, fallback)   │
 └───────────────┬─────────────────────────────────────────────────┘
                 │ redis://default:…@redis.railway.internal:6379
                 ▼
          Redis (volume /data): job status/results (TTL), monitor stats
```

Why the separate Redis: the server stores `/crawl/job` and `/llm/job` status and results plus dashboard statistics in Redis. With the bundled loopback Redis they vanish on every redeploy and are local to one replica. The Railway Redis keeps results retrievable across redeploys (a webhook-less client polling `GET /crawl/job/{id}` keeps working), moves result payloads out of the browser container's memory, and lets several replicas share job state. Upstream supports this directly through `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`. The bundled Redis still starts (upstream supervisord config, ~5 MB idle) and becomes the fallback if `REDIS_HOST` is set to `localhost`.

## Services

### Crawl4AI

| Setting | Value |
|---|---|
| Source | repo `baranberkay96/crawl4ai-railway`, root `/services/crawl4ai` (Dockerfile) |
| Start | image CMD `railway-start.sh` |
| Healthcheck | `/health` (public, returns `{"status":"ok","version":"0.9.4"}`), timeout 300 s |
| Public domain | yes, target port 11235 |
| Volume | none (stateless; job state in Redis) |
| Restart policy | ON_FAILURE, 10 retries |
| Replicas | 1 (see scaling notes) |

Files in `services/crawl4ai/`:

- `Dockerfile`: `FROM` the pinned official image, copies the two files below, keeps the upstream `config.yml` as `config.upstream.yml`, replaces `/app/config.yml` with a symlink to `/etc/crawl4ai/config.yml` (root-owned; `/app` stays read-only as upstream intends), runs as root only for the start script.
- `render_config.py`: loads the upstream config and overrides only `crawler.pool.max_pages`, `crawler.pool.idle_ttl_sec`, `crawler.memory_threshold_percent`, `limits.queue.workers`, `rate_limiting.default_limit`, `security.cors_allow_origins` from variables, sets `security.api_token` from `CRAWL4AI_API_TOKEN` (this enables `POST /token`) and `security.jwt_enabled: true` when `SECRET_KEY` is set (fail fast if the key ever disappears). Invalid values stop the start with a clear message. File is written 0444.
- `railway-start.sh`: renders the config, waits up to `REDIS_WAIT_SECONDS` (120) for the external Redis (non-fatal; the app tolerates a missing Redis), exports `HOME=/home/appuser` and execs the upstream `entrypoint.sh` unchanged. supervisord runs as root only so it can open its log dispatchers on the container's root-owned stdout/stderr; gunicorn and Redis run as `appuser` (`user=appuser` in the upstream supervisord config). Tested: starting supervisord as `appuser` after a root start fails with `EACCES` on `/dev/stdout`.

Variables: see `template.json` (all optional; `CRAWL4AI_API_TOKEN` and `SECRET_KEY` generated). Pool and queue defaults equal upstream's.

### Redis

Railway base definition (`_railway-base/redis.json`): `redis:8.2`, password from `secret()`, AOF-less snapshots (`--save 60 1`) on the `/data` volume.

## First use

1. Copy `CRAWL4AI_API_TOKEN` from the Crawl4AI service variables and the public domain from Settings → Networking.
2. `curl https://{domain}/health` → 200 without a token.
3. `curl -X POST https://{domain}/md -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d '{"url":"https://example.com"}'` returns Markdown.
4. Playground: `https://{domain}/playground` (paste the token into its auth field); monitor: `https://{domain}/dashboard`.
5. MCP: `claude mcp add --transport sse crawl4ai https://{domain}/mcp/sse --header "Authorization: Bearer {token}"`.
6. Per-client tokens: `POST /token` with `{"email": "{you@company.com}", "api_token": "{token}"}` returns a 60-minute JWT with `data` scope (no admin/monitor actions). The email domain must have an MX record.

## Improvements over market templates

1. **Pinned image by tag and digest** (0.9.4) instead of `latest`.
2. **Healthcheck** on `/health` and `PORT` set; 1 GiB `/dev/shm` for Chromium as upstream's compose file does.
3. **Stable `SECRET_KEY`** (MCP tool calls and JWTs keep working across restarts) and `jwt_enabled` fail-fast; **`POST /token`** enabled for short-lived per-client tokens.
4. **External Redis** for job results and monitor stats: survive redeploys, shared by replicas, out of the browser container's RAM.
5. **Browser pool, memory guard, job workers, rate limit and CORS tunable from variables** without forking the image; upstream config otherwise untouched.
6. Upstream security posture kept: API bound to all interfaces only with a token, SSRF egress pinning, hooks and `/execute_js` off, `/app` read-only.
7. Honest README with Crawl4AI's required attribution and a responsible-crawling note.

## Resource estimate

Railway prices: RAM $10/GB-month, vCPU $20/vCPU-month, volume $0.15/GB-month.

| Service | Idle RAM / CPU | Typical RAM / CPU | Notes |
|---|---|---|---|
| Crawl4AI | 0.6 GB / 0.02 vCPU (permanent browser + API) | 2 GB / 0.5 vCPU avg, peaks 3-4 GB | Measured locally: ~0.9 GB after a few crawls with two pooled browsers; every concurrent page adds ~50-150 MB |
| Redis | 0.01 GB / ~0 | 0.05 GB | Job results expire after `REDIS_TASK_TTL` |
| Volume (Redis) | 0.1 GB | 0.5 GB | |

Estimated monthly cost: **idle ≈ $7** (0.61 GB × $10 + 0.02 vCPU × $20), **typical ≈ $31** (2.05 GB × $10 + 0.5 vCPU × $20 + 0.5 GB × $0.15). Heavy parallel crawling scales with `CRAWL4AI_MAX_PAGES`.

Minimum plan: **Hobby**. Upstream recommends at least 4 GB for the container (its Docker healthcheck flags < 2 GB); Trial's 1 GB per service is not enough for Chromium under load.

## Scaling notes

- Vertical first: raise `CRAWL4AI_MAX_PAGES` and `CRAWL4AI_JOB_WORKERS` as RAM allows.
- Horizontal: `numReplicas` > 1 works for the REST API and for job polling (shared Redis). Caveats: MCP over SSE needs the same replica for the stream and its POSTs and Railway has no sticky sessions, so use `/mcp/ws` or one replica for MCP; `/artifacts/{id}` files (screenshots/PDFs stored server-side) live on the replica that produced them; rate limits are per replica.

## Verification checklist

Local (done 2026-10-11, `docker build --platform linux/amd64` + `docker run --init --shm-size 1g` with a `redis:8.2` container on a user network): build OK; rendered config shows overrides; gunicorn `Listening at: http://[::]:11235`; `/health` 200; `/crawl` without token 401; `/md` with token returned Markdown for example.com; `/crawl/job` completed and `task:{id}` plus `monitor:endpoint_stats` keys appeared in the external Redis; `POST /token` returned a JWT that was accepted by `/md`; `/mcp/sse` with token streamed an `endpoint` event; `/playground/` 200; processes: supervisord root, everything else `appuser`.

On first Railway deploy:

- [ ] Build OK; deploy healthy on `/health`; logs show `render_config:` and `Redis reachable at redis.railway.internal:6379`.
- [ ] `POST /md` with the token returns Markdown; without the token 401.
- [ ] `POST /crawl/job`, then redeploy Crawl4AI, then `GET /crawl/job/{task_id}` still returns the result.
- [ ] `/mcp/sse` connects from Claude Code with the Bearer header.
- [ ] `df -h /dev/shm` in a Railway shell shows 1.0G.

## Open questions

- `RAILWAY_SHM_SIZE_BYTES` is documented by Railway (default 64 MB); upstream Chromium also runs with `--disable-dev-shm-usage`, so a smaller value would not break crawling.
- Railway's per-request limit (15 minutes) caps synchronous `/crawl` calls and SSE streams; long crawls should use `/crawl/job`.
- Whether Railway's container runtime grants `CAP_DAC_OVERRIDE` to root does not matter here (the rendered config lives in a root-owned directory), but supervisord as root is a deviation from upstream's non-root supervisord, documented above.
- The bundled Redis inside the image keeps running even when the external Redis is used; disabling it would require replacing upstream's supervisord config.
