# NOTICE: Crawl4AI v0.9 LLM-Ready Web Crawler template

This product includes software developed by UncleCode (https://x.com/unclecode) as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai).

## Software used

| Component | Source | License | How it is used |
|---|---|---|---|
| Crawl4AI server image | `unclecode/crawl4ai:0.9.4@sha256:9021b3cb…ebc9b`, https://github.com/unclecode/crawl4ai | Apache-2.0 with an additional attribution requirement (Copyright UncleCode) | Base image (`FROM`), used unmodified. At start the template writes its own `config.yml` derived from the image's upstream `config.yml` (selected keys overridden from variables, see `render_config.py`); the upstream `entrypoint.sh` and `supervisord.conf` run unchanged. The attribution above is reproduced as the license requires. |
| Chromium / Playwright, gunicorn, supervisord, bundled Redis | inside the image | their respective licenses (BSD, Apache-2.0, MIT, BSD-like, RSALv2/SSPLv1/AGPLv3 for Redis) | Run unmodified |
| Redis | `redis:8.2` (Railway base service definition) | Redis 8: RSALv2 / SSPLv1 / AGPLv3 (tri-license) | Run unmodified as a separate service |

Product names belong to their owners. This is a community template, not affiliated with UncleCode or the Crawl4AI project.

## Upstream files and docs checked (2026-10-11)

- `unclecode/crawl4ai` tag `v0.9.4` (latest stable release, 2026-09-23): `Dockerfile`, `docker-compose.yml` (shm 1 GB, 4 GB memory limit, `CRAWL4AI_API_TOKEN` passthrough), `deploy/docker/entrypoint.sh` (bind `[::]` only with a credential), `supervisord.conf`, `config.yml`, `server.py` (auth gate, `/health`, `/token`, MCP mount), `auth.py`, `auth_gate.py`, `mcp_bridge.py` (`/mcp/sse`, `/mcp/ws`), `redis_config.py` (`REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`), `utils.py` (`load_config`, cgroup-aware memory), `crawler_pool.py`, `work_queue.py`, `monitor.py`, `.llm.env.example`, `README.md`, `LICENSE`.
- Docker Hub tags for `unclecode/crawl4ai` (`0.9.4` = `latest` = digest `sha256:9021b3cb…ebc9b`).
- Railway variables reference: `RAILWAY_SHM_SIZE_BYTES` (default 67108864 bytes).

## Market templates and repositories reviewed

| Template / repo | License | Use |
|---|---|---|
| `Owzyy8` "Crawl4AI" (image-only) | n/a | Base concept (official image, token, port). Configuration rewritten. |
| `crawl4ai-1` / `salmanalfariz24/crawl4ai-railway` | Apache-2.0, Copyright 2026 Salman AlFariz | Reviewed for configuration ideas (digest pin, healthcheck, shm variable, `SECRET_KEY`). No files adapted. |
| `crawl4ai` (image-only) | n/a | Reviewed, nothing taken. |

All files in this package (`Dockerfile`, `railway-start.sh`, `render_config.py` and the docs) were written for this template. No README text from other templates was reused.
