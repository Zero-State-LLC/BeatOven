# BeatOven production container (Render + Azure compatible)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BEATOVEN_HOST=0.0.0.0 \
    BEATOVEN_PORT=8000

WORKDIR /app

# System dependencies kept minimal for deterministic builds
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
        build-essential \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY README.md setup.py pyproject.toml ./
COPY beatoven ./beatoven
COPY scripts ./scripts

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000

# Respect platform-provided PORT while keeping deterministic defaults
CMD ["sh", "-c", "uvicorn beatoven.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${BEATOVEN_WORKERS:-1}"]
