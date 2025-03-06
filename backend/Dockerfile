FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false

# Copy only pyproject.toml first
COPY pyproject.toml /app/

# Generate a fresh lock file
RUN poetry lock

# Install project dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]