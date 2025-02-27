FROM python:3.10-slim

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

# Copy only requirements to cache them in docker layer
COPY pyproject.toml /app/

# Generate poetry.lock if it doesn't exist
RUN if [ ! -f poetry.lock ]; then poetry lock; fi

# Copy project files
COPY . /app/

# Install project dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Create necessary directories
RUN mkdir -p /app/logs

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
