from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import DeviceCommand, DeviceCommandStatus


class CRUDDeviceCommand:
    def create(
        self,
        db: Session,
        *,
        device_id: str,
        tenant_id: Optional[str],
        command_type: str,
        requested_by: str,
        payload: Optional[dict] = None,
    ) -> DeviceCommand:
        obj = DeviceCommand(
            device_id=device_id,
            tenant_id=tenant_id,
            command_type=command_type,
            payload=payload,
            status=DeviceCommandStatus.PENDING,
            requested_by=requested_by,
            requested_at=datetime.utcnow(),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, *, command_id: str) -> Optional[DeviceCommand]:
        return db.query(DeviceCommand).filter(DeviceCommand.id == command_id).first()

    def get_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DeviceCommand]:
        return (
            db.query(DeviceCommand)
            .filter(DeviceCommand.device_id == device_id)
            .order_by(DeviceCommand.requested_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pending(self, db: Session, *, device_id: str) -> List[DeviceCommand]:
        # Reclaim commands stuck in SENT for > 2 minutes (player may have crashed/restarted)
        two_mins_ago = datetime.utcnow() - timedelta(minutes=2)
        stuck = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status == DeviceCommandStatus.SENT,
                DeviceCommand.sent_at < two_mins_ago,
            )
            .all()
        )
        for cmd in stuck:
            cmd.status = DeviceCommandStatus.PENDING
            cmd.sent_at = None
        if stuck:
            db.commit()

        return (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status == DeviceCommandStatus.PENDING,
            )
            .order_by(DeviceCommand.requested_at.asc())
            .all()
        )

    def mark_sent(self, db: Session, *, obj: DeviceCommand) -> DeviceCommand:
        obj.status = DeviceCommandStatus.SENT
        obj.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return obj

    def ack(
        self,
        db: Session,
        *,
        obj: DeviceCommand,
        success: bool,
        error_message: Optional[str] = None,
    ) -> DeviceCommand:
        obj.status = DeviceCommandStatus.EXECUTED if success else DeviceCommandStatus.FAILED
        obj.executed_at = datetime.utcnow()
        obj.error_message = error_message
        db.commit()
        db.refresh(obj)
        return obj

    def cancel(self, db: Session, *, obj: DeviceCommand) -> DeviceCommand:
        obj.status = DeviceCommandStatus.CANCELLED
        db.commit()
        db.refresh(obj)
        return obj


crud_device_command = CRUDDeviceCommand()
