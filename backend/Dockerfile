# Build from the REPO ROOT (not backend/), since this image needs both
# backend/ and model/ as siblings:
#   docker build -f backend/Dockerfile -t dixon-coles-api .
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY model /app/model
COPY backend /app/backend

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Render (and similar platforms) assign the listen port via $PORT at
# runtime instead of using a fixed one — fall back to 8000 for local
# `docker run` where $PORT isn't set. Shell form (not exec-array form)
# is required here so $PORT actually gets expanded.
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
