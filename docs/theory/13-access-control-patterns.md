# 13 — Access Control Patterns

## ¿Qué es?

Access control is the set of mechanisms that decide, for a given request, whether the caller is who they claim to be and whether they are allowed to do what they are asking to do. The two halves have different names and different failure modes: *authentication* (AuthN) answers "who is this?", and *authorisation* (AuthZ) answers "may they do this?". A system can have perfect authentication and no authorisation (every logged-in user can see every row), or vice versa (correct ownership checks against an anonymous caller). ProgImage needs both: JWTs establish identity (see [`06-jwt-authentication.md`](06-jwt-authentication.md)), and ownership filters at the SQL layer establish permission.

## ¿Por qué lo usamos?

ProgImage is a multi-tenant image store — every user uploads their own images, and no user should ever see another user's data. The authentication layer alone cannot provide this; a valid token merely says "I am user 42", not "user 42 is allowed to see image 17". Ownership enforcement has to live somewhere, and the pattern used throughout the images router is to make it part of the query itself: every read filters on `owner_id == current_user.id`, so a request from the wrong user cannot possibly return the row. The additional subtlety — returning 404 instead of 403 for someone else's images — is a deliberate information-disclosure choice explained below.

## ¿Cómo funciona?

### Owner-scoped reads at the SQL layer

The whole pattern lives in one query. See `app/routers/images.py:65`:

```python
result = await session.execute(
    select(Image).where(
        Image.id == image_id,
        Image.owner_id == current_user.id,
    )
)
image = result.scalar_one_or_none()
if image is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Image {image_id} not found",
    )
return Response(content=image.data, media_type=image.content_type)
```

Two things are happening simultaneously:

- The `WHERE` clause fuses the identity lookup (`Image.id == image_id`) and the ownership check (`Image.owner_id == current_user.id`) into one query. The database cannot return a row that does not satisfy both.
- `scalar_one_or_none()` collapses "not found" and "owned by someone else" into the same result (`None`). The endpoint cannot accidentally leak either state because it only sees whether a row came back.

This is deliberately different from the pattern of fetching the row and then checking ownership in Python:

```python
# Anti-pattern
image = await session.get(Image, image_id)
if image is None:
    raise HTTPException(404, ...)
if image.owner_id != current_user.id:
    raise HTTPException(403, ...)
return image
```

That version works but has three flaws: it hits the DB with less selective SQL (missing the composite filter prevents some index strategies), it adds a code path that can be forgotten on the next endpoint, and it distinguishes 404 from 403 in a way that leaks information (see next section).

### Why 404 and not 403 for someone else's resource

When a user asks for an image they do not own, the semantically "correct" status code is 403 Forbidden — the server understood the request and refuses to authorise it. The problem is enumeration: a 403 response tells the attacker that `image_id` exists and belongs to someone else, which is information they could not otherwise obtain. A 404 response is indistinguishable between "no such id" and "exists but not yours", so an attacker scanning the id space learns nothing beyond what they already knew.

ProgImage documents this choice in-line at `app/routers/images.py:60`:

```python
"""Return the raw bytes of an image owned by the current user.

Access control: images owned by other users are reported as 404
(not 403) so the API does not leak which image ids exist.
"""
```

The trade-off: if two users ever collaborate and one asks the other "why do I get 404 for image 17?", the answer "because it is not yours" is not available from the API itself. For a system where resources are strictly single-owner this is fine. Where resources are shared, 403 becomes the right answer again.

### Where auth is enforced

Each protected route takes `current_user: User = Depends(get_current_user)` — see `app/routers/images.py:30` for the upload path and `app/routers/images.py:58` for the read path. The dependency raises 401 if the token is missing, invalid, expired, or references a deactivated user. By the time the route body runs, `current_user` is guaranteed to be a loaded `User` row, and `current_user.id` can be used in the ownership filter without further checks.

### Write-side ownership

Uploads attach the current user as the owner at `app/routers/images.py:38`:

```python
image = Image(
    content_type=file.content_type,
    data=data,
    description=file.filename,
    owner_id=current_user.id,
)
```

There is no field in the request body for `owner_id`. Even if a client tried to send one, the Pydantic schema (`UploadFile` for the file plus the multipart form) does not accept it. This is the mirror of the read-side pattern: ownership is set from the authenticated identity, never from client input. Attempts to upload "as" another user are impossible by construction, not by validation.

### FK + cascade as a backstop

The foreign key at `app/models/image.py:33` declares `ForeignKey("users.id", ondelete="CASCADE")`. If a user is deleted, their images are deleted by the database — enforced in SQL regardless of how the user row went away. This is defence in depth: the ORM-level `cascade="all, delete-orphan"` on the relationship (`app/models/user.py:34`) handles the ORM path, and the FK handles the raw-SQL path. Neither on its own is enough; together they are.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Row-Level Security (RLS) in Postgres** | Policies live in the database; every tenant sees only their rows regardless of the application. Requires passing a session variable per connection (`SET LOCAL app.user_id = ...`). Powerful; adds complexity to connection management. |
| **Casbin / oso / policy engines** | Expressive rule languages (RBAC, ABAC, ReBAC). Shine when permission logic becomes rich (roles, groups, shared resources). Over-engineered when every rule is "owner only". |
| **Pre-fetch then check in Python** | What most tutorials show. Works for small apps; invites 404/403 leaks and makes the ownership check easy to forget. |
| **403 everywhere for authorisation failures** | Semantically correct per HTTP; leaks resource existence. Right choice for admin dashboards where IDs are not sensitive. |
| **Separate microservice for authorisation** | Centralised policy. Adds a network hop and a new dependency; worth it only at scale. |

Specific friction: the owner-scoped-query pattern is simple but easy to forget on a new endpoint. The moment one route fetches an `Image` without the `owner_id` filter, the invariant is broken. The way to make this harder to get wrong is to centralise the filter — e.g., a `get_owned_image(image_id, user)` helper, or SQLAlchemy query filters applied globally. ProgImage is small enough that the explicit filter at each call site is readable; a larger codebase would move it.

## Para profundizar

- OWASP Access Control Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html>
- OWASP API Security Top 10 — "Broken Object Level Authorization" (BOLA): <https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/>
- Postgres Row-Level Security: <https://www.postgresql.org/docs/current/ddl-rowsecurity.html>
- FastAPI security docs: <https://fastapi.tiangolo.com/tutorial/security/>
