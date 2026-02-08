"""
Celery application configuration for the backend.
"""
from celery import Celery
from app.config import settings
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
    "home-gpu-cloud",
    broker=redis_url,
    backend=redis_url,
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=backend_use_ssl,
    include=["app.tasks.gpu_tasks"]
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
