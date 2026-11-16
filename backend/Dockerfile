# Build context: repository root. Persistent host must mount /data.
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY docs/schema-handoff.json /srv/docs/schema-handoff.json
RUN mkdir -p /data
ENV SQLITE_PATH=/data/offline.db DEV2_DATABASE_URL=sqlite:////data/dev2_clinical.db \
    ATTACHMENTS_ROOT=/data/attachments \
    SCHEMA_MANIFEST_PATH=/srv/docs/schema-handoff.json
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
