# backend/tests/test_users.py
import pytest
from fastapi.testclient import TestClient


def test_read_users_me(client, user_token_headers, db_user):
    """Test getting current user info"""
    response = client.get("/api/v1/users/me", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == db_user.email
    assert data["first_name"] == db_user.first_name
    assert data["last_name"] == db_user.last_name


def test_update_user_me(client, user_token_headers, db_user):
    """Test updating current user info"""
    data = {"first_name": "Updated", "last_name": "Name"}
    response = client.put("/api/v1/users/me", headers=user_token_headers, json=data)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["first_name"] == "Updated"
    assert updated_data["last_name"] == "Name"
    assert updated_data["email"] == db_user.email


def test_create_user_admin(client, admin_token_headers):
    """Test creating a new user (admin only)"""
    user_data = {
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "NewPassword123",
        "phone_number": "9876543210",
        "role": "guest"
    }
    response = client.post("/api/v1/users", headers=admin_token_headers, json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert "password" not in data  # Password should not be returned


def test_create_user_normal_user_forbidden(client, user_token_headers):
    """Test that normal users cannot create other users"""
    user_data = {
        "email": "another@example.com",
        "first_name": "Another",
        "last_name": "User",
        "password": "AnotherPassword123",
        "phone_number": "5555555555"
    }
    response = client.post("/api/v1/users", headers=user_token_headers, json=user_data)
    assert response.status_code == 403  # Forbidden


def test_read_users_admin(client, admin_token_headers, db_user):
    """Test that admins can list all users"""
    response = client.get("/api/v1/users", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the admin user should be there


def test_read_users_normal_user_forbidden(client, user_token_headers):
    """Test that normal users cannot list all users"""
    response = client.get("/api/v1/users", headers=user_token_headers)
    assert response.status_code == 403  # Forbidden


def test_read_user_by_id_admin(client, admin_token_headers, db_user):
    """Test that admins can get a specific user by ID"""
    response = client.get(f"/api/v1/users/{db_user.id}", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == db_user.id
    assert data["email"] == db_user.email


def test_read_user_by_id_normal_user_forbidden(client, user_token_headers, db_admin):
    """Test that normal users cannot get other users by ID"""
    response = client.get(f"/api/v1/users/{db_admin.id}", headers=user_token_headers)
    assert response.status_code == 403  # Forbidden


def test_update_user_admin(client, admin_token_headers, db_user):
    """Test that admins can update other users"""
    update_data = {"first_name": "AdminUpdated", "last_name": "UserName"}
    response = client.put(f"/api/v1/users/{db_user.id}", headers=admin_token_headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "AdminUpdated"
    assert data["last_name"] == "UserName"
    assert data["id"] == db_user.id


def test_delete_user_admin(client, admin_token_headers, db_user):
    """Test that admins can deactivate users"""
    response = client.delete(f"/api/v1/users/{db_user.id}", headers=admin_token_headers)
    assert response.status_code == 204  # No content
    
    # Verify user is deactivated
    response = client.get(f"/api/v1/users/{db_user.id}", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert not data["is_active"]


def test_register_new_user(client):
    """Test user registration"""
    user_data = {
        "email": "register@example.com",
        "first_name": "Register",
        "last_name": "User",
        "password": "RegisterPass123",
        "phone_number": "8765432109"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert "password" not in data  # Password should not be returned
    
    # Try to register with same email
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400  # Bad request - user already exists


def test_login_access_token(client, db_user, test_user):
    """Test login to get access token"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    
    # Test with wrong password
    login_data["password"] = "wrong-password"
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401  # Unauthorized
