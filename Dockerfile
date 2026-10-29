FROM node:22-bookworm-slim AS web-build
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.14-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STORESPARK_HOST=0.0.0.0 \
    STORESPARK_PORT=8000 \
    STORESPARK_DATA_DIR=/app/data
WORKDIR /app
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY storespark/ ./storespark/
COPY --from=web-build /build/web/dist/ ./web/dist/
RUN pip install --no-cache-dir --no-deps . \
    && useradd --system --uid 10001 --create-home storespark \
    && mkdir -p /app/data \
    && chown 10001:10001 /app/data \
    && chmod 700 /app/data
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"
CMD ["python", "-m", "storespark"]
