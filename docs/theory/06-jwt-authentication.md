# 06 — JWT Authentication

## ¿Qué es?

A JSON Web Token (JWT, RFC 7519) is a compact, URL-safe way of representing claims between two parties. The token is a single string of three Base64URL-encoded parts separated by dots: `header.payload.signature`. The header names the signing algorithm, the payload is a JSON object of claims (who the token is about, when it expires, who issued it, anything else you want), and the signature is produced by signing the first two parts with a secret (symmetric algorithms like HS256) or a private key (asymmetric algorithms like RS256). Any party in possession of the secret or the matching public key can verify the token without needing to call back to the issuer — that stateless property is what makes JWTs attractive for API authentication.

## ¿Por qué lo usamos?

ProgImage is a stateless HTTP service with no session store. Every request has to carry its own proof of identity because there is no server-side table of logged-in users to look up. JWTs fit that shape precisely: the login endpoint returns a signed token, the client includes it as `Authorization: Bearer <token>` on every subsequent request, and each protected endpoint verifies the signature and expiry locally. There is no cache to invalidate, no sticky session to pin, and horizontally scaling the app is just "add another container". The counterweight is that genuine revocation before expiry is awkward (see trade-offs below) — short expiry windows and bcrypt-hashed credentials (see [`07-bcrypt-passwords.md`](07-bcrypt-passwords.md)) are the mitigation.

## ¿Cómo funciona?

### Issuing a token

The login endpoint verifies the password then calls `create_access_token`. See `app/auth/security.py:32`:

```python
def create_access_token(
    subject: int,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, object] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
```

Two claims are set:

- `sub` ("subject") — the user id, stringified because RFC 7519 defines `sub` as a string.
- `exp` ("expiration time") — a Unix timestamp after which the token is invalid. PyJWT auto-rejects expired tokens on decode.

The library accepts a `datetime` for `exp` and serialises it as a Unix epoch integer. `iat` (issued-at) is not set here — it is useful for audit trails but PyJWT does not require it.

### Verifying a token

Decoding runs in `app/auth/security.py:44`:

```python
def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    sub = payload.get("sub")
    if sub is None:
        raise jwt.InvalidTokenError("Token payload missing subject")
    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Token subject is not an integer") from exc
```

The `algorithms=[...]` kwarg is not cosmetic — explicitly listing allowed algorithms is what blocks the historical "`alg: none`" attack and the "RS256-key-interpreted-as-HS256-secret" confusion attack. PyJWT refuses to decode a token whose header advertises an algorithm not in that list.

Any failure — bad signature, expired token, missing or non-integer `sub` — raises a subclass of `jwt.InvalidTokenError`, which the dependency catches uniformly.

### OAuth2 Bearer flow in FastAPI

FastAPI ships an `OAuth2PasswordBearer` helper that both declares the auth scheme in OpenAPI (so the Swagger UI gets an "Authorize" button) and extracts the Bearer token from each request. See `app/auth/dependencies.py:13`:

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
```

The `tokenUrl` is a documentation hint pointing clients at the endpoint that issues tokens; it does not perform any routing itself.

The dependency that resolves a token to a user is at `app/auth/dependencies.py:16`:

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise credentials_exception

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user
```

Every protected route takes `current_user: User = Depends(get_current_user)` and receives a loaded `User` row. The DB lookup after decoding is deliberate: it catches tokens that are cryptographically valid but reference a user who has since been deleted or deactivated.

### The login endpoint

Password check and token issuance at `app/auth/router.py:57` use `OAuth2PasswordRequestForm`, which parses `username` and `password` from a `application/x-www-form-urlencoded` body — the OAuth2 password-grant shape, which is also what the Swagger UI's "Authorize" dialog sends.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Server-side sessions (cookie + session store)** | Easy revocation (delete the row), good for browser apps with CSRF protection. Requires a session store (Redis / DB) and sticky routing or shared state. |
| **Opaque bearer tokens (random strings in a DB)** | Simple to revoke; requires a DB lookup on every request. Fine when you are already paying for a cache. |
| **PASETO (Platform-Agnostic Security Tokens)** | Fixes JWT's algorithm-confusion footguns by baking the algorithm into the token version. Smaller ecosystem; fewer libraries. |
| **mTLS / client certificates** | Strong, stateless, mutual auth. Painful UX for human users; mostly used service-to-service. |
| **OIDC with an external provider** | Delegates the auth problem (Auth0, Cognito, Keycloak). Pulls in a dependency and a bill, but gets you refresh tokens, MFA, and social login for free. |

Specific friction: revocation. A JWT is valid until its `exp` passes — if a laptop is stolen you cannot "log out" that token server-side without either a revocation list (adds state) or rotating the signing key (invalidates everyone). HS256 symmetric signing is simplest but means every service that verifies tokens needs the secret; RS256 lets you distribute only a public key but adds key-management overhead. For ProgImage, HS256 inside one container is the right call; the moment there are two services verifying tokens, RS256 becomes attractive.

## Para profundizar

- RFC 7519 (JWT): <https://datatracker.ietf.org/doc/html/rfc7519>
- PyJWT docs: <https://pyjwt.readthedocs.io/en/stable/>
- FastAPI OAuth2 tutorial: <https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/>
- "JWT: the right questions to ask" — common pitfalls: <https://pragmaticwebsecurity.com/articles/apisecurity/how-to-prevent-jwt-vulnerabilities.html>
