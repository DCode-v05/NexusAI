FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for spaCy, PyPDF2, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./
RUN uv sync --frozen || uv sync

# Download spaCy model
RUN uv run python -m spacy download en_core_web_sm || true

# Copy source and alembic
COPY src/ src/
COPY alembic.ini ./
COPY alembic/ alembic/
COPY scripts/ scripts/

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
