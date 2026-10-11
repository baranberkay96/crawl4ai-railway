# Deploy and Host Crawl4AI with Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/crawl4ai-v09-llm-ready-web-crawler?referralCode=20H68q)

Crawl4AI turns web pages into clean Markdown and structured data for LLMs, RAG pipelines and AI agents. This template runs the Crawl4AI 0.9 server with headless Chromium, a token-protected REST API, an MCP endpoint, the browser playground and monitoring dashboard, plus Redis for background job results.

## About Hosting Crawl4AI

The Crawl4AI server is a FastAPI app that drives a pool of headless Chromium browsers. Hosting it well means enough memory and shared memory for the browsers, authentication from the first request, a stable signing key for tokens, and somewhere durable for async job results. This community template builds on the official `unclecode/crawl4ai` image pinned by version and digest, generates the API token and signing key, gives Chromium 1 GiB of `/dev/shm`, checks `/health` before routing traffic, and stores job status and results in a Railway Redis so they survive redeploys. Browser pool size, idle timeout, memory guard, job workers and rate limit are adjustable through variables.

## Common Use Cases

- Converting documentation sites and articles to Markdown for RAG ingestion
- Giving Claude Code or other MCP clients a web-crawling tool through `/mcp/sse`
- Extracting structured JSON from pages with an LLM (OpenAI, Anthropic or Gemini key required)
- Running crawls from n8n, Make or your backend over plain HTTP with async jobs and polling
- Server-side screenshots and PDFs of web pages

## Dependencies for Crawl4AI Hosting

- Redis for job results and monitor statistics (included)
- Optional: an LLM provider API key for LLM-based extraction; plain crawling needs none

### Deployment Dependencies

- Crawl4AI repository: https://github.com/unclecode/crawl4ai
- Self-hosting guide: https://docs.crawl4ai.com/core/self-hosting/
- Docker deployment notes (0.9.4): https://github.com/unclecode/crawl4ai/blob/v0.9.4/deploy/docker/README.md
- Railway shared memory variable (`RAILWAY_SHM_SIZE_BYTES`): https://docs.railway.com/reference/variables

### Implementation Details

| Service | Source | Purpose |
|---|---|---|
| Crawl4AI | Dockerfile based on `unclecode/crawl4ai:0.9.4` | REST API, MCP, playground and dashboard on port 11235, healthcheck `/health` |
| Redis | `redis:8.2` with a volume | Job status and results (`/crawl/job`, `/llm/job`), dashboard statistics |

**First request**

1. Copy `CRAWL4AI_API_TOKEN` from the Crawl4AI service's Variables tab and the domain from Settings → Networking.
2. Send it as a Bearer token: `curl -X POST https://{your-domain}/md -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d '{"url": "https://example.com"}'`.
3. Open `https://{your-domain}/playground` to build requests in the browser (paste the token there) and `/dashboard` for live monitoring.
4. MCP: `claude mcp add --transport sse crawl4ai https://{your-domain}/mcp/sse --header "Authorization: Bearer {token}"`. A WebSocket transport is also available at `/mcp/ws`.
5. Client tokens: `POST /token` with `{"email": "{you@company.com}", "api_token": "{token}"}` returns a 60-minute token that can crawl but cannot run admin actions.

**Long crawls**: Railway ends single HTTP requests after 15 minutes. Use `POST /crawl/job` and poll `GET /crawl/job/{task_id}`; results stay in Redis for `REDIS_TASK_TTL` seconds.

**Tuning and scaling**: `CRAWL4AI_MAX_PAGES` caps concurrent browser pages (each needs roughly 50-150 MB), `CRAWL4AI_BROWSER_IDLE_TTL` returns memory after bursts, `CRAWL4AI_JOB_WORKERS` sets background concurrency. Scale vertically first. More replicas work for the REST API and job polling because Redis is shared; keep one replica if you rely on MCP over SSE.

**Pinning and upgrades**: the image tag and digest are in `services/crawl4ai/Dockerfile`. Change both, check the upstream migration notes, and redeploy.

**Responsible use**: you are responsible for complying with the terms of service and robots rules of the sites you crawl, applicable law, and Railway's Fair Use Policy. Internal and private network addresses are blocked by default.

This product includes software developed by UncleCode (https://x.com/unclecode) as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai).

### Why Deploy Crawl4AI on Railway?

Railway runs the browser-heavy crawler with HTTPS, private networking to Redis and your other services, and usage-based billing for the RAM and CPU it actually uses. Your agents and workflows get a crawling API you control, without managing servers.
