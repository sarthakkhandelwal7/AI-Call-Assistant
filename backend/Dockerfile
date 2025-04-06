FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Tk
RUN apt-get update && apt-get install -y --no-install-recommends \
    tk \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Generate a fresh lock file and install dependencies (without installing the root package)
RUN poetry lock && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Start the FastAPI application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 