FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/platform

# Mirror the monorepo layout (backend/app -> app) so content-dir detection works.
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app ./app
RUN pip install --no-cache-dir .

# Canonical contracts + seeded content are baked into the image.
COPY schemas ./schemas
COPY content ./content

ENV SDP_CONTENT_DIR=/opt/platform/content

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
