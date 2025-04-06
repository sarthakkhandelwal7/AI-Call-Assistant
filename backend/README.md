# AI Call Assistant Backend

This is the backend service for the AI Call Assistant application, built with FastAPI and Poetry.

## Setup

The backend service is configured to use the root-level `.env` file and connect to the PostgreSQL database via Docker Compose.

## Running with Docker Compose

The backend can be added to an existing Docker Compose stack:

```bash
docker-compose up -d backend
```

## API Documentation

When the service is running, you can access the API documentation at:

-   Swagger UI: http://localhost:8000/docs
-   ReDoc: http://localhost:8000/redoc
