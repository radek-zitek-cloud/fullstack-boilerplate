"""Tests for user endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestGetCurrentUser:
    """Test get current user endpoint."""

    async def test_get_current_user_success(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test getting current user profile."""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert "id" in data

    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestUpdateProfile:
    """Test update profile endpoint."""

    async def test_update_profile_success(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test updating user profile."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "note": "This is a test note",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["note"] == "This is a test note"

    async def test_update_profile_partial(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test partial update of user profile."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "first_name": "OnlyFirstName",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "OnlyFirstName"
        # Last name should remain unchanged
        assert data["last_name"] == test_user.last_name

    async def test_update_profile_unauthenticated(self, client: AsyncClient):
        """Test updating profile without authentication."""
        response = await client.patch(
            "/api/v1/users/me",
            json={"first_name": "Test"},
        )
        assert response.status_code == 401
