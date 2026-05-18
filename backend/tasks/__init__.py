from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

OFFLINE_THRESHOLD_MINUTES = 5


@shared_task(name="tasks.daily_device_stats")
def daily_device_stats():
    """Pre-compute daily playback view counts per device and log them."""
    from core.database import SessionLocal
    from core.models import Device, PlaybackLog
    from sqlalchemy import func

    db = SessionLocal()
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        rows = (
            db.query(PlaybackLog.device_id, func.count(PlaybackLog.id).label("views"))
            .filter(PlaybackLog.created_at >= today_start)
            .group_by(PlaybackLog.device_id)
            .all()
        )
        result = {str(r.device_id): r.views for r in rows}
        logger.info("daily_device_stats: %d devices with views today", len(result))
        return result
    except Exception as exc:
        logger.error("daily_device_stats failed: %s", exc)
        raise
    finally:
        db.close()


@shared_task(name="tasks.mark_offline_devices")
def mark_offline_devices():
    """Mark devices as offline when last_seen_at exceeds the threshold."""
    from core.database import SessionLocal
    from core.models import Device

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=OFFLINE_THRESHOLD_MINUTES)
        stale = (
            db.query(Device)
            .filter(
                Device.status == "online",
                Device.last_seen_at < cutoff,
            )
            .all()
        )
        count = 0
        for device in stale:
            device.status = "offline"
            count += 1
        if count:
            db.commit()
            logger.info("Marked %d device(s) as offline (threshold: %d min)", count, OFFLINE_THRESHOLD_MINUTES)
        return {"marked_offline": count}
    except Exception as exc:
        db.rollback()
        logger.error("mark_offline_devices failed: %s", exc)
        raise
    finally:
        db.close()
