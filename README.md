# Hotel Virtual Key System

A complete solution for hotels to provide digital room keys to guests via mobile wallet integration.

## Features

- **Digital Room Keys**: Generate virtual keys for hotel room access
- **Mobile Wallet Integration**: Support for Apple Wallet and Google Wallet
- **NFC Access Control**: Unlock doors using smartphone NFC
- **Secure Authentication**: JWT-based API authentication
- **Key Management**: Create, activate, deactivate, and extend key validity
- **Email Delivery**: Send keys directly to guests' email
- **Access Logging**: Track all key usage and access attempts

## System Architecture

The system consists of the following components:

1. **Backend API**: FastAPI application for key management and verification
2. **Database**: PostgreSQL for data storage
3. **Email Service**: Email delivery for key distribution
4. **Wallet Integration**: Apple and Google Wallet pass generation
5. **NFC Communication**: Door lock integration for key verification
6. **Admin Dashboard**: Web interface for hotel staff (optional)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Node.js 16+ (for frontend)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hotel-key-system.git
   cd hotel-key-system
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your configurations
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the API at http://localhost:8000 and the admin dashboard at http://localhost:3000

### Development Setup

1. Backend setup:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install poetry
   poetry install
   ```

2. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

## API Documentation

Once the backend is running, access the API documentation at:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Key Endpoints

- `POST /api/v1/auth/login`: Authenticate and get access token
- `POST /api/v1/keys`: Create a new digital key
- `PATCH /api/v1/keys/{key_id}/activate`: Activate a key
- `PATCH /api/v1/keys/{key_id}/extend`: Extend key validity
- `POST /api/v1/verify/key`: Verify a key for door access

## Security Considerations

- All API endpoints (except verification) require authentication
- Keys have limited validity periods based on reservation dates
- Access attempts are logged for security auditing
- Staff permissions are required for sensitive operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
