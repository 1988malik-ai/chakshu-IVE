# Chakshu — Linux/macOS container (API + built React UI in one process)
# Not a Windows .exe; use GitHub Actions or a Windows VM for that.

FROM node:20-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-fast.txt requirements-video.txt pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY scripts/check-media-deps.py ./scripts/check-media-deps.py

COPY requirements-reports.txt ./

RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir --prefer-binary -r requirements-fast.txt \
    && pip install --no-cache-dir -r requirements-video.txt \
    && pip install --no-cache-dir -r requirements-reports.txt \
    && pip install --no-cache-dir -e . --no-deps

COPY --from=frontend /app/frontend/dist ./frontend/dist

ENV PYTHONPATH=/app/src
ENV AIVE_API_HOST=0.0.0.0
ENV AIVE_API_PORT=9450
ENV AIVE_FRONTEND_DIST=/app/frontend/dist

EXPOSE 9450

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9450/api/health')" || exit 1

CMD ["python", "-m", "aive.api._launcher", "--host", "0.0.0.0", "--port", "9450", "--frontend-dist", "/app/frontend/dist"]
