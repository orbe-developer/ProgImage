"""Tests for image upload and retrieval, including access control."""

from httpx import AsyncClient


async def test_upload_requires_auth(client: AsyncClient, png_bytes: bytes) -> None:
    r = await client.post(
        "/api/v1/images",
        files={"file": ("a.png", png_bytes, "image/png")},
    )
    assert r.status_code == 401


async def test_upload_success(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images",
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["content_type"] == "image/png"
    assert body["description"] == "a.png"
    assert body["id"] >= 1
    assert "created_at" in body


async def test_upload_wrong_content_type_rejected(
    client: AsyncClient, auth_headers_a: dict[str, str]
) -> None:
    r = await client.post(
        "/api/v1/images",
        files={"file": ("a.txt", b"not an image", "text/plain")},
        headers=auth_headers_a,
    )
    assert r.status_code == 406


async def test_owner_can_fetch_their_image(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    upload = await client.post(
        "/api/v1/images",
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    image_id = upload.json()["id"]
    r = await client.get(f"/api/v1/images/{image_id}", headers=auth_headers_a)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")
    assert r.content == png_bytes


async def test_non_owner_gets_404_not_leaked_as_403(
    client: AsyncClient,
    auth_headers_a: dict[str, str],
    auth_headers_b: dict[str, str],
    png_bytes: bytes,
) -> None:
    """Access control: another user's images must look like they do not exist."""
    upload = await client.post(
        "/api/v1/images",
        files={"file": ("secret.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    image_id = upload.json()["id"]
    r = await client.get(f"/api/v1/images/{image_id}", headers=auth_headers_b)
    assert r.status_code == 404


async def test_fetch_nonexistent_image_returns_404(
    client: AsyncClient, auth_headers_a: dict[str, str]
) -> None:
    r = await client.get("/api/v1/images/999999", headers=auth_headers_a)
    assert r.status_code == 404
