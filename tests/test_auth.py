"""Tests for the authentication endpoints."""

from httpx import AsyncClient


async def test_register_success(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "password": "longenough"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@test.com"
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_rejected(client: AsyncClient) -> None:
    payload = {"email": "dup@test.com", "password": "longenough"}
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


async def test_register_weak_password_rejected(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@test.com", "password": "short"},
    )
    assert r.status_code == 422


async def test_register_malformed_email_rejected(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "longenough"},
    )
    assert r.status_code == 422


async def test_login_success_returns_bearer_token(
    client: AsyncClient, user_a_token: str
) -> None:
    assert isinstance(user_a_token, str)
    assert len(user_a_token) > 20


async def test_login_wrong_password_rejected(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "pw@test.com", "password": "longenough"},
    )
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "pw@test.com", "password": "wrongpass"},
    )
    assert r.status_code == 401


async def test_login_nonexistent_user_rejected(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@test.com", "password": "longenough"},
    )
    assert r.status_code == 401


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


async def test_me_with_token_returns_user(
    client: AsyncClient, auth_headers_a: dict[str, str]
) -> None:
    r = await client.get("/api/v1/auth/me", headers=auth_headers_a)
    assert r.status_code == 200
    assert r.json()["email"] == "a@test.com"


async def test_me_with_tampered_token_returns_401(client: AsyncClient) -> None:
    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert r.status_code == 401
