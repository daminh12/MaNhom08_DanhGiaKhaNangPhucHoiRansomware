FROM restic/restic:0.18.1 AS restic
COPY backup.py /usr/bin/backup.py
FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/tool:${PATH}"
COPY --from=restic /usr/bin/restic /usr/bin/backup.py /tool/
ENTRYPOINT ["python", "/tool/backup.py"]
