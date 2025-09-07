import os
from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


def make_celery():
    broker = CELERY_BROKER_URL
    backend = CELERY_RESULT_BACKEND

    celery = Celery(
        "bow",
        broker=broker,
        backend=backend,
        include=["app.utils.file_util", "app.utils.notification_util"],
    )

    celery.conf.update(
        task_default_queue="default",
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone=os.getenv("CELERY_TIMEZONE", "Asia/Kolkata"),
        enable_utc=False,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_time_limit=1800,
        task_soft_time_limit=1200,
        result_expires=86400,
        broker_transport_options={"visibility_timeout": 3600},
        task_default_retry_delay=15,
        broker_connection_retry_on_startup=True,
    )
    return celery


celery_app = make_celery()
