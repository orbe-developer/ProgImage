# 08 — pytest and pytest-asyncio

## ¿Qué es?

pytest is Python's dominant test framework. It replaces `unittest`'s class-based assertions with plain `def test_*` functions, uses the `assert` statement directly (and rewrites it at import time so failure messages show the operands), and introduces a dependency-injection system called *fixtures* that largely obviates per-test setup/teardown boilerplate. pytest-asyncio is a plugin that teaches pytest how to run coroutine tests: it awaits `async def test_*` functions on an event loop supplied by the plugin, and it supports async fixtures that yield awaitable values. Together they are the de facto standard for testing async Python code.

## ¿Por qué lo usamos?

ProgImage is async end-to-end — the routes, the DB session, the HTTP client used in tests, all return coroutines. Testing that code with the stock `unittest` runner means wrapping every call in `asyncio.run(...)` and losing the fixture plumbing. pytest-asyncio removes that friction entirely: a test function marked `async def` is just awaited, and an async fixture decorated with `@pytest_asyncio.fixture` yields its value as if it were sync. The companion to this file is [`09-httpx-asgi-testing.md`](09-httpx-asgi-testing.md), which covers the HTTP client that these fixtures hand to each test.

## ¿Cómo funciona?

### `asyncio_mode = "auto"`

The plugin has two operating modes. The default (`strict`) requires you to decorate every async test with `@pytest.mark.asyncio`. `auto` mode skips the ceremony: every coroutine test and coroutine fixture is treated as async automatically. ProgImage opts into `auto` mode in `pyproject.toml:33`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

`testpaths` restricts collection to `tests/` so pytest does not scan the whole repo (useful once there is a `docs/` or `scripts/` tree in the project).

### Fixtures

A fixture is a function whose return value is injected into any test that names it as a parameter. The decorator variant that gives you an async fixture is `@pytest_asyncio.fixture`. ProgImage uses it to build a fresh database per test at `tests/conftest.py:32`:

```python
@pytest_asyncio.fixture
async def engine():
    """Fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
```

The `yield` splits the fixture into setup (before yield) and teardown (after yield). Because the fixture is async, pytest-asyncio awaits each half on the same event loop as the test that depends on it.

### Fixture scope

By default a fixture runs once per test (`scope="function"`). Larger scopes — `class`, `module`, `session` — reuse the same instance across more tests, which is faster but shares state. ProgImage sticks to function scope deliberately: an in-memory SQLite engine is cheap to create and reusing one across tests would mean each test seeing rows left over from the previous one. The right scope is "the smallest unit over which the state is safe to share"; for a database that is almost always one test.

### Fixture composition

Fixtures can depend on other fixtures by naming them as parameters. See `tests/conftest.py:45`:

```python
@pytest_asyncio.fixture
async def session_factory(engine):
    """Session factory bound to the per-test engine."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)
```

`session_factory` takes `engine` by name, so pytest resolves `engine` first and threads its result in. The same composition chains all the way up to `user_a_token` → `client` → `session_factory` → `engine`.

### `conftest.py` discovery

Fixtures in `conftest.py` are available to every test in the same directory and its subdirectories, with no imports. The project's shared fixtures live in `tests/conftest.py:1` and are automatically visible to any `tests/test_*.py` file. This is pytest's answer to "where do I put shared setup?" — in a conftest, not in a utility module that each test file has to import.

### `parametrize`

Not currently used in ProgImage, but the standard way to run the same test body across several inputs:

```python
@pytest.mark.parametrize("payload", [{"width": -1}, {"width": 10001}])
async def test_rejects_bad_width(payload, client): ...
```

Each parametrisation shows up as its own test id in the output, which is useful when you want granular pass/fail signalling instead of one monster test.

### Markers and skip

`@pytest.mark.skip(reason="...")`, `@pytest.mark.skipif(condition, reason="...")`, and `@pytest.mark.xfail` are the common ways to control execution. Custom markers (`@pytest.mark.slow`) can be registered in `pyproject.toml` under `[tool.pytest.ini_options] markers = ["slow: ..."]` and filtered with `pytest -m "not slow"`.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **`unittest` (stdlib)** | No external dependency. Class-based, verbose, no fixture system — you reinvent it. `IsolatedAsyncioTestCase` handles async but inelegantly. |
| **`nose2`** | Successor to the long-abandoned `nose`. Smaller user base; pytest absorbed most of what nose did better. |
| **`anyio` + pytest-anyio** | Alternative async plugin that works for `asyncio` and `trio`. Right choice if you care about trio; overkill if you are asyncio-only. |
| **`asynctest`** | Older async-testing helpers. Deprecated in favour of what pytest-asyncio and stdlib `IsolatedAsyncioTestCase` now provide. |

Specific friction: pytest-asyncio's event-loop scope is a historical source of pain. Prior to recent versions, mixing fixture scopes with the loop scope could cause "attached to a different loop" errors. The modern defaults in `auto` mode mostly make this invisible, but the moment you introduce a `session`-scoped async fixture you have to pin the loop scope accordingly (`loop_scope="session"`). Also, pytest's assertion rewriting does not reach into C extensions or into code imported before the rewriter installs — rare in practice, confusing when it hits.

## Para profundizar

- pytest docs: <https://docs.pytest.org/en/stable/>
- Fixtures reference: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- pytest-asyncio docs: <https://pytest-asyncio.readthedocs.io/en/latest/>
- Discussion of `asyncio_mode`: <https://pytest-asyncio.readthedocs.io/en/latest/concepts.html#asyncio-modes>
