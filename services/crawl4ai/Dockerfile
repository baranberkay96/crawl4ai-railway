# Crawl4AI server for Railway.
#
# Base: the official Crawl4AI Docker image (FastAPI + gunicorn, headless
# Chromium via Playwright, supervisord, loopback Redis). Pinned by tag and
# index digest; upgrade by changing both and redeploying.
FROM unclecode/crawl4ai:0.9.4@sha256:9021b3cb5c6f12570bbcd5395638495e0a06969b3148e377b953d174af2ebc9b

USER root

# railway-start.sh renders the server config from the upstream file plus
# CRAWL4AI_* variables as root, then drops to appuser and runs the upstream
# entrypoint unchanged. /app stays root-owned and read-only; /app/config.yml
# becomes a symlink to the rendered file in the root-owned /etc/crawl4ai.
COPY railway-start.sh render_config.py /usr/local/lib/crawl4ai-railway/
RUN cp /app/config.yml /usr/local/lib/crawl4ai-railway/config.upstream.yml && \
    install -d -m 0755 -o root -g root /etc/crawl4ai && \
    cp /app/config.yml /etc/crawl4ai/config.yml && \
    chmod 0644 /etc/crawl4ai/config.yml && \
    rm /app/config.yml && \
    ln -s /etc/crawl4ai/config.yml /app/config.yml && \
    chmod 0555 /usr/local/lib/crawl4ai-railway/railway-start.sh && \
    chmod 0444 /usr/local/lib/crawl4ai-railway/render_config.py \
        /usr/local/lib/crawl4ai-railway/config.upstream.yml

WORKDIR /app
CMD ["/usr/local/lib/crawl4ai-railway/railway-start.sh"]
