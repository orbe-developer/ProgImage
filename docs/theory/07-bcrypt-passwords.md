# 07 — Bcrypt Password Hashing

## ¿Qué es?

Bcrypt is a password-hashing function designed in 1999 by Niels Provos and David Mazières around the Blowfish cipher's key schedule. Three properties distinguish it from a general-purpose cryptographic hash like SHA-256: it is deliberately slow (hundreds of milliseconds, not microseconds), it incorporates a random per-password salt, and the cost of hashing is tunable through a work factor so that the function can keep pace with hardware improvements. The output is a self-describing string of the form `$2b$12$<22-char salt><31-char hash>`, meaning every stored hash carries its own algorithm identifier, cost, and salt — you do not need a separate column for any of them.

## ¿Por qué lo usamos?

ProgImage stores one `hashed_password` field per user and verifies it on every login. The honest reason bcrypt is the right choice here is that fast hashes (MD5, SHA-1, SHA-256) are catastrophic for passwords: an attacker who steals the database can compute billions of candidate hashes per second on a commodity GPU. Bcrypt's slowness and per-password salt mean the same stolen database buys the attacker thousands of guesses per second instead, and no amount of precomputed rainbow table work carries over because each hash is salted. The library is tiny, has no transitive dependencies worth caring about, and the direct API fits our two functions (`hash_password`, `verify_password`) perfectly. The companion to this piece is [`06-jwt-authentication.md`](06-jwt-authentication.md) — bcrypt protects the credential at rest; JWTs transport proof of authentication at runtime.

## ¿Cómo funciona?

### Hashing on registration

See `app/auth/security.py:17`:

```python
def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")
```

- `bcrypt.gensalt()` generates a 16-byte random salt and encodes it with a default work factor of 12 (meaning `2^12 = 4096` key-expansion rounds internally). You can pass `rounds=14` for higher cost at the price of a slower login.
- `bcrypt.hashpw(password_bytes, salt)` runs the derivation. The returned bytes already contain the salt and the cost, so there is nothing to store separately.
- The `.decode("utf-8")` at the end exists so the string fits a `String(255)` column — the raw hash is ASCII either way.

### Verification on login

See `app/auth/security.py:24`:

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
```

`checkpw` extracts the salt and cost from the stored hash, re-derives the hash from the candidate password, and does a constant-time comparison. The constant-time comparison matters: a naïve `==` leaks the length of the matching prefix via timing and is a known attack surface.

### Why direct `bcrypt`, not `passlib`

The common FastAPI tutorials still show `passlib[bcrypt]`. ProgImage uses `bcrypt` directly on purpose. The module docstring at `app/auth/security.py:1` names the reason:

> "Uses `bcrypt` directly rather than passlib to avoid the known compatibility issues between passlib and bcrypt 4.x+."

Concretely: `passlib` 1.7.4 (the current release at the time of this writing) reaches into private `bcrypt` internals (`bcrypt.__about__.__version__`) that were removed in `bcrypt` 4.x. The result is a noisy `AttributeError: module 'bcrypt' has no attribute '__about__'` at import time, often misreported as the auth system being broken. `passlib` is unmaintained enough that the fix has not landed. Direct `bcrypt` has none of this problem, a smaller API, and one fewer dependency.

### Work factor and timing

The default cost of 12 is roughly a 250–400 ms operation on a modern laptop CPU. That number is the whole point: logins are not high-throughput, and the slowness is paid once per login by one user, not per request. If logins start feeling sluggish for legitimate users you lower the cost; if hardware gets faster you raise it. Both can be done per-user because the cost is embedded in the hash, so new logins can be transparently re-hashed with a higher cost on successful verification (ProgImage does not currently do this but it is a two-line change in `verify_password`).

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Argon2 (argon2-cffi)** | Winner of the 2015 Password Hashing Competition. Memory-hard, which makes GPU attacks even harder. The modern default if you are picking today with no constraints. Slightly larger dependency; different parameter tuning (memory, iterations, parallelism). |
| **scrypt** | Also memory-hard. Older than Argon2, less actively studied. Fine, but no clear advantage over Argon2 at this point. |
| **PBKDF2-HMAC-SHA256** | Standard-blessed (FIPS, NIST). Fast on GPUs because it is just repeated SHA — needs very high iteration counts to be competitive. Use when a compliance regime names it specifically. |
| **passlib with bcrypt** | What tutorials show. Adds an abstraction over several algorithms with a unified API. The compat footgun with bcrypt 4.x makes it a liability right now. |
| **Plain SHA-256 / "we salt it ourselves"** | Catastrophically wrong for passwords. Fast hashes exist to protect data integrity, not to resist offline cracking. |

Specific friction: bcrypt silently truncates inputs longer than 72 bytes. That is a historical quirk — long passphrases map to the same hash as their first 72 bytes. The mitigation is to either enforce `max_length` at the Pydantic layer (we do: `password: str = Field(min_length=8, max_length=128)` in `app/auth/schemas.py`) or pre-hash with SHA-256 before passing to bcrypt. Argon2 does not have this limit.

## Para profundizar

- `bcrypt` Python library docs: <https://github.com/pyca/bcrypt>
- Provos & Mazières original paper ("A Future-Adaptable Password Scheme"): <https://www.usenix.org/legacy/event/usenix99/provos/provos_html/>
- OWASP Password Storage Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html>
- Argon2 for comparison: <https://argon2-cffi.readthedocs.io/en/stable/>
