FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels /wheels/* \
    && rm -rf /wheels

COPY . .

RUN adduser --system --uid 1001 --no-create-home appuser \
    && mkdir -p /app/data /app/staticfiles \
    && chown -R appuser:root /app \
    && chmod -R g=u /app

COPY entrypoint.sh /entrypoint.sh
RUN tr -d '\r' < /entrypoint.sh > /tmp/ep.sh && mv /tmp/ep.sh /entrypoint.sh && chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

ENTRYPOINT ["sh", "/entrypoint.sh"]
