FROM python:3.12.11-slim AS builder
WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --prefix=/install .

FROM python:3.12.11-slim
RUN groupadd --system nexus && useradd --system --gid nexus --home /app nexus
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=nexus:nexus src ./src
ENV PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER nexus
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"
ENTRYPOINT ["uvicorn"]
CMD ["nexus_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
