# GRC Studio interface – the assets are built with Node, the runtime has no Node.
# Build: docker build -f docker/ui.Dockerfile -t grc-studio-ui .
FROM node:22-bookworm-slim AS assets
WORKDIR /ui
COPY src/ui/package.json src/ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY src/ui ./
RUN npm run build

FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY src/api/pyproject.toml src/api/pyproject.toml
COPY src/ui/pyproject.toml src/ui/pyproject.toml
COPY src/contracts/pyproject.toml src/contracts/pyproject.toml
COPY src/contracts src/contracts
COPY src/ui/grc_ui src/ui/grc_ui
COPY --from=assets /ui/grc_ui/static src/ui/grc_ui/static
COPY --from=assets /ui/grc_ui/icons src/ui/grc_ui/icons
RUN uv venv /app/.venv && \
    uv export --frozen --no-dev --no-emit-workspace --package grc-ui -o /tmp/req.txt && \
    uv pip install --python /app/.venv/bin/python -r /tmp/req.txt && \
    uv pip install --python /app/.venv/bin/python --no-deps ./src/contracts ./src/ui

FROM python:3.12-slim-bookworm AS runtime
RUN groupadd --system --gid 10001 grc && useradd --system --uid 10001 --gid grc --no-create-home grc
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 10001
EXPOSE 8001
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/healthz', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "grc_ui.main:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--forwarded-allow-ips", "*"]
