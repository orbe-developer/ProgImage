"""Tests for the image processing endpoints and their Pydantic validation."""

from httpx import AsyncClient


async def test_compress_happy_path(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/processing/compress_image",
        params={"width": 5, "height": 5},
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert len(r.content) > 0


async def test_compress_rejects_negative_width_via_pydantic(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/processing/compress_image",
        params={"width": -5, "height": 10},
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    assert r.status_code == 422


async def test_compress_rejects_oversized_width_via_pydantic(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/processing/compress_image",
        params={"width": 100000, "height": 10},
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    assert r.status_code == 422


async def test_compress_requires_auth(
    client: AsyncClient, png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/processing/compress_image",
        params={"width": 10, "height": 10},
        files={"file": ("a.png", png_bytes, "image/png")},
    )
    assert r.status_code == 401


async def test_rotate_happy_path(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/processing/rotate_image",
        params={"angle": 90},
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    assert r.status_code == 200
    assert len(r.content) > 0


async def test_filter_blur_happy_path(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/filtering/filter_blur",
        files={"file": ("a.png", png_bytes, "image/png")},
        headers=auth_headers_a,
    )
    assert r.status_code == 200


async def test_mask_image_pair_happy_path(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/masking/mask_image",
        files=[
            ("files", ("a.png", png_bytes, "image/png")),
            ("files", ("b.png", png_bytes, "image/png")),
        ],
        headers=auth_headers_a,
    )
    assert r.status_code == 200


async def test_mask_image_wrong_arity_returns_400(
    client: AsyncClient, auth_headers_a: dict[str, str], png_bytes: bytes
) -> None:
    r = await client.post(
        "/api/v1/images/masking/mask_image",
        files=[("files", ("a.png", png_bytes, "image/png"))],
        headers=auth_headers_a,
    )
    assert r.status_code == 400
