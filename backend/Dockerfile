# Multi-stage lightweight Dockerfile for FastAPI backend
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies required for PyMuPDF and ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runner stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app /app/app
COPY .env.example /app/.env.example

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
