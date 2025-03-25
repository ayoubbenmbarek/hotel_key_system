#!/bin/bash

# Exit script if any command fails
set -e

# Parse command line arguments
RESET=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--reset]"
            echo "  --reset: Reset database and remove all data"
            exit 1
            ;;
    esac
done

# Create necessary directories
# mkdir -p certificates/apple certificates/google backend/logs

# Check if .env file exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example"
    cp .env.example .env
    echo "Please edit .env file with your actual configuration"
fi

# Start services
echo "Starting services with Docker Compose..."
if [ "$RESET" = true ]; then
    echo "Resetting all containers and data..."
    docker-compose down -v
else
    echo "Stopping containers while preserving data..."
    docker-compose down
fi

docker-compose up -d

# Function to wait for database to be ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    until docker-compose exec -T db pg_isready -U postgres; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up and running!"
}

# Wait for database
wait_for_db

if [ "$RESET" = true ]; then
    # Reset database completely
    echo "Resetting database..."
    docker-compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS hotel_keys;"
    docker-compose exec -T db psql -U postgres -c "CREATE DATABASE hotel_keys;"

    # Initialize database with migrations
    echo "Running database migrations..."
    docker-compose exec -T backend alembic stamp base
    docker-compose exec -T backend alembic upgrade head

    # Create admin user
    echo "Creating admin user..."
    HASHED_PASSWORD=$(docker-compose exec -T backend python -c "from app.security import get_password_hash; print(get_password_hash('password123'))")

    docker-compose exec -T db psql -U postgres -d hotel_keys -c "
    INSERT INTO \"user\" (id, email, first_name, last_name, phone_number, hashed_password, role, is_active, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'admin@example.com',
        'Admin',
        'User',
        '1234567890',
        '${HASHED_PASSWORD}',
        'ADMIN',
        true,
        NOW(),
        NOW()
    );"
    echo "Admin user created successfully. Email: admin@example.com, Password: password123"
else
    # Just run any pending migrations
    echo "Checking for and applying any pending migrations..."
    docker-compose exec -T backend alembic upgrade head
fi

echo "System is ready!"
echo "Access the API at: https://8b8b-2a01-e0a-159-2b50-fc89-6241-570a-86b.ngrok-free.app/api/v1/docs"
echo "Access email testing at: http://localhost:8025"
echo "Access database admin at: http://localhost:8080 (postgres/password)"
echo "use flag --reset to reset database and remove all data"