FROM python:3.11-slim AS builder
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /app/packages /app/packages
ENV PYTHONPATH=/app/packages
COPY src/ ./src/
COPY eval/ ./eval/
COPY monitoring/ ./monitoring/
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
ENV PORT=8000
ENV WORKERS=2
EXPOSE ${PORT}
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD python -c "import requests; requests.get('http://localhost:${PORT}/health').raise_for_status()"
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS}"]
