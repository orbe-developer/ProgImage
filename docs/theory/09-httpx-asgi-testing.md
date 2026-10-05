# 09 — Testing FastAPI with httpx and ASGITransport

## ¿Qué es?

httpx is a modern HTTP client for Python that mirrors `requests`' API while adding first-class async support and HTTP/2. Its `AsyncClient` is the async counterpart of `httpx.Client`. For testing an ASGI application like FastAPI, httpx ships `ASGITransport`, a transport that speaks the ASGI protocol directly to your app in-process — no socket, no port, no running server. The result is end-to-end HTTP-level testing that is as fast as a function call: a test issues `await client.post("/api/v1/images", ...)` and httpx round-trips the request through the FastAPI app in the same event loop, returning a real `Response` object.

## ¿Por qué lo usamos?

Testing a FastAPI app end-to-end has two schools: spin up a real server, or drive the app through ASGI in-process. The in-process approach is dramatically faster (no socket overhead, no port races, no fixtures around starting and stopping a server), and because httpx returns the same `Response` object a production call would, the tests look identical to what a client would write. We pair this with [`08-pytest-asyncio.md`](08-pytest-asyncio.md) for async fixtures, FastAPI's dependency-override machinery for swapping the database to an in-memory SQLite, and the result is a test suite that runs the whole stack — routing, validation, auth, DB, serialisation — in milliseconds per test.

## ¿Cómo funciona?

### `AsyncClient` + `ASGITransport`

The wiring is done once per test by the `client` fixture at `tests/conftest.py:56`:

```python
@pytest_asyncio.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Anonymous async HTTP client with get_session overridden."""

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    app.dependency_overrides.clear()
```

Three things are happening:

- `ASGITransport(app=app)` wraps the FastAPI instance in the httpx transport interface. Any request made through this client is handed to the app via its ASGI entry point.
- `AsyncClient(transport=transport, base_url="http://test")` builds a client whose requests go through that transport. `base_url` is a placeholder — the hostname is never resolved — but setting it lets tests call relative paths like `/api/v1/auth/login`.
- `async with` ensures the client is cleanly closed after the test, even on failure.

### Dependency overrides

FastAPI's `app.dependency_overrides` is a dict mapping a dependency callable to a replacement. Any route that does `Depends(get_session)` will, inside the test, receive sessions from `_override_get_session` instead. ProgImage uses this to swap the real Postgres session for an in-memory SQLite one so each test gets a clean, isolated database. The `app.dependency_overrides.clear()` at the end of the fixture is non-negotiable — overrides are process-global, and forgetting to clear them leaks state into the next test.

### In-memory SQLite

The engine fixture at `tests/conftest.py:32` builds `sqlite+aiosqlite:///:memory:` and runs `Base.metadata.create_all` against it. Because the engine is per-test and in-memory, there is nothing to tear down beyond disposing the engine, and tests cannot interfere with each other through shared rows. The small cost is that SQLite is not Postgres: certain features (JSONB, array columns, some constraint behaviour) will not be exercised. For ProgImage's schema (two tables, standard types) this gap is immaterial, and the migrations themselves still run against real Postgres in Docker.

### Lifespan handling

An ASGI app has a `lifespan` protocol — the startup/shutdown hooks that `app/main.py` uses to create tables and dispose the engine. `ASGITransport` by default does *not* trigger lifespan events, which is intentional: the test fixture is already building its own engine and schema, and firing the production lifespan would try to connect to Postgres. Should a test actually need the lifespan to run (e.g., to exercise a startup handler), httpx offers `LifespanManager` from `asgi-lifespan` or newer httpx versions expose `ASGITransport(..., lifespan="on")`.

### Pre-authenticated clients

The pattern for giving tests a logged-in user composes fixtures. `tests/conftest.py:73` defines a helper that registers and logs in through the real endpoints:

```python
async def _register_and_login(http: AsyncClient, email: str, password: str) -> str:
    r = await http.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    r = await http.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]
```

And `tests/conftest.py:88` wraps that into a `user_a_token` fixture that any test can consume. Note the mix of `json=` (register uses JSON) and `data=` (login uses form-urlencoded, per the OAuth2 password-grant spec). Two users are provided (`user_a_*`, `user_b_*`) so authorisation tests have cross-user scenarios ready.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **`starlette.testclient.TestClient`** | Synchronous. Works, but forces an async-to-sync bridge inside every test, which is awkward when the rest of the suite is async. Uses `requests` under the hood. |
| **`httpx.AsyncClient` against a real server (uvicorn in a thread)** | Exercises networking too. Slower, flakier (port conflicts, lifecycle), and no clear benefit over `ASGITransport` for most tests. |
| **`async-asgi-testclient`** | Earlier async client built for ASGI. Mostly obsolete now that httpx provides `ASGITransport` natively. |
| **Playwright / Selenium against the deployed app** | True end-to-end including the browser. Belongs in a separate tier, not in the pytest suite. |

Specific friction: `ASGITransport` does not emit lifespan events by default. First-time users wire up a startup handler, test it, see nothing fire, and conclude the test runner is broken. The fix is to opt in explicitly, as noted above. Also, dependency overrides are global state on the `FastAPI` instance; parallel test execution (`pytest-xdist`) multiplies the risk of leaks unless each worker gets its own app instance — which is a bigger refactor than most suites need. ProgImage runs single-process, so the `clear()` call is sufficient.

## Para profundizar

- httpx docs: <https://www.python-httpx.org/>
- `AsyncClient` and `ASGITransport`: <https://www.python-httpx.org/async/>
- FastAPI testing guide: <https://fastapi.tiangolo.com/advanced/async-tests/>
- FastAPI dependency overrides: <https://fastapi.tiangolo.com/advanced/testing-dependencies/>
