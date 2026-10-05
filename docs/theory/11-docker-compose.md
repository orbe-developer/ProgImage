# 11 — Docker Compose

## ¿Qué es?

Docker Compose is a tool for defining and running multi-container applications from a single YAML file. Each top-level entry under `services:` describes a container — the image to run (or how to build it), its environment variables, the volumes and networks it attaches to, the ports it exposes, and the healthchecks that determine its readiness. The CLI (`docker compose up`, `docker compose run`, `docker compose logs`) orchestrates the lot: it builds images where needed, creates a user-defined network so services can address each other by name, starts containers in the right dependency order, and tears everything down on `docker compose down`. In recent Docker versions Compose is a plugin invoked as `docker compose` (two words); the standalone `docker-compose` binary is the older v1 implementation.

## ¿Por qué lo usamos?

ProgImage is at minimum two containers — the FastAPI app and a Postgres database — plus a one-shot migration runner. Starting those by hand with three `docker run` incantations, custom networks, and the right environment variable wiring is tedious and easy to get wrong. Compose turns the whole stack into `docker compose up`, which is the lowest-friction way to let a reviewer try the project without reading a setup guide. The Dockerfile itself is covered in [`10-docker.md`](10-docker.md); this file is about how multiple containers come together.

## ¿Cómo funciona?

### Service definitions and shared network

Every service listed under `services:` runs as a container on an auto-created network, reachable from the others by its service name. ProgImage's `db` service is at `docker-compose.yml:2`:

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-progimage}
```

Two things to note: `restart: unless-stopped` has the Docker daemon restart the container if it exits for any reason other than a user-issued stop, and `${DB_USER:-postgres}` is Compose's variable-substitution syntax — the value is read from the host environment (or an adjacent `.env` file) with a default fallback. The `.env` file at the project root is the standard place to park local overrides without committing them.

### Named volumes

The Postgres data directory needs to survive container restarts. ProgImage attaches a named volume at `docker-compose.yml:9`:

```yaml
    volumes:
      - pgdata:/var/lib/postgresql/data
```

The `pgdata` name is declared at the top level (`docker-compose.yml:57`), so Compose manages it and nothing on the host filesystem needs to exist beforehand. Compare this with a bind mount (`./data:/var/lib/postgresql/data`), which maps a host directory straight into the container — fine for source code, risky for a database (permissions, SELinux, Windows path quirks).

### Healthchecks

A service can declare a healthcheck so Compose knows when it is actually ready, not just started. See `docker-compose.yml:11`:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-progimage}"]
      interval: 5s
      timeout: 5s
      retries: 10
```

`pg_isready` is Postgres's own tool for checking whether the server is accepting connections — much more reliable than "the container is running". The result is used by other services via `depends_on`.

### `depends_on: condition: service_healthy`

Without a healthcheck, `depends_on` only waits for the dependency's container to *start*, not to be *ready*. The app service relies on the healthcheck at `docker-compose.yml:33`:

```yaml
    depends_on:
      db:
        condition: service_healthy
```

With that condition, Compose will not launch the `app` container until `db`'s healthcheck has passed. This replaces the ugly `wait-for-it.sh` scripts of the past — the app can assume Postgres is reachable on first connect, so the FastAPI startup never needs to retry.

### Environment passthrough

The app service inherits config via environment variables, which Pydantic Settings then reads. See `docker-compose.yml:24`:

```yaml
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_USER: ${DB_USER:-postgres}
      ...
      JWT_SECRET: ${JWT_SECRET:-dev-secret-change-me-with-a-32-plus-byte-value}
```

`DB_HOST: db` is doing something subtle: `db` is a hostname resolvable on the Compose network, so the app connects to `db:5432` and Compose's embedded DNS routes it to the `db` service. There is no need to expose Postgres on the host for the app to reach it — the ports mapping (`"5432:5432"`) only exists so that psql on the host can connect for debugging.

### Profiles for one-shot work

Not every service should start on `docker compose up`. Compose profiles allow a service to be defined but excluded from the default run. ProgImage uses this for the migration runner at `docker-compose.yml:41`:

```yaml
  migrate:
    build:
      context: .
      dockerfile: Dockerfile
    profiles: ["migrate"]
    ...
    command: ["alembic", "upgrade", "head"]
```

Normal startup (`docker compose up`) ignores the `migrate` service. To run it: `docker compose run --rm migrate`. The `--rm` flag deletes the container after it exits, which is the right shape for a one-shot — the migrations get applied, the container is thrown away, no stopped containers accumulate.

### `command` override

Each service defaults to the image's `CMD`. The `migrate` service overrides it to run Alembic instead of Uvicorn, reusing the same image but with a different entry point. This is cheaper and simpler than building a dedicated migration image, and it guarantees the migration runner has exactly the Python environment the app has.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Kubernetes (minikube, kind, k3d)** | Production-grade orchestration, declarative, scalable. Massively more machinery than a two-container project needs. |
| **Docker Swarm** | Docker's native cluster mode. Simpler than K8s. Effectively unmaintained relative to K8s and Compose. |
| **Nomad + Consul** | HashiCorp's take. Clean separation of concerns. Overkill for one-machine development. |
| **systemd units on the host** | Zero containers, zero orchestration. You own every library version yourself and lose reproducibility. |
| **Tilt / Skaffold** | Dev-focused orchestrators that handle rebuild-on-change. Nice for larger projects; unnecessary when `docker compose up --build` is already fast enough. |

Specific friction: the YAML schema has changed several times (versions 1, 2, 3, and now the "Compose Spec"). Old `version: "3.8"` headers are harmless but unnecessary; recent Compose simply ignores them. Also, `depends_on` with healthchecks works for *startup* ordering but has no story for runtime failure — if the DB dies mid-session, the app is not restarted. That is a job for a real supervisor, not Compose.

## Para profundizar

- Compose file reference: <https://docs.docker.com/compose/compose-file/>
- `depends_on` with healthchecks: <https://docs.docker.com/compose/how-tos/startup-order/>
- Compose profiles: <https://docs.docker.com/compose/how-tos/profiles/>
- Environment variables in Compose: <https://docs.docker.com/compose/how-tos/environment-variables/>
