"""CRUD da tabela device_pairing_events (SPEC 004 — auditoria de pareamento)."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import DevicePairingEvent, DevicePairingEventType, User


class CRUDDevicePairingEvent:
    def log(
        self,
        db: Session,
        *,
        device,
        event_type: str,
        requested_by_id: Optional[str] = None,
        reason: Optional[str] = None,
        previous_token_version: Optional[int] = None,
        new_token_version: Optional[int] = None,
        previous_pairing_version: Optional[int] = None,
        new_pairing_version: Optional[int] = None,
        previous_pairing_code: Optional[str] = None,
        new_pairing_code: Optional[str] = None,
        metadata: Optional[dict] = None,
        commit: bool = True,
    ) -> DevicePairingEvent:
        """Insere um evento de pareamento.

        `commit=False` permite enfileirar a insercao dentro de uma transacao
        maior (ex: regenerate_pairing_code ja faz commit das mudancas no
        device, e adiciona o evento na mesma transacao).
        """
        obj = DevicePairingEvent(
            device_id=device.id,
            tenant_id=device.tenant_id,
            event_type=event_type,
            previous_token_version=previous_token_version,
            new_token_version=new_token_version,
            previous_pairing_version=previous_pairing_version,
            new_pairing_version=new_pairing_version,
            previous_pairing_code=previous_pairing_code,
            new_pairing_code=new_pairing_code,
            requested_by=requested_by_id,
            reason=reason,
            extra_metadata=metadata,
            created_at=datetime.utcnow(),
        )
        db.add(obj)
        if commit:
            db.commit()
            db.refresh(obj)
        return obj

    def list_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        limit: int = 50,
        event_type: Optional[str] = None,
    ) -> List[DevicePairingEvent]:
        q = db.query(DevicePairingEvent).filter(DevicePairingEvent.device_id == device_id)
        if event_type:
            q = q.filter(DevicePairingEvent.event_type == event_type)
        return q.order_by(DevicePairingEvent.created_at.desc()).limit(limit).all()

    def count_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        event_type: Optional[str] = None,
    ) -> int:
        q = db.query(DevicePairingEvent).filter(DevicePairingEvent.device_id == device_id)
        if event_type:
            q = q.filter(DevicePairingEvent.event_type == event_type)
        return q.count()


crud_device_pairing_event = CRUDDevicePairingEvent()
