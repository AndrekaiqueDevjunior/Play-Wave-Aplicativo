from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from core.database import get_db
from core.dependencies import get_current_user
from core.models import Device, Campaign, Media, User, PlaybackLog, AudioTrack

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
        "users": {
            "total": total_users,
        },
    }
