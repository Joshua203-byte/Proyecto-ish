"""
Celery application configuration for the GPU worker.
"""
from celery import Celery
from .config import settings

import ssl

# Configure SSL for Heroku Redis (rediss://)
redis_url = settings.REDIS_URL
broker_use_ssl = None
backend_use_ssl = None

if redis_url.startswith("rediss://"):
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

celery_app = Celery(
    "home-gpu-cloud-worker",
    broker=redis_url,
    backend=redis_url,
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=backend_use_ssl,
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
from .tasks import gpu_tasks  # noqa: F401, E402
