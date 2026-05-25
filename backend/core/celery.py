import os
import sys

# Garante que `/app` (raiz dos packages) esteja no sys.path quando o worker
# é iniciado pelo entry-script /usr/local/bin/celery — caso contrário, tasks
# que importam packages top-level (crud/, services/, api/) falham com
# ModuleNotFoundError. O FastAPI/uvicorn não tem esse problema porque é
# iniciado com `uvicorn main:app` a partir de /app.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from celery import Celery
from core.config import settings

app = Celery(
    "playwave",
    broker=settings.CELERY_BROKER_URL or settings.RABBITMQ_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    include=["tasks", "tasks.media.backfill_has_audio"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_ignore_result=True,
    task_store_errors_even_if_ignored=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=500,
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "mark-offline-devices-every-2m": {
            "task": "tasks.mark_offline_devices",
            "schedule": 120.0,
        },
        "daily-device-stats-midnight": {
            "task": "tasks.daily_device_stats",
            "schedule": 86400.0,
        },
        # SPEC 003 — expira comandos abandonados (sem ACK do player).
        "expire-stale-commands-every-60s": {
            "task": "tasks.expire_stale_commands",
            "schedule": 60.0,
        },
    },
)
