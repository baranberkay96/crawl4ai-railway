"""Render Crawl4AI's config.yml from the upstream defaults plus Railway variables.

Usage: python3 render_config.py <upstream config.yml> <output config.yml>

Only the keys listed in OVERRIDES (plus the auth keys below) are touched;
everything else stays exactly as shipped in the pinned upstream image.
An invalid value stops the container with a clear message instead of
silently running with a different configuration.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Callable

import yaml

# variable name -> (path in config.yml, parser)
OVERRIDES: dict[str, tuple[tuple[str, ...], Callable[[str], Any]]] = {
    "CRAWL4AI_MAX_PAGES": (("crawler", "pool", "max_pages"), int),
    "CRAWL4AI_BROWSER_IDLE_TTL": (("crawler", "pool", "idle_ttl_sec"), int),
    "CRAWL4AI_MEMORY_THRESHOLD": (("crawler", "memory_threshold_percent"), float),
    "CRAWL4AI_JOB_WORKERS": (("limits", "queue", "workers"), int),
    "CRAWL4AI_RATE_LIMIT": (("rate_limiting", "default_limit"), str),
}


def _set(config: dict, path: tuple[str, ...], value: Any) -> dict:
    """Return a copy of config with path set to value (nested dicts copied)."""
    head, *rest = path
    current = config.get(head)
    if rest:
        child = current if isinstance(current, dict) else {}
        return {**config, head: _set(child, tuple(rest), value)}
    return {**config, head: value}


def _parse(name: str, raw: str, parser: Callable[[str], Any]) -> Any:
    try:
        value = parser(raw)
    except ValueError:
        sys.exit(f"render_config: {name}={raw!r} is not a valid {parser.__name__}")
    if isinstance(value, (int, float)) and value <= 0:
        sys.exit(f"render_config: {name} must be greater than 0 (got {raw!r})")
    if isinstance(value, str) and "/" not in value:
        sys.exit(f"render_config: {name} must look like '1000/minute' (got {raw!r})")
    return value


def render(config: dict, env: dict[str, str]) -> dict:
    result = config
    for name, (path, parser) in OVERRIDES.items():
        raw = env.get(name, "").strip()
        if raw:
            result = _set(result, path, _parse(name, raw, parser))

    origins = [o.strip() for o in env.get("CRAWL4AI_CORS_ORIGINS", "").split(",") if o.strip()]
    if origins:
        result = _set(result, ("security", "cors_allow_origins"), origins)

    # The static operator token in config.yml also enables POST /token, which
    # issues short-lived "data" scope JWTs to callers that present it.
    token = env.get("CRAWL4AI_API_TOKEN", "").strip()
    if token:
        result = _set(result, ("security", "api_token"), token)
    # With a fixed SECRET_KEY, jwt_enabled makes the server refuse to start if
    # the key is ever removed (instead of minting tokens with a random key).
    if env.get("SECRET_KEY", "").strip():
        result = _set(result, ("security", "jwt_enabled"), True)
    return result


def main(source: str, target: str) -> None:
    with open(source, encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    rendered = render(config, dict(os.environ))
    tmp = f"{target}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        yaml.safe_dump(rendered, handle, sort_keys=False)
    os.chmod(tmp, 0o444)
    os.replace(tmp, target)
    pool = rendered["crawler"]["pool"]
    print(
        "render_config: max_pages=%s idle_ttl_sec=%s memory_threshold=%s job_workers=%s rate=%s"
        % (
            pool.get("max_pages"),
            pool.get("idle_ttl_sec"),
            rendered["crawler"].get("memory_threshold_percent"),
            rendered.get("limits", {}).get("queue", {}).get("workers"),
            rendered["rate_limiting"].get("default_limit"),
        ),
        flush=True,
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: render_config.py <upstream config.yml> <output config.yml>")
    main(sys.argv[1], sys.argv[2])
