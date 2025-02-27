# backend/tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db, Base
from app.models.user import User
from app.security import get_password_hash


# Create a test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create a test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Test database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the app's database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def test_db():
    # Create the tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPassword123",
        "phone_number": "1234567890"
    }


@pytest.fixture
def db_user(test_db, test_user):
    db = TestingSessionLocal()
    
    # Create a test user
    hashed_password = get_password_hash(test_user["password"])
    db_user = User(
        email=test_user["email"],
        first_name=test_user["first_name"],
        last_name=test_user["last_name"],
        phone_number=test_user["phone_number"],
        hashed_password=hashed_password,
        role="guest",
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    yield db_user
    
    # Clean up
    db.delete(db_user)
    db.commit()
    db.close()


@pytest.fixture
def test_admin():
    return {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "AdminPassword123",
        "phone_number": "1234567890"
    }


@pytest.fixture
def db_admin(test_db, test_admin):
    db = TestingSessionLocal()
    
    # Create an admin user
    hashed_password = get_password_hash(test_admin["password"])
    db_admin = User(
        email=test_admin["email"],
        first_name=test_admin["first_name"],
        last_name=test_admin["last_name"],
        phone_number=test_admin["phone_number"],
        hashed_password=hashed_password,
        role="admin",
        is_active=True
    )
    
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    
    yield db_admin
    
    # Clean up
    db.delete(db_admin)
    db.commit()
    db.close()


@pytest.fixture
def user_token_headers(client, db_user, test_user):
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers


@pytest.fixture
def admin_token_headers(client, db_admin, test_admin):
    login_data = {
        "username": test_admin["email"],
        "password": test_admin["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers
