"""Test data helpers that go through the public API."""

from typing import Any

from httpx import AsyncClient

TEST_PASSWORD = "correct-horse-battery"


async def register_user(client: AsyncClient, email: str, username: str) -> dict[str, Any]:
    """Register a user and return the response body."""
    response = await client.post(
        "/users",
        json={
            "email": email,
            "username": username,
            "password": TEST_PASSWORD,
            "password_confirm": TEST_PASSWORD,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    """Log in as `email` and return the Authorization header."""
    response = await client.post(
        "/auth/token", data={"username": email, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
