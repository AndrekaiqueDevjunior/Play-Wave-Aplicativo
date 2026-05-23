from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.models import AudioPlaybackEvent
from core.schemas_completos import (
    AudioPlaybackEventCreate,
    AudioPlaybackEventCreate as AudioPlaybackEventUpdate,
)
from .crud_base import CRUDBase


class CRUDAudioPlaybackEvent(CRUDBase[AudioPlaybackEvent, AudioPlaybackEventCreate, AudioPlaybackEventUpdate]):
    def get_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AudioPlaybackEvent]:
        return (
            db.query(AudioPlaybackEvent)
            .filter(AudioPlaybackEvent.device_id == device_id)
            .order_by(desc(AudioPlaybackEvent.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_device_and_type(
        self,
        db: Session,
        *,
        device_id: str,
        event_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AudioPlaybackEvent]:
        return (
            db.query(AudioPlaybackEvent)
            .filter(
                AudioPlaybackEvent.device_id == device_id,
                AudioPlaybackEvent.event_type == event_type,
            )
            .order_by(desc(AudioPlaybackEvent.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        hours: int = 24,
        limit: int = 100,
    ) -> List[AudioPlaybackEvent]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(AudioPlaybackEvent)
            .filter(
                AudioPlaybackEvent.device_id == device_id,
                AudioPlaybackEvent.created_at >= cutoff,
            )
            .order_by(desc(AudioPlaybackEvent.created_at))
            .limit(limit)
            .all()
        )

    def get_errors_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AudioPlaybackEvent]:
        return (
            db.query(AudioPlaybackEvent)
            .filter(
                AudioPlaybackEvent.device_id == device_id,
                AudioPlaybackEvent.event_type == "error",
            )
            .order_by(desc(AudioPlaybackEvent.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def cleanup_old_events(
        self,
        db: Session,
        *,
        days: int = 30,
    ) -> int:
        """Remove eventos antigos. Retorna número de linhas deletadas."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = db.query(AudioPlaybackEvent).filter(
            AudioPlaybackEvent.created_at < cutoff
        ).delete()
        db.commit()
        return result


crud_audio_playback_event = CRUDAudioPlaybackEvent(AudioPlaybackEvent)
