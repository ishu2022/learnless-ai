-- Runs once, the first time the Postgres data volume is created.
-- Alembic's baseline migration also enables it (idempotent) so both paths are safe.
CREATE EXTENSION IF NOT EXISTS vector;
