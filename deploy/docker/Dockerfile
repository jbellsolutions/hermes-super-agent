FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml ./
COPY packages/ ./packages/
COPY src/ ./src/

RUN uv sync

COPY . .

EXPOSE 8000
ENV INSTALL_MODE=super-saiyan
CMD ["bash", "scripts/start.sh"]
