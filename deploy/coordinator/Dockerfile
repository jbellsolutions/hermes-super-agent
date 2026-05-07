FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Layer 1: dependencies (cache-friendly)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.32" \
    "httpx>=0.27" \
    "pydantic>=2.9" \
    "anthropic>=0.39" \
    "openai>=1.54" \
    "python-dotenv>=1.0" \
    "nats-py>=2.7"

# Layer 2: source
COPY src ./src

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "coordinator.main:app", "--host", "0.0.0.0", "--port", "8000"]
