# ProgImage — Postman

Interactive API client collection for exercising every ProgImage endpoint without writing curl commands.

## Files

| File | Purpose |
|------|---------|
| `ProgImage.postman_collection.json` | 24 endpoints organised in 5 folders (Auth, Images, Processing, Filtering, Masking). Collection-level Bearer auth via `{{token}}`; Register and Login override to anonymous. |
| `ProgImage.postman_environment.json` | Default values for `baseUrl`, `token`, `email`, `password`, `imageId`. The same keys exist as collection variables, so this file is optional. |

## Import

In Postman: **File → Import →** drop both JSON files, or **Workspace → Import → Upload Files**.

## Typical flow

1. **Make sure the app is running.** Either:
   - `docker compose up --build` from the project root, or
   - `uv run uvicorn app.main:app --reload`
2. **Auth → Register** — creates the user described by `{{email}}` and `{{password}}`.
3. **Auth → Login** — on success the Tests tab stores the returned `access_token` into the collection variable `token`. You will see "Token saved to collection variable." in the Postman console.
4. **Auth → Me** — proves the token works.
5. **Images → Upload Image** — attach any JPEG/PNG under the `file` form-data field. On success the Tests tab also saves the returned `id` into `imageId`.
6. **Images → Get Image By Id** — retrieves the image you just uploaded. Change `imageId` to an id owned by a different user to see the 404 (access control).
7. **Processing / Filtering / Masking** — try `width=-5` on Compress to see Pydantic's 422 validation error; send only one file to Mask to see the 400 arity check.

## Variables

| Variable | Where set | Notes |
|----------|-----------|-------|
| `baseUrl` | collection + env | Defaults to `http://localhost:8000/api/v1`. Point this at your Docker host to run against a container. |
| `token` | populated by Login | Collection variable (not environment). Clear it manually to simulate a logged-out client. |
| `email` / `password` | env + collection | Used by Register and Login bodies. Change before importing to use your own credentials. |
| `imageId` | populated by Upload | Used by Get Image By Id. |

## Notes

- All requests under the Images / Processing / Filtering / Masking folders inherit the collection-level Bearer auth. If you add new requests, do not override the auth unless the endpoint should be anonymous.
- The Postman v2.1 schema is used so the file imports cleanly into any current Postman / Insomnia / Bruno client.
- Postman does not populate the `src` of file inputs for security reasons — you have to pick the actual file in the Postman GUI for Upload and masking endpoints.
