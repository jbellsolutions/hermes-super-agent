# Hermes Admiral — Railway-ready container.
#
# Runs the A2A server (agent_os.a2a.server:app) which exposes:
#   GET  /agentCard   discovery
#   POST /messages    receive delegated tasks
#   GET  /tasks/{id}  task status
#   GET  /health      Railway healthcheck
#
# In production this is the only container that needs the full hermes-super-agent
# repo + uv environment. Spawned superagents get their own VPSes via the
# bootstrap pipeline, not this image.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# uv for dependency resolution
RUN pip install --no-cache-dir uv

WORKDIR /app

# Layer 1: deps (cache-friendly)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

# Layer 2: source
COPY src ./src
COPY templates ./templates
COPY vault ./vault

# Install the project itself
RUN uv sync --no-dev --frozen

ENV PYTHONPATH=/app/src
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "agent_os.a2a.server:app", "--host", "0.0.0.0", "--port", "8080"]
