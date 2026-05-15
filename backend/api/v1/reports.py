import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import Campaign, Device, PlaybackLog, User, ViewReport
from core.schemas_completos import PlaybackLogResponse, ViewReportResponse
from crud.entidades import crud_playback_log, crud_view_report

router = APIRouter(prefix="/reports", tags=["reports"])


def _tenant_id_for(user: User) -> Optional[str]:
    return None if user.role == "admin" else str(user.tenant_id)


def _period(days: int, date_from: Optional[datetime], date_to: Optional[datetime]):
    end = date_to or datetime.utcnow()
    start = date_from or (end - timedelta(days=days - 1))
    return start, end


def _apply_tenant(query, model, tenant_id: Optional[str]):
    if tenant_id:
        return query.filter(model.tenant_id == tenant_id)
    return query


def _status_counts(db: Session, tenant_id: Optional[str]):
    query = db.query(Device.status, func.count(Device.id)).group_by(Device.status)
    query = _apply_tenant(query, Device, tenant_id)
    counts = {str(status.value if hasattr(status, "value") else status): total for status, total in query.all()}
    return [
        {"name": "Online", "status": "online", "value": counts.get("online", 0), "color": "#10b981"},
        {"name": "Offline", "status": "offline", "value": counts.get("offline", 0), "color": "#ef4444"},
        {"name": "Sincronizando", "status": "syncing", "value": counts.get("syncing", 0), "color": "#f59e0b"},
        {"name": "Erro", "status": "error", "value": counts.get("error", 0), "color": "#f87171"},
        {"name": "Pareamento", "status": "waiting_pairing", "value": counts.get("waiting_pairing", 0), "color": "#60a5fa"},
        {"name": "Bloqueado", "status": "blocked", "value": counts.get("blocked", 0), "color": "#64748b"},
    ]


def _playback_query(
    db: Session,
    tenant_id: Optional[str],
    start: datetime,
    end: datetime,
    device_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
):
    query = db.query(PlaybackLog).filter(PlaybackLog.created_at >= start, PlaybackLog.created_at <= end)
    query = _apply_tenant(query, PlaybackLog, tenant_id)
    if device_id:
        query = query.filter(PlaybackLog.device_id == device_id)
    if campaign_id:
        query = query.filter(PlaybackLog.campaign_id == campaign_id)
    return query


# ─── Playback logs ────────────────────────────────────────────────────────────

@router.get("/playback", response_model=List[PlaybackLogResponse])
def list_playback_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=365),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    tid = _tenant_id_for(current_user)
    start, end = _period(days, date_from, date_to)
    return (
        _playback_query(db, tid, start, end, device_id, campaign_id)
        .order_by(PlaybackLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/playback/stats")
def playback_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=365),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)
    return crud_playback_log.get_statistics(db, tenant_id=tid, days=days)


