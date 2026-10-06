# Contributing

## Branches

- `main` - stable, always runnable. **Never push directly.**
- `develop` - integration branch; feature branches merge here.
- `feature/<short-name>` - one branch per task, e.g. `feature/auth-login`.

## Workflow

1. `git checkout develop && git pull`
2. `git checkout -b feature/<short-name>`
3. Make changes, run `docker compose up --build` and the tests.
4. `git add -p && git commit -m "feat: short description"`
5. `git push -u origin feature/<short-name>`
6. Open a pull request into `develop`, request a review, address comments, then merge.

## Rules

- Never commit `.env` or any secret. Add new variables to `.env.example`.
- Database changes need an Alembic migration (see `docs/DEVELOPMENT.md`).
- Keep pull requests small and focused on one thing.

A full GitHub setup guide (collaborators, branch protection, conflict resolution) will be added in `docs/GITHUB_SETUP.md`.
