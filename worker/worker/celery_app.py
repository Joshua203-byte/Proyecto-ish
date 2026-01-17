"""
Celery application configuration for the GPU worker.
"""
from celery import Celery
from worker.config import settings

celery_app = Celery(
    "home-gpu-cloud-worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Only process one task at a time (GPU is exclusive resource)
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    # Task routing
    task_default_queue="gpu_jobs",
    # Task acknowledgement
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Import tasks to register them
from worker.tasks import gpu_tasks  # noqa: F401, E402