@router.get("/summary")
def report_summary(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=365),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    device_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
):
    tid = _tenant_id_for(current_user)
    start, end = _period(days, date_from, date_to)
    playback = _playback_query(db, tid, start, end, device_id, campaign_id)

    total_views = playback.count()

    top_campaign_row = (
        playback.with_entities(
            PlaybackLog.campaign_id,
            PlaybackLog.campaign_name,
            func.count(PlaybackLog.id).label("views"),
        )
        .group_by(PlaybackLog.campaign_id, PlaybackLog.campaign_name)
        .order_by(func.count(PlaybackLog.id).desc())
        .first()
    )
    top_device_row = (
        playback.with_entities(
            PlaybackLog.device_id,
            PlaybackLog.device_name,
            func.count(PlaybackLog.id).label("views"),
        )
        .group_by(PlaybackLog.device_id, PlaybackLog.device_name)
        .order_by(func.count(PlaybackLog.id).desc())
        .first()
    )

    views_by_day_rows = (
        playback.with_entities(
            func.date(PlaybackLog.created_at).label("date"),
            func.count(PlaybackLog.id).label("views"),
        )
        .group_by(func.date(PlaybackLog.created_at))
        .order_by(func.date(PlaybackLog.created_at).asc())
        .all()
    )
    views_by_campaign_rows = (
        playback.with_entities(
            PlaybackLog.campaign_name.label("name"),
            func.count(PlaybackLog.id).label("views"),
        )
        .group_by(PlaybackLog.campaign_name)
        .order_by(func.count(PlaybackLog.id).desc())
        .limit(10)
        .all()
    )
    details = (
        playback.order_by(PlaybackLog.created_at.desc())
        .limit(200)
        .all()
    )

    devices_q = db.query(Device)
    devices_q = _apply_tenant(devices_q, Device, tid)
    campaigns_q = db.query(Campaign)
    campaigns_q = _apply_tenant(campaigns_q, Campaign, tid)

    problem_devices = devices_q.filter(Device.status.in_(["offline", "error", "blocked"])).count()

    return {
        "total_views": total_views,
        "total_devices": devices_q.count(),
        "active_campaigns": campaigns_q.filter(Campaign.status == "active").count(),
        "top_campaign": {
            "id": str(top_campaign_row.campaign_id) if top_campaign_row else None,
            "name": top_campaign_row.campaign_name if top_campaign_row else "Sem dados",
            "views": top_campaign_row.views if top_campaign_row else 0,
        },
        "top_device": {
            "id": str(top_device_row.device_id) if top_device_row else None,
            "name": top_device_row.device_name if top_device_row else "Sem dados",
            "views": top_device_row.views if top_device_row else 0,
        },
        "problem_devices": problem_devices,
        "views_per_day": [
            {"date": row.date.strftime("%d/%m") if hasattr(row.date, "strftime") else str(row.date), "views": row.views}
            for row in views_by_day_rows
        ],
        "views_by_campaign": [
            {"name": row.name or "Sem campanha", "views": row.views}
            for row in views_by_campaign_rows
        ],
        "device_status": _status_counts(db, tid),
        "details": [
            {
                "id": str(log.id),
                "date": log.created_at.strftime("%d/%m/%Y") if log.created_at else "",
                "device": log.device_name or str(log.device_id),
                "campaign": log.campaign_name or str(log.campaign_id),
                "media": log.media_name or str(log.media_id),
                "views": 1,
                "status": log.status.value if hasattr(log.status, "value") else log.status,
            }
            for log in details
        ],
    }


# ─── View reports ─────────────────────────────────────────────────────────────

@router.get("/views", response_model=List[ViewReportResponse])
def list_view_reports(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    if device_id:
        reports = crud_view_report.get_by_device(db, device_id=device_id)
    elif campaign_id:
        reports = crud_view_report.get_by_campaign(db, campaign_id=campaign_id)
    elif tid:
        reports = crud_view_report.get_by_tenant(db, tenant_id=tid)
    else:
        reports = crud_view_report.get_multi(db, skip=skip, limit=limit)

    return reports[skip: skip + limit]


@router.get("/views/stats")
def view_report_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=365),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)
    return crud_view_report.get_statistics(db, tenant_id=tid, days=days)


# ─── CSV Export ───────────────────────────────────────────────────────────────

@router.get("/export")
@router.get("/export/csv")
def export_playback_csv(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    if tid:
        logs = crud_playback_log.get_by_tenant(db, tenant_id=tid)
    else:
        logs = crud_playback_log.get_multi(db, skip=0, limit=10000)

    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = [l for l in logs if l.created_at and l.created_at >= cutoff]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "device_id", "campaign_id", "media_id", "status",
                     "started_at", "ended_at", "duration_ms", "created_at"])
    for log in logs:
        writer.writerow([
            str(log.id),
            str(log.device_id or ""),
            str(log.campaign_id or ""),
            str(log.media_id or ""),
            log.status or "",
            log.started_at.isoformat() if log.started_at else "",
            log.ended_at.isoformat() if log.ended_at else "",
            log.duration_ms or 0,
            log.created_at.isoformat() if log.created_at else "",
        ])

    output.seek(0)
    filename = f"playback_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─── Device / Campaign specific reports ────────────────────────────────────────

@router.get("/device/{device_id}")
def get_device_report(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = _tenant_id_for(current_user)
    logs = crud_playback_log.get_by_device(db, device_id=device_id)
    if tid:
        logs = [l for l in logs if str(l.tenant_id) == tid]
    return logs


@router.get("/campaign/{campaign_id}")
def get_campaign_report(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = _tenant_id_for(current_user)
    logs = crud_playback_log.get_by_campaign(db, campaign_id=campaign_id)
    if tid:
        logs = [l for l in logs if str(l.tenant_id) == tid]
    return logs


# ─── Register playback (admin or device) ───────────────────────────────────────

class PlaybackCreateBody(BaseModel):
    device_id: str
    campaign_id: str
    media_id: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "completed"


@router.post("/playback")
def register_playback(
    body: PlaybackCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = crud_playback_log.create_log(
        db,
        device_id=body.device_id,
        campaign_id=body.campaign_id,
        media_id=body.media_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
        duration_ms=body.duration_ms,
        status=body.status,
    )
    return {"id": str(log.id), "status": log.status}
