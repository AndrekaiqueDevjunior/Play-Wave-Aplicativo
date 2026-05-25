from datetime import datetime, timedelta
import json

try:
    from celery import shared_task
    from celery.utils.log import get_task_logger
except ModuleNotFoundError:
    def shared_task(*_args, **_kwargs):
        def decorator(func):
            return func
        return decorator

    def get_task_logger(_name):
        import logging

        return logging.getLogger(_name)

logger = get_task_logger(__name__)

OFFLINE_THRESHOLD_MINUTES = 5

@shared_task(name="tasks.recalculate_device_playlists")
def recalculate_device_playlists():
    """Invalidate only stale device playlist caches.

    This task is intentionally not scheduled every few seconds anymore. Playlist
    caches are event-invalidated by API writes and have a short TTL; this task is
    a maintenance fallback for manual runs or future low-frequency schedules.
    """
    from core.database import SessionLocal
    from core.models import Device
    from core.models import Campaign
    from core.config import get_redis_client
    from sqlalchemy import and_, cast
    from sqlalchemy.dialects.postgresql import JSONB
    from datetime import datetime

    db = SessionLocal()
    redis_client = get_redis_client()
    try:
        devices = db.query(Device).filter(Device.is_active == True).all()
        processed_count = 0
        invalidated_count = 0
        
        for device in devices:
            # Get current campaign based on time-based scheduling
            campaign = None
            if device.current_campaign_id:
                campaign = db.query(Campaign).filter(Campaign.id == device.current_campaign_id).first()
            
            if not campaign:
                # Find active campaign targeting this device
                campaign = (
                    db.query(Campaign)
                    .filter(
                        and_(
                            cast(Campaign.device_ids, JSONB).contains([str(device.id)]),
                            Campaign.status == "active",
                        )
                    )
                    .order_by(Campaign.priority.desc())
                    .first()
                )
            
            # Get current campaign version
            current_campaign_id = str(campaign.id) if campaign else None
            current_config_version = campaign.config_version if campaign else None
            
            cache_key = f"device_playlist:{device.id}"
            if redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        payload = json.loads(cached)
                        cached_campaign = payload.get("campaign") if isinstance(payload, dict) else None
                        cached_version = (
                            cached_campaign.get("config_version")
                            if isinstance(cached_campaign, dict)
                            else None
                        )
                        if cached_version != current_config_version:
                            redis_client.delete(cache_key)
                            invalidated_count += 1
                except Exception as e:
                    logger.error("Failed to inspect cache for device %s: %s", device.id, e)
            
            processed_count += 1
        
        logger.info(
            "recalculate_device_playlists: processed=%d invalidated=%d",
            processed_count,
            invalidated_count,
        )
        return {"processed": processed_count, "invalidated": invalidated_count}
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


@shared_task(name="tasks.expire_stale_commands")
def expire_stale_commands():
    """Marca como EXPIRED comandos cujo expires_at ja passou.

    SPEC 003. Roda a cada 60s via beat. O endpoint /commands/pending tambem faz
    housekeeping local por device, mas esta task garante limpeza mesmo quando
    o player esta offline.
    """
    # Fork pool não herda sys.path do main — garante /app no path antes do import.
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)

    from core.database import SessionLocal
    from crud.entidades.crud_device_command import crud_device_command

    db = SessionLocal()
    try:
        count = crud_device_command.mark_expired_batch(db)
        if count:
            logger.info("expire_stale_commands: expired=%d", count)
        return {"expired": count}
    except Exception as exc:
        db.rollback()
        logger.error("expire_stale_commands failed: %s", exc)
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
