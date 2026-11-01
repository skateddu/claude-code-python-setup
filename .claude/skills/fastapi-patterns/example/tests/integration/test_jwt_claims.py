"""JWT claim validation and partial-update edge cases."""

from datetime import datetime, timedelta, timezone
from typing import Any

from httpx import AsyncClient
import jwt
import pytest

from my_app.config import Settings
from tests.factories import auth_headers, register_user

pytestmark = pytest.mark.integration


def _bearer(settings: Settings, claims: dict[str, Any]) -> dict[str, str]:
    """Sign `claims` with the app's own key: a valid signature on chosen claims."""
    encoded = jwt.encode(
        claims, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return {"Authorization": f"Bearer {encoded}"}


def _in_an_hour() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "1", "iss": "my-app"},
        {"sub": "1", "iss": "another-service", "exp": _in_an_hour()},
        {"sub": "1", "exp": _in_an_hour()},
    ],
    ids=["no-expiry", "foreign-issuer", "no-issuer"],
)
async def test_read_current_user_rejects_missing_or_foreign_claims(
    client: AsyncClient, settings: Settings, claims: dict[str, Any]
) -> None:
    await register_user(client=client, email="ada@example.com", username="ada")

    response = await client.get("/users/me", headers=_bearer(settings=settings, claims=claims))

    assert response.status_code == 401


async def test_update_user_explicit_null_returns_422(client: AsyncClient) -> None:
    """Omitting a field leaves it alone; sending null for it is a validation error."""
    user = await register_user(client=client, email="ada@example.com", username="ada")
    headers = await auth_headers(client=client, email="ada@example.com")

    response = await client.patch(f"/users/{user['id']}", json={"email": None}, headers=headers)

    assert response.status_code == 422


async def test_update_user_omitted_field_is_left_unchanged(client: AsyncClient) -> None:
    user = await register_user(client=client, email="ada@example.com", username="ada")
    headers = await auth_headers(client=client, email="ada@example.com")

    response = await client.patch(
        f"/users/{user['id']}", json={"username": "ada2"}, headers=headers
    )

    assert response.json()["email"] == "ada@example.com"
    assert response.json()["username"] == "ada2"
