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

# Run with Docker Compose
echo "Starting services with Docker Compose..."
docker-compose down
docker-compose build
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
docker-compose exec backend alembic revision --autogenerate -m "Initial migration" || echo "Migration file already exists"
docker-compose exec backend alembic upgrade head

# Create admin user if it doesn't exist
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

echo "System is ready!"
echo "Access the API at: https://5a68-2a01-e0a-159-2b50-5c47-ed09-6b4d-d45f.ngrok-free.app/api/v1/docs"
echo "Access email testing at: http://localhost:8025"
echo "Access database admin at: http://localhost:8080 (postgres/password)"
