FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY transcript_cleaner /app/transcript_cleaner
COPY backend/requirements.txt /app/backend/requirements.txt

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 8000

FROM base AS dev
CMD ["uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--reload-dir", "/app/backend", "--reload-dir", "/app/transcript_cleaner"]

FROM base AS prod
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
