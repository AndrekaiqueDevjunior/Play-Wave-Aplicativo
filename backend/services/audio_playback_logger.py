"""
Audio Playback Logger — Registra eventos de reprodução (quando algo tocou).

Eventos:
- track_started: música começou
- track_ended: música terminou (com duração)
- spot_started: anúncio começou
- spot_ended: anúncio terminou
- error: algo deu errado (ex: arquivo corrompido)

Pode ser chamado pelo player via API ou por um background worker.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from core.models import AudioPlaybackEvent
from core.schemas_completos import (
    AudioPlaybackEventCreate,
    AudioPlaybackEventTypeEnum,
    AudioPlaybackResultEnum,
)
from crud.entidades import crud_audio_playback_event


def log_track_started(
    db: Session,
    *,
    device_id: str,
    track_id: str,
    playlist_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AudioPlaybackEvent:
    """Registra início de uma track."""
    event = crud_audio_playback_event.create(
        db,
        obj_in=AudioPlaybackEventCreate(
            device_id=device_id,
            playlist_id=playlist_id,
            track_id=track_id,
            event_type=AudioPlaybackEventTypeEnum.TRACK_STARTED,
            result=AudioPlaybackResultEnum.SUCCESS,
            started_at=datetime.utcnow(),
            metadata=metadata,
        ),
    )
    return event


def log_track_ended(
    db: Session,
    *,
    device_id: str,
    track_id: str,
    playlist_id: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AudioPlaybackEvent:
    """Registra fim de uma track."""
    event = crud_audio_playback_event.create(
        db,
        obj_in=AudioPlaybackEventCreate(
            device_id=device_id,
            playlist_id=playlist_id,
            track_id=track_id,
            event_type=AudioPlaybackEventTypeEnum.TRACK_ENDED,
            result=AudioPlaybackResultEnum.SUCCESS,
            ended_at=datetime.utcnow(),
            duration_seconds=duration_seconds,
            metadata=metadata,
        ),
    )
    return event


def log_spot_started(
    db: Session,
    *,
    device_id: str,
    spot_id: str,
    playlist_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AudioPlaybackEvent:
    """Registra início de um spot."""
    event = crud_audio_playback_event.create(
        db,
        obj_in=AudioPlaybackEventCreate(
            device_id=device_id,
            playlist_id=playlist_id,
            spot_id=spot_id,
            event_type=AudioPlaybackEventTypeEnum.SPOT_STARTED,
            result=AudioPlaybackResultEnum.SUCCESS,
            started_at=datetime.utcnow(),
            metadata=metadata,
        ),
    )
    return event


def log_spot_ended(
    db: Session,
    *,
    device_id: str,
    spot_id: str,
    playlist_id: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AudioPlaybackEvent:
    """Registra fim de um spot."""
    event = crud_audio_playback_event.create(
        db,
        obj_in=AudioPlaybackEventCreate(
            device_id=device_id,
            playlist_id=playlist_id,
            spot_id=spot_id,
            event_type=AudioPlaybackEventTypeEnum.SPOT_ENDED,
            result=AudioPlaybackResultEnum.SUCCESS,
            ended_at=datetime.utcnow(),
            duration_seconds=duration_seconds,
            metadata=metadata,
        ),
    )
    return event


def log_playback_error(
    db: Session,
    *,
    device_id: str,
    error_message: str,
    track_id: Optional[str] = None,
    spot_id: Optional[str] = None,
    playlist_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AudioPlaybackEvent:
    """Registra erro durante reprodução."""
    event = crud_audio_playback_event.create(
        db,
        obj_in=AudioPlaybackEventCreate(
            device_id=device_id,
            playlist_id=playlist_id,
            track_id=track_id,
            spot_id=spot_id,
            event_type=AudioPlaybackEventTypeEnum.ERROR,
            result=AudioPlaybackResultEnum.FAILED,
            error_message=error_message,
            metadata=metadata,
        ),
    )
    return event


def log_track_skipped(
    db: Session,
    *,
    device_id: str,
    track_id: str,
    playlist_id: Optional[str] = None,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AudioPlaybackEvent:
    """Registra track que foi pulada (ex: arquivo corrompido)."""
    if not metadata:
        metadata = {}
    if reason:
        metadata["skip_reason"] = reason

    event = crud_audio_playback_event.create(
        db,
        obj_in=AudioPlaybackEventCreate(
            device_id=device_id,
            playlist_id=playlist_id,
            track_id=track_id,
            event_type=AudioPlaybackEventTypeEnum.TRACK_ENDED,
            result=AudioPlaybackResultEnum.SKIPPED,
            metadata=metadata,
        ),
    )
    return event
