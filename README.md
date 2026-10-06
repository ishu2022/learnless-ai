# LearnLess AI

**Learn More. Watch Less.**

LearnLess AI turns long YouTube videos, playlists and PDFs into summaries, notes,
flashcards and quizzes, and lets students ask questions answered from their own material (RAG).

> **Status: Phase 1 - Foundation.** The infrastructure, backend skeleton and frontend skeleton run
> end to end. Authentication and AI features arrive in later phases (see [Roadmap](#roadmap)).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui setup, TanStack Query |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic |
| Database | PostgreSQL 16 + pgvector |
| Background jobs | Celery + Redis |
| File storage | MinIO (S3-compatible) |
| Dev environment | Docker Compose |

```
Browser --> Next.js (3000) --> FastAPI (8000) --+--> PostgreSQL + pgvector
                                                +--> Redis <--> Celery worker
                                                +--> MinIO (S3 storage)
```

## Quick start (new developer)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (on Windows, with the WSL2 backend) and Git.
You do **not** need to install PostgreSQL, Redis, Python or Node locally.

```bash
git clone <repository-url>
cd learnless-ai

# 1. Create your local config, then open .env and change the two CHANGE ME passwords
cp .env.example .env          # Windows cmd: copy .env.example .env

# 2. Build and start everything
docker compose up --build
```

First start downloads images and installs dependencies, so allow a few minutes.

## Verify it works

| What | URL | Expected |
|---|---|---|
| Frontend status page | http://localhost:3000 | Backend, PostgreSQL + pgvector, Redis and MinIO all show **Connected** |
| API liveness | http://localhost:8000/api/v1/health | `{"status":"ok", ...}` |
| API readiness | http://localhost:8000/api/v1/health/ready | `"status":"ok"` with `database`, `redis`, `storage` components |
| API docs (Swagger) | http://localhost:8000/docs | Interactive docs |
| MinIO console | http://localhost:9001 | Log in with `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |

Run the backend tests:

```bash
docker compose exec backend pytest
```

Stop everything: `docker compose down` (add `-v` to also delete all stored data).

## Project structure

```
learnless-ai/
  backend/            FastAPI app (app/api, core, db, models, schemas, repositories,
                      services, integrations, rag, workers, utils), alembic/, tests/
  frontend/           Next.js app (app, components, hooks, lib, types)
  infra/postgres/     DB init scripts (enables pgvector)
  docs/               Development docs
  .github/            Pull request template
  docker-compose.yml  Whole dev environment
  .env.example        Configuration template (copy to .env)
```

## Roadmap

1. **Foundation** (this phase)
2. Authentication
3. Courses & resources
4. Content processing
5. AI summarization
6. RAG & AI chat
7. Flashcards & quizzes
8. Progress & analytics
9. UI/UX polish
10. Testing & deployment

## More documentation

- [Development guide and troubleshooting](docs/DEVELOPMENT.md)
- [Contributing / Git workflow](CONTRIBUTING.md)
