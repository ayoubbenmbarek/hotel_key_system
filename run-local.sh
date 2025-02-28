#!/bin/bash

# Exit script if any command fails
set -e

# Create necessary directories
# mkdir -p certificates/apple certificates/google backend/logs

# Check if .env file exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example"
    cp .env.example .env
    echo "Please edit .env file with your actual configuration"
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python -m venv venv
    cd ..
fi

# Activate virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
cd backend
pip install poetry
poetry config virtualenvs.create false
poetry lock
poetry install
cd ..

# Check if PostgreSQL is running
pg_isready >/dev/null 2>&1 || { echo "PostgreSQL is not running. Please start PostgreSQL first."; exit 1; }

# Create database if it doesn't exist
echo "Checking if database exists..."
psql -lqt | cut -d \| -f 1 | grep -qw hotel_keys || createdb hotel_keys

# Set DATABASE_URL environment variable
export DATABASE_URL=postgresql://postgres:password@localhost/hotel_keys

# Run migrations
echo "Running database migrations..."
cd backend
alembic revision --autogenerate -m "Initial migration" || echo "Migration file already exists"
alembic upgrade head

# Check if admin user exists
echo "Checking if admin user exists..."
ADMIN_EXISTS=$(docker-compose exec db psql -U postgres -d hotel_keys -t -c "SELECT COUNT(*) FROM \"user\" WHERE email='admin@example.com';" | tr -d '[:space:]')

if [ "$ADMIN_EXISTS" = "0" ]; then
    echo "Creating admin user..."
    docker-compose exec db psql -U postgres -d hotel_keys -c "
    INSERT INTO \"user\" (id, email, first_name, last_name, phone_number, hashed_password, role, is_active, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'admin@example.com',
        'Admin',
        'User',
        '1234567890',
        '\$2b\$12\$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'ADMIN',
        true,
        NOW(),
        NOW()
    );
    "
    echo "Admin user created successfully. Email: admin@example.com, Password: admin123"
else
    echo "Admin user already exists"
fi

# Start the application
echo "Starting the application..."
cd backend
uvicorn app.main:app --reload

echo "System is ready!"
echo "Access the API at: http://localhost:8000/api/v1/docs"
