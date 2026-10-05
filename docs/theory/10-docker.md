# 10 — Docker

## ¿Qué es?

Docker is a tool for packaging an application and all of its runtime dependencies into a single immutable artefact — an image — that runs the same on any host with a container runtime. An image is built by executing a `Dockerfile`, which is a sequence of declarative instructions (`FROM`, `COPY`, `RUN`, `ENV`, `CMD`, …) that each produce a layer. Layers are cached and content-addressed, so unchanged instructions are reused on subsequent builds. A container is a running instance of an image with its own filesystem, process namespace, and network interface, isolated from the host by Linux kernel primitives (namespaces, cgroups). The whole thing exists to make "it works on my machine" either universally true or universally false — never partially true.

## ¿Por qué lo usamos?

ProgImage has to run against a real Postgres and bring up cleanly on any laptop or CI runner without a wiki page of setup steps. A `Dockerfile` plus a `docker-compose.yml` (covered in [`11-docker-compose.md`](11-docker-compose.md)) collapses that onboarding to a single `docker compose up`. On top of reproducibility, the image is also the deployment artefact — the same bytes that pass CI are what runs in production — which eliminates an entire class of "it worked in staging" bugs. For a portfolio project, having a working Docker setup is also an unmissable signal that the author knows how production deployments are shaped.

## ¿Cómo funciona?

### Multi-stage build

ProgImage uses a two-stage build to keep the runtime image slim. The builder stage installs toolchains, compiles native dependencies, and resolves the Python environment; the runtime stage copies only the finished venv and the app code. See `Dockerfile:4`:

```dockerfile
# Builder stage: install dependencies with uv into a project-local venv
FROM python:3.12-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
```

`build-essential` plus the `-dev` headers for libjpeg and zlib are needed because Pillow compiles native extensions during install. These are large packages and we do not want them in the final image.

### Cache-friendly ordering

Image layer caching is purely content-based: if a layer's inputs are unchanged, Docker reuses the cached result. The practical consequence is that you want files that change rarely (lockfiles) copied before files that change often (source code). ProgImage does this at `Dockerfile:23`:

```dockerfile
# Install only runtime dependencies first for cacheable layer
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy the application code and install the project itself
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev
```

Editing a route no longer invalidates the dependency-install layer. Only when `pyproject.toml` or `uv.lock` changes does the slow `uv sync` run again.

### Runtime stage

See `Dockerfile:34`:

```dockerfile
FROM python:3.12-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home /app app
```

Only the runtime libraries (`libjpeg62-turbo`, `zlib1g`) are installed here — no `-dev` headers, no `build-essential`. The user `app` is a system account with no login shell; it is who the container will run as.

### Non-root user

Running as root inside a container is a long-standing bad habit — a container escape or a vulnerable binary immediately gets root on the container filesystem, which is a much larger blast radius than a non-privileged account. ProgImage copies the venv over with the right ownership and switches to the unprivileged user at `Dockerfile:48`:

```dockerfile
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000
```

`COPY --from=builder` is the multi-stage glue — the finished `/app` tree is copied out of the builder image, and nothing else from the builder (not the compilers, not the apt cache) is in the final image.

### `HEALTHCHECK`

See `Dockerfile:54`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1
```

The container runtime periodically runs this command inside the container and marks the container healthy / unhealthy based on the exit code. Compose uses the result for `depends_on: service_healthy` wiring; Kubernetes has its own analogue (`livenessProbe`). The one-liner `urllib.request.urlopen('/docs')` is deliberately minimal — no shell, no curl install, just the stdlib.

### `CMD`

See `Dockerfile:57`:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Exec form (JSON array), not shell form — so Uvicorn becomes PID 1 and receives signals directly. `--host 0.0.0.0` is required for the socket to accept connections from outside the container.

### Image size trade-offs

`python:3.12-slim` is roughly 50 MB vs ~1 GB for the full `python:3.12`. Alpine images (`python:3.12-alpine`) are even smaller but use `musl` instead of `glibc`, which breaks wheels for many C-extension packages (Pillow included) and forces fallback source builds. Slim is the usual middle ground: Debian base, Python preinstalled, minimal extras.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Single-stage image** | Simpler Dockerfile. Final image carries the toolchain — hundreds of MB larger and a bigger attack surface. |
| **Alpine base** | Smallest images. Breaks binary wheels (`musl` vs `glibc`), source builds take longer, occasional runtime quirks. |
| **Distroless (`gcr.io/distroless/python3`)** | No shell, no package manager, tiny attack surface. Debugging a crashed container is painful without `sh`. |
| **Buildah / Podman / Kaniko** | Daemonless or rootless build alternatives. Mostly compatible with Dockerfiles. Pick when a corporate environment forbids the Docker daemon. |
| **`pip install` straight on the host** | Zero container machinery. Loses reproducibility, loses the "same artefact in prod" guarantee, requires every environment to agree on native libs. |

Specific friction: layer caching gives you reproducibility *within* a build but not *between* builds on different machines unless you pin everything, including base image digests (`FROM python:3.12-slim@sha256:...`). Also, Pillow's native dependencies are a recurring papercut — forget one of libjpeg/zlib/libtiff/libwebp and the image builds fine but blows up at runtime on an unexpected format.

## Para profundizar

- Dockerfile reference: <https://docs.docker.com/reference/dockerfile/>
- Multi-stage builds: <https://docs.docker.com/build/building/multi-stage/>
- Build cache best practices: <https://docs.docker.com/build/cache/>
- `HEALTHCHECK` reference: <https://docs.docker.com/reference/dockerfile/#healthcheck>
