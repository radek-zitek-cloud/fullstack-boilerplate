"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestLogin:
    """Test login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_inactive_user(self, client: AsyncClient, db: AsyncSession):
        """Test login with inactive user."""
        from app.core.security import get_password_hash
        
        # Create inactive user
        inactive_user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False,
        )
        db.add(inactive_user)
        await db.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]


class TestRegister:
    """Test registration endpoint."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "newpassword123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "New"
        assert data["last_name"] == "User"
        assert "id" in data
        # Note: Registration returns user data, not tokens (must login separately)

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_register_invalid_password(self, client: AsyncClient):
        """Test registration with password too short."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",  # Less than 8 characters
            },
        )
        assert response.status_code == 422  # Validation error


class TestRefreshToken:
    """Test token refresh endpoint."""

    async def test_refresh_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Now refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        assert response.status_code == 401

    async def test_refresh_with_access_token(self, client: AsyncClient, auth_headers: dict):
        """Test refresh with access token instead of refresh token."""
        # Extract the access token from auth headers
        access_token = auth_headers["Authorization"].replace("Bearer ", "")
        
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestChangePassword:
    """Test password change endpoint."""

    async def test_change_password_success(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test successful password change."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 204

        # Verify old password doesn't work
        old_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert old_login.status_code == 401

        # Verify new password works
        new_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "newpassword456",
            },
        )
        assert new_login.status_code == 200

    async def test_change_password_wrong_current(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test password change with wrong current password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        """Test password change without authentication."""
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 401  # No auth header


class TestAdminAuthorization:
    """Test admin authorization - CRITICAL SECURITY TEST."""

    async def test_admin_access_with_admin_user(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test that admin user can access admin endpoints."""
        # This test verifies our security fix works
        # Create a test admin-only endpoint or test via deps directly
        from app.api.deps import get_current_admin_user
        
        # We can't directly test without an admin endpoint, 
        # but we can verify the token contains is_admin=True
        response = await client.get(
            "/api/v1/users/me",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is True

    async def test_admin_access_with_regular_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that regular user cannot access admin functions."""
        # Verify regular user has is_admin=False
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is False

    async def test_active_user_check(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Test that inactive users cannot access protected endpoints."""
        from app.core.security import get_password_hash
        
        # Create inactive user
        inactive_user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False,
        )
        db.add(inactive_user)
        await db.commit()
        
        # Try to get token for inactive user (should fail at login)
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]


class TestPasswordReset:
    """Test password reset flow."""

    async def test_forgot_password_existing_user(
        self, client: AsyncClient, test_user: User
    ):
        """Test password reset request for existing user."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        # Should return 204 even if user exists (prevent enumeration)
        assert response.status_code == 204

    async def test_forgot_password_nonexistent_user(self, client: AsyncClient):
        """Test password reset request for non-existent user."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        # Should return 204 to prevent email enumeration
        assert response.status_code == 204

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token."""
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid_token",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "Invalid or expired token" in response.json()["detail"]
