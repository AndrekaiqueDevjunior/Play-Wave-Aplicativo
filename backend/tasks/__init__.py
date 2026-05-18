from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

OFFLINE_THRESHOLD_MINUTES = 5


@shared_task(name="tasks.recalculate_device_playlists")
def recalculate_device_playlists():
    """Recalculate playlists for all devices based on time-based campaign scheduling and invalidate Redis cache."""
    from core.database import SessionLocal
    from core.models import Device
    from crud.entidades.crud_campaign import crud_campaign
    from core.config import get_redis_client

    db = SessionLocal()
    redis_client = get_redis_client()
    try:
        devices = db.query(Device).filter(Device.is_active == True).all()
        updated_count = 0
        
        for device in devices:
            # Get current campaign based on time-based scheduling
            campaign = None
            if device.current_campaign_id:
                from core.models import Campaign
                campaign = db.query(Campaign).filter(Campaign.id == device.current_campaign_id).first()
            
            if not campaign:
                campaign = crud_campaign.get_active_for_device(db, device_id=str(device.id))
            
            # Get current campaign version
            current_campaign_id = str(campaign.id) if campaign else None
            current_config_version = campaign.config_version if campaign else None
            
            # Invalidate Redis cache for this device
            cache_key = f"device_playlist:{device.id}"
            if redis_client:
                try:
                    redis_client.delete(cache_key)
                    logger.info("Invalidated cache for device %s", device.id)
                except Exception as e:
                    logger.error("Failed to invalidate cache for device %s: %s", device.id, e)
            
            logger.info(
                "Device %s: campaign=%s, config_version=%s",
                device.id,
                current_campaign_id,
                current_config_version
            )
            updated_count += 1
        
        logger.info("recalculate_device_playlists: processed %d devices", updated_count)
        return {"processed": updated_count}
    except Exception as exc:
        logger.error("recalculate_device_playlists failed: %s", exc)
        raise
    finally:
        db.close()


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
