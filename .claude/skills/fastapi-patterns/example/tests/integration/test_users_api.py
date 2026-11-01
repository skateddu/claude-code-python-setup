"""User API behaviour through HTTP, against an in-memory database."""

from httpx import AsyncClient
import pytest

from tests.factories import auth_headers, register_user

pytestmark = pytest.mark.integration


async def test_register_user_valid_payload_returns_public_fields(client: AsyncClient) -> None:
    user = await register_user(client=client, email="ada@example.com", username="ada")

    assert user["email"] == "ada@example.com"
    assert "hashed_password" not in user


async def test_register_user_duplicate_email_returns_conflict(client: AsyncClient) -> None:
    await register_user(client=client, email="ada@example.com", username="ada")

    response = await client.post(
        "/users",
        json={
            "email": "ada@example.com",
            "username": "ada2",
            "password": "correct-horse-battery",
            "password_confirm": "correct-horse-battery",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


async def test_register_user_mismatched_passwords_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/users",
        json={
            "email": "ada@example.com",
            "username": "ada",
            "password": "correct-horse-battery",
            "password_confirm": "something-else-entirely",
        },
    )

    assert response.status_code == 422


async def test_login_wrong_password_returns_401_with_challenge(client: AsyncClient) -> None:
    await register_user(client=client, email="ada@example.com", username="ada")

    response = await client.post(
        "/auth/token", data={"username": "ada@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_read_current_user_with_token_returns_user(client: AsyncClient) -> None:
    await register_user(client=client, email="ada@example.com", username="ada")
    headers = await auth_headers(client=client, email="ada@example.com")

    response = await client.get("/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == "ada"


async def test_read_current_user_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/users/me")

    assert response.status_code == 401


async def test_update_user_other_account_returns_403(client: AsyncClient) -> None:
    await register_user(client=client, email="ada@example.com", username="ada")
    other = await register_user(client=client, email="bob@example.com", username="bob")
    headers = await auth_headers(client=client, email="ada@example.com")

    response = await client.patch(
        f"/users/{other['id']}", json={"username": "taken"}, headers=headers
    )

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


async def test_list_users_pages_in_stable_order(client: AsyncClient) -> None:
    for name in ("ada", "bob", "cyd"):
        await register_user(client=client, email=f"{name}@example.com", username=name)
    headers = await auth_headers(client=client, email="ada@example.com")

    response = await client.get("/users", params={"offset": 1, "limit": 1}, headers=headers)

    assert response.json()["total"] == 3
    assert [user["username"] for user in response.json()["items"]] == ["bob"]
