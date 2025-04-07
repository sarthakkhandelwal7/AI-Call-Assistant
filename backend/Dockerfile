# Stage 1: Build Stage with all dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies needed for build (and potentially runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tk \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy only files needed for dependency installation
COPY poetry.lock pyproject.toml ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install all dependencies (including dev) but NOT the project root itself yet
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application code (including README.md and source files)
COPY . .

# Optional: Run tests here if desired
# RUN poetry run pytest

# Stage 2: Production Stage
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    tk \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy only files needed for dependency installation
COPY poetry.lock pyproject.toml ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install only production dependencies using the correct flag and excluding the project root
RUN poetry install --no-interaction --no-ansi --without dev --no-root

# Copy application code from builder stage
COPY --from=builder /app /app

# Expose the port the app runs on
EXPOSE 8000

# Production CMD: Use gunicorn or uvicorn without reload
# Using Gunicorn as a robust production server
# Adjust workers based on CPU cores (e.g., (2 * $CPU_CORES) + 1)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]

# Alternative CMD using Uvicorn directly (simpler, may be sufficient)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 