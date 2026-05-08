import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import PlaybackLogResponse, ViewReportResponse
from crud.entidades import crud_playback_log, crud_view_report

router = APIRouter(prefix="/reports", tags=["reports"])


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
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    if device_id:
        logs = crud_playback_log.get_by_device(db, device_id=device_id)
    elif campaign_id:
        logs = crud_playback_log.get_by_campaign(db, campaign_id=campaign_id)
    elif tid:
        logs = crud_playback_log.get_by_tenant(db, tenant_id=tid)
    else:
        logs = crud_playback_log.get_multi(db, skip=skip, limit=limit)

    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = [l for l in logs if l.created_at and l.created_at >= cutoff]

    return logs[skip: skip + limit]


@router.get("/playback/stats")
def playback_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=365),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)
    return crud_playback_log.get_statistics(db, tenant_id=tid, days=days)


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
