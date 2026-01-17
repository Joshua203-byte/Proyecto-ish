"""
Celery application configuration for the backend.
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "home-gpu-cloud",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "worker.tasks.gpu_tasks.*": {"queue": "gpu_jobs"},
    },
    beat_schedule={
        # Periodic tasks can be added here
    },
)
