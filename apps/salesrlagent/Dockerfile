FROM node:22-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
COPY sales_agent/static /src/sales_agent/static
RUN npm run build

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SALES_DB_PATH=/app/data/sales.sqlite3
WORKDIR /app
COPY pyproject.toml ./
COPY sales_agent ./sales_agent
COPY --from=frontend /src/sales_agent/static/ui ./sales_agent/static/ui
RUN pip install --no-cache-dir '.[postgres]' && useradd --uid 10001 --create-home sales && mkdir /app/data && chown sales:sales /app/data
FROM base AS training
USER root
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir gymnasium stable-baselines3 matplotlib
RUN mkdir -p /app/artifacts && chown sales:sales /app/artifacts
USER sales
CMD ["python", "-m", "sales_agent.hrl.train", "--steps", "100000", "--episodes", "100", "--output", "/app/artifacts/docker-training"]

FROM base AS runtime
USER sales
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"
CMD ["uvicorn", "sales_agent.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
