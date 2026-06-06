import logging
from datetime import datetime
from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.models import AudioSpotSchedule, AudioPlaylist, Campaign, Device
from core.schemas_completos import AudioSpotScheduleCreate, AudioSpotScheduleUpdate
from .crud_base import CRUDBase

log = logging.getLogger("playwave.spot_schedule")


def _bump_versions(db: Session, schedule: AudioSpotSchedule, reason: str) -> None:
    """Incrementa versão dos agregados afetados pelo schedule."""
    now = datetime.utcnow()

    if schedule.playlist_id:
        db.query(AudioPlaylist).filter(AudioPlaylist.id == schedule.playlist_id).update(
            {"version": AudioPlaylist.version + 1, "updated_at": now}
        )
        log.info(
            "player.schedule.version_incremented",
            extra={"playlist_id": str(schedule.playlist_id), "reason": reason},
        )

    if schedule.campaign_id:
        db.query(Campaign).filter(Campaign.id == schedule.campaign_id).update(
            {"campaign_version": Campaign.campaign_version + 1, "updated_at": now}
        )
        log.info(
            "player.schedule.version_incremented",
            extra={"campaign_id": str(schedule.campaign_id), "reason": reason},
        )

    if schedule.device_id:
        db.query(Device).filter(Device.id == schedule.device_id).update(
            {"schedule_version": Device.schedule_version + 1, "updated_at": now}
        )
        log.info(
            "player.schedule.version_incremented",
            extra={"device_id": str(schedule.device_id), "reason": reason},
        )


class CRUDAudioSpotSchedule(
    CRUDBase[AudioSpotSchedule, AudioSpotScheduleCreate, AudioSpotScheduleUpdate]
):
    def create(
        self,
        db: Session,
        *,
        obj_in: AudioSpotScheduleCreate,
        playlist_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        device_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> AudioSpotSchedule:
        data = jsonable_encoder(obj_in)

        # Escopos explícitos têm precedência sobre os do schema
        if playlist_id:
            data["playlist_id"] = playlist_id
        if campaign_id:
            data["campaign_id"] = campaign_id
        if device_id:
            data["device_id"] = device_id
        if tenant_id:
            data["tenant_id"] = tenant_id

        db_obj = AudioSpotSchedule(**data)
        db.add(db_obj)
        db.flush()

        _bump_versions(db, db_obj, reason="spot_schedule.created")

        db.commit()
        db.refresh(db_obj)

        log.info(
            "spot_schedule.created",
            extra={
                "schedule_id": str(db_obj.id),
                "spot_id": str(db_obj.spot_id),
                "tenant_id": str(db_obj.tenant_id) if db_obj.tenant_id else None,
                "playlist_id": str(db_obj.playlist_id) if db_obj.playlist_id else None,
                "campaign_id": str(db_obj.campaign_id) if db_obj.campaign_id else None,
                "device_id": str(db_obj.device_id) if db_obj.device_id else None,
            },
        )
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: AudioSpotSchedule,
        obj_in: AudioSpotScheduleUpdate,
    ) -> AudioSpotSchedule:
        data = obj_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.flush()

        _bump_versions(db, db_obj, reason="spot_schedule.updated")

        db.commit()
        db.refresh(db_obj)

        log.info(
            "spot_schedule.updated",
            extra={
                "schedule_id": str(db_obj.id),
                "spot_id": str(db_obj.spot_id),
                "tenant_id": str(db_obj.tenant_id) if db_obj.tenant_id else None,
            },
        )
        return db_obj

    def remove(self, db: Session, *, id: str) -> Optional[AudioSpotSchedule]:
        obj = db.query(AudioSpotSchedule).filter(AudioSpotSchedule.id == id).first()
        if obj:
            _bump_versions(db, obj, reason="spot_schedule.deleted")
            db.delete(obj)
            db.commit()
            log.info("spot_schedule.deleted", extra={"schedule_id": id})
        return obj

    def get_by_playlist(self, db: Session, *, playlist_id: str) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(AudioSpotSchedule.playlist_id == playlist_id)
            .order_by(AudioSpotSchedule.priority.desc())
            .all()
        )

    def get_by_campaign(self, db: Session, *, campaign_id: str) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(AudioSpotSchedule.campaign_id == campaign_id)
            .order_by(AudioSpotSchedule.priority.desc())
            .all()
        )

    def get_by_device(self, db: Session, *, device_id: str) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(AudioSpotSchedule.device_id == device_id)
            .order_by(AudioSpotSchedule.priority.desc())
            .all()
        )

    def get_active_by_playlist(self, db: Session, *, playlist_id: str) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(
                AudioSpotSchedule.playlist_id == playlist_id,
                AudioSpotSchedule.is_active.is_(True),
            )
            .order_by(AudioSpotSchedule.priority.desc())
            .all()
        )

    def get_by_spot(self, db: Session, *, spot_id: str) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(AudioSpotSchedule.spot_id == spot_id)
            .all()
        )


crud_audio_spot_schedule = CRUDAudioSpotSchedule(AudioSpotSchedule)
