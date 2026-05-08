from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioTrack, Campaign, Device, DeviceEvent, Media, PlaybackLog, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_filter = current_user.role != "admin"
    tid = str(current_user.tenant_id) if tenant_filter else None

    def tq(model):
        q = db.query(model)
        if tid:
            q = q.filter(model.tenant_id == tid)
        return q

    total_devices   = tq(Device).count()
    online_devices  = tq(Device).filter(Device.status == "online").count()
    offline_devices = tq(Device).filter(Device.status == "offline").count()

    total_campaigns  = tq(Campaign).count()
    active_campaigns = tq(Campaign).filter(Campaign.status == "active").count()

    total_media = tq(Media).count()

    total_audio = tq(AudioTrack).count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_playbacks_q = db.query(PlaybackLog).filter(PlaybackLog.created_at >= today_start)
    if tid:
        today_playbacks_q = today_playbacks_q.filter(PlaybackLog.tenant_id == tid)

    # Playback stats last 7 days
    cutoff = datetime.utcnow() - timedelta(days=7)
    pb_q = db.query(PlaybackLog).filter(PlaybackLog.created_at >= cutoff)
    if tid:
        pb_q = pb_q.filter(PlaybackLog.tenant_id == tid)
    playbacks_7d = pb_q.count()
    total_views_7d = pb_q.with_entities(
        func.sum(PlaybackLog.duration_ms)
    ).scalar() or 0

    # Users (admin sees all)
    users_q = db.query(User)
    if tid:
        users_q = users_q.filter(User.tenant_id == tid)
    total_users = users_q.count()

    recent_devices_q = tq(Device).order_by(Device.updated_at.desc(), Device.created_at.desc()).limit(5)
    active_campaigns_q = (
        tq(Campaign)
        .filter(Campaign.status == "active")
        .order_by(Campaign.updated_at.desc(), Campaign.created_at.desc())
        .limit(5)
    )
    alerts_q = db.query(DeviceEvent).filter(DeviceEvent.severity.in_(["warning", "error", "critical"]))
    if tid:
        alerts_q = alerts_q.filter(DeviceEvent.tenant_id == tid)
    alerts_q = alerts_q.order_by(DeviceEvent.created_at.desc()).limit(5)

    views_per_day = (
        pb_q.with_entities(
            func.date(PlaybackLog.created_at).label("date"),
            func.count(PlaybackLog.id).label("views"),
        )
        .group_by(func.date(PlaybackLog.created_at))
        .order_by(func.date(PlaybackLog.created_at).asc())
        .all()
    )

    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": offline_devices,
        },
        "campaigns": {
            "total": total_campaigns,
            "active": active_campaigns,
        },
        "media": {
            "total": total_media,
        },
        "audio": {
            "total": total_audio,
        },
        "playbacks_7d": {
            "count": playbacks_7d,
            "total_duration_ms": total_views_7d,
        },
        "today": {
            "playbacks": today_playbacks_q.count(),
        },
        "users": {
            "total": total_users,
        },
        "views_per_day": [
            {"date": row.date.strftime("%d/%m") if hasattr(row.date, "strftime") else str(row.date), "views": row.views}
            for row in views_per_day
        ],
        "recent_devices": [
            {
                "id": str(device.id),
                "name": device.name,
                "location": device.location,
                "status": device.status.value if hasattr(device.status, "value") else device.status,
                "last_connection": device.last_connection,
                "last_seen_at": device.last_seen_at,
                "updated_at": device.updated_at,
            }
            for device in recent_devices_q
        ],
        "active_campaigns": [
            {
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status.value if hasattr(campaign.status, "value") else campaign.status,
                "device_count": len(campaign.device_ids or []),
                "total_views": campaign.total_views or 0,
            }
            for campaign in active_campaigns_q
        ],
        "alerts": [
            {
                "id": str(alert.id),
                "type": alert.event_type.value if hasattr(alert.event_type, "value") else alert.event_type,
                "severity": alert.severity.value if hasattr(alert.severity, "value") else alert.severity,
                "message": alert.description or (
                    alert.event_type.value if hasattr(alert.event_type, "value") else str(alert.event_type)
                ),
                "created_at": alert.created_at,
            }
            for alert in alerts_q
        ],
    }
