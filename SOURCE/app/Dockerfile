# syntax=docker/dockerfile:1
FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
# Optional CA for managed lab builds; ordinary Docker Desktop needs no secret.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.txt
RUN groupadd --gid 10001 lab && useradd --uid 10001 --gid lab --no-create-home lab
COPY --chown=10001:10001 . .
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "30", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
