FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.32" \
    "httpx>=0.27" \
    "pydantic>=2.9"

COPY wrapper.py .

EXPOSE 8001
CMD ["python", "-m", "uvicorn", "wrapper:app", "--host", "0.0.0.0", "--port", "8001"]
