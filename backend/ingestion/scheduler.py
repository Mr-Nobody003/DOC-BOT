"""Scheduling hooks for recurring ingestion (Kubernetes CronJob, etc.)."""


def default_schedules() -> list[dict]:
    """Describe recommended schedules for operators; not executed here."""
    return [
        {"name": "pubmed_delta", "cron": "0 3 * * *", "queue": "ingest_pubmed_query"},
    ]
