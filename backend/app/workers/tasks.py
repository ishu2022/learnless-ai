from app.workers.celery_app import celery_app


@celery_app.task(name="system.ping")
def ping() -> str:
    """Trivial task proving the worker <-> Redis wiring works."""
    return "pong"
