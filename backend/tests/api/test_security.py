"""Tests for security features."""

import pytest
from httpx import AsyncClient


class TestSecurityHeaders:
    """Test that security headers are present on all responses."""

    async def test_security_headers_on_api_endpoint(self, client: AsyncClient):
        """Test that security headers are present on API responses."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        
        # Check all security headers are present
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    async def test_csp_header_content(self, client: AsyncClient):
        """Test that CSP header has appropriate content."""
        response = await client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        
        # Should contain basic directives
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp

    async def test_permissions_policy_header(self, client: AsyncClient):
        """Test that Permissions-Policy restricts device access."""
        response = await client.get("/health")
        pp = response.headers.get("Permissions-Policy", "")
        
        # Should restrict sensitive APIs
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp


class TestUploadAuthentication:
    """Test upload endpoint authentication - CRITICAL SECURITY TEST."""

    async def test_upload_requires_authentication(self, client: AsyncClient):
        """Test that file upload requires authentication."""
        # Create a test file
        files = {
            "file": ("test.txt", b"test content", "text/plain"),
        }
        
        response = await client.post(
            "/api/v1/uploads/upload",
            files=files,
        )
        # Should require authentication (401 or 403)
        assert response.status_code in [401, 403]

    async def test_get_upload_requires_authentication(self, client: AsyncClient):
        """Test that retrieving uploaded file requires authentication."""
        response = await client.get("/api/v1/uploads/uploads/test-file.txt")
        
        # Should require authentication (returns 401, 403, or 404)
        assert response.status_code in [401, 403, 404]


class TestCORSConfiguration:
    """Test CORS configuration."""

    async def test_cors_preflight(self, client: AsyncClient):
        """Test CORS preflight request."""
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    async def test_cors_headers_on_response(self, client: AsyncClient):
        """Test CORS headers are present on actual requests."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test"},
            headers={"Origin": "http://localhost:5173"},
        )
        
        assert "access-control-allow-origin" in response.headers
