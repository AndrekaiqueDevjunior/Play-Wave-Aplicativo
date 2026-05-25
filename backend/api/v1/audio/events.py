from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import AudioPlaybackEventCreate, AudioPlaybackEventResponse
from crud.entidades import crud_audio_playback_event

router = APIRouter(prefix="/audio/events", tags=["audio-events"])


@router.post(
    "/",
    response_model=List[AudioPlaybackEventResponse],
    status_code=http_status.HTTP_201_CREATED,
)
def log_playback_events(
    events: List[AudioPlaybackEventCreate],
    db: Session = Depends(get_db),
):
    """Registra um lote de eventos de reprodução enviados pelo player."""
    if not events:
        return []
    created = []
    for event in events:
        obj = crud_audio_playback_event.create(db, obj_in=event)
        created.append(obj)
    return created


@router.get(
    "/",
    response_model=List[AudioPlaybackEventResponse],
)
def list_playback_events(
    device_id: str = Query(..., description="ID do dispositivo"),
    event_type: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista eventos de reprodução de um dispositivo (requer autenticação de admin)."""
    if event_type:
        return crud_audio_playback_event.get_by_device_and_type(
            db, device_id=device_id, event_type=event_type, skip=skip, limit=limit
        )
    return crud_audio_playback_event.get_recent_by_device(
        db, device_id=device_id, hours=hours, limit=limit
    )
