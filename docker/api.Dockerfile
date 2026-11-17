# GRC Studio API – multi-stage, no root at runtime.
# Build: docker build -f docker/api.Dockerfile -t grc-studio-api .
FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY src/api/pyproject.toml src/api/pyproject.toml
COPY src/ui/pyproject.toml src/ui/pyproject.toml
COPY src/contracts/pyproject.toml src/contracts/pyproject.toml
COPY src/api src/api
COPY src/contracts src/contracts
# only the API package and its dependencies, no dev tools
RUN uv venv /app/.venv && \
    uv export --frozen --no-dev --no-emit-workspace --package grc-api -o /tmp/req.txt && \
    uv pip install --python /app/.venv/bin/python -r /tmp/req.txt && \
    uv pip install --python /app/.venv/bin/python --no-deps ./src/api

FROM python:3.12-slim-bookworm AS runtime
RUN groupadd --system --gid 10001 grc && useradd --system --uid 10001 --gid grc --no-create-home grc
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"
# migrations run at start (lifespan), then the server
CMD ["grc-api", "serve", "--host", "0.0.0.0", "--port", "8000"]
