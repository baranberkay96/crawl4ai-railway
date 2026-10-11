#!/usr/bin/env bash
# Railway start wrapper for the official Crawl4AI image.
#
# 1. As root: render /etc/crawl4ai/config.yml (/app/config.yml links to it)
#    with pool/memory/queue/rate-limit tuning and auth keys from variables.
#    /app and the rendered file stay read-only for the runtime user.
# 2. Optionally wait (bounded) for the external Railway Redis.
# 3. Exec the upstream entrypoint.sh, which resolves the bind address (all
#    interfaces only when CRAWL4AI_API_TOKEN is set) and starts supervisord.
#    supervisord stays root only to open its log dispatchers on the
#    container's stdout/stderr (a root-owned pipe on Railway and Docker);
#    both programs it runs, gunicorn (API + Chromium) and the bundled
#    loopback Redis, run as appuser via `user=appuser` in the upstream
#    supervisord.conf.
set -euo pipefail

LIB=/usr/local/lib/crawl4ai-railway

if [[ "$(id -u)" != "0" ]]; then
    echo "railway-start: not running as root; using the image's config.yml unchanged" >&2
    exec bash /app/entrypoint.sh
fi

if [[ -z "${CRAWL4AI_API_TOKEN:-}" ]]; then
    echo "railway-start: WARNING: CRAWL4AI_API_TOKEN is empty; Crawl4AI will only listen on loopback and the healthcheck will fail" >&2
fi

python3 "${LIB}/render_config.py" "${LIB}/config.upstream.yml" /etc/crawl4ai/config.yml

redis_host="${REDIS_HOST:-localhost}"
if [[ "${redis_host}" != "localhost" && "${redis_host}" != "127.0.0.1" ]]; then
    REDIS_WAIT_HOST="${redis_host}" REDIS_WAIT_PORT="${REDIS_PORT:-6379}" \
    REDIS_WAIT_SECONDS="${REDIS_WAIT_SECONDS:-120}" python3 - <<'PY'
import os, socket, sys, time

host, port = os.environ["REDIS_WAIT_HOST"], int(os.environ["REDIS_WAIT_PORT"])
deadline = time.monotonic() + int(os.environ["REDIS_WAIT_SECONDS"])
while True:
    try:
        socket.create_connection((host, port), timeout=3).close()
        print(f"railway-start: Redis reachable at {host}:{port}", flush=True)
        break
    except OSError as exc:
        if time.monotonic() > deadline:
            print(f"railway-start: Redis {host}:{port} not reachable ({exc}); starting anyway", file=sys.stderr)
            break
        time.sleep(2)
PY
fi

# Children inherit this environment; Playwright finds its browsers via HOME.
export HOME=/home/appuser USER=appuser LOGNAME=appuser
cd /app
exec bash /app/entrypoint.sh
