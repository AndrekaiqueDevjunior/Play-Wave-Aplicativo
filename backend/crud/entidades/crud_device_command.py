from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.models import DESTRUCTIVE_COMMAND_TYPES, DeviceCommand, DeviceCommandStatus


DEFAULT_EXPIRES_IN_SECONDS = 600  # 10 minutos
MIN_EXPIRES_IN_SECONDS = 60
MAX_EXPIRES_IN_SECONDS = 3600
STUCK_SENT_TIMEOUT_MINUTES = 2
STUCK_EXECUTING_TIMEOUT_MINUTES = 5

# Statuses que ainda representam "trabalho por fazer" — usados para expiração
# e recuperação de comandos travados.
PENDING_STATUSES = (
    DeviceCommandStatus.PENDING,
    DeviceCommandStatus.SENT,
    DeviceCommandStatus.RECEIVED,
    DeviceCommandStatus.EXECUTING,
    DeviceCommandStatus.EXECUTED,  # legado: alias de RECEIVED
)


def is_destructive(command_type: str) -> bool:
    return command_type in DESTRUCTIVE_COMMAND_TYPES


def clamp_expires_in_seconds(value: Optional[int]) -> int:
    if value is None:
        return DEFAULT_EXPIRES_IN_SECONDS
    if value < MIN_EXPIRES_IN_SECONDS:
        return MIN_EXPIRES_IN_SECONDS
    if value > MAX_EXPIRES_IN_SECONDS:
        return MAX_EXPIRES_IN_SECONDS
    return value


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
        expires_in_seconds: Optional[int] = None,
    ) -> DeviceCommand:
        expires_in = clamp_expires_in_seconds(expires_in_seconds)
        now = datetime.utcnow()
        obj = DeviceCommand(
            device_id=device_id,
            tenant_id=tenant_id,
            command_type=command_type,
            payload=payload,
            status=DeviceCommandStatus.PENDING,
            requested_by=requested_by,
            requested_at=now,
            expires_at=now + timedelta(seconds=expires_in),
            is_destructive=is_destructive(command_type),
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
        """Retorna pending validos. Tambem aplica housekeeping local:
        - marca como EXPIRED tudo que ja passou de expires_at;
        - reabilita comandos travados em SENT por mais de N minutos.

        Housekeeping global eh feito pela task Celery `expire_stale_commands`.
        """
        now = datetime.utcnow()

        # 1) Marcar como EXPIRED comandos cujo expires_at ja passou.
        expired = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status.in_(PENDING_STATUSES),
                DeviceCommand.expires_at.isnot(None),
                DeviceCommand.expires_at < now,
            )
            .all()
        )
        for cmd in expired:
            cmd.status = DeviceCommandStatus.EXPIRED
            cmd.executed_at = now
            cmd.error_message = "Comando expirou sem ACK do player"

        # 2a) Reclamar comandos travados em SENT por > N minutos
        # (player pode ter caido entre SENT e o RECEIVED ACK).
        stuck_sent_cutoff = now - timedelta(minutes=STUCK_SENT_TIMEOUT_MINUTES)
        stuck = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status == DeviceCommandStatus.SENT,
                DeviceCommand.sent_at < stuck_sent_cutoff,
                or_(
                    DeviceCommand.expires_at.is_(None),
                    DeviceCommand.expires_at > now,
                ),
            )
            .all()
        )
        for cmd in stuck:
            cmd.status = DeviceCommandStatus.PENDING
            cmd.sent_at = None

        # 2b) Reclamar comandos travados em EXECUTING/RECEIVED/EXECUTED por > N min.
        # Ocorre quando o player morreu após marcar received/executing mas antes do ACK
        # (ex: restart_app — o processo é encerrado durante a execução).
        stuck_exec_cutoff = now - timedelta(minutes=STUCK_EXECUTING_TIMEOUT_MINUTES)
        stuck_exec = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status.in_([
                    DeviceCommandStatus.EXECUTING,
                    DeviceCommandStatus.RECEIVED,
                    DeviceCommandStatus.EXECUTED,
                ]),
                DeviceCommand.started_at < stuck_exec_cutoff,
                or_(
                    DeviceCommand.expires_at.is_(None),
                    DeviceCommand.expires_at > now,
                ),
            )
            .all()
        )
        for cmd in stuck_exec:
            cmd.status = DeviceCommandStatus.PENDING
            cmd.sent_at = None
            cmd.started_at = None
            cmd.received_at = None

        if stuck or stuck_exec or expired:
            db.commit()

        # 3) Listar pending ainda validos (expires_at NULL ou futuro).
        return (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status == DeviceCommandStatus.PENDING,
                or_(
                    DeviceCommand.expires_at.is_(None),
                    DeviceCommand.expires_at > now,
                ),
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

    def mark_many_sent(self, db: Session, *, commands: List[DeviceCommand]) -> None:
        if not commands:
            return
        sent_at = datetime.utcnow()
        for command in commands:
            command.status = DeviceCommandStatus.SENT
            command.sent_at = sent_at
            db.add(command)
        db.commit()

    def ack(
        self,
        db: Session,
        *,
        obj: DeviceCommand,
        success: bool,
        error_message: Optional[str] = None,
        result: Optional[dict] = None,
    ) -> DeviceCommand:
        obj.status = DeviceCommandStatus.COMPLETED if success else DeviceCommandStatus.FAILED
        obj.executed_at = datetime.utcnow()
        obj.result = result
        obj.error_message = error_message
        db.commit()
        db.refresh(obj)
        return obj

    def mark_received(self, db: Session, *, obj: DeviceCommand) -> DeviceCommand:
        obj.status = DeviceCommandStatus.RECEIVED
        obj.received_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return obj

    def mark_executing(self, db: Session, *, obj: DeviceCommand) -> DeviceCommand:
        obj.status = DeviceCommandStatus.EXECUTING
        obj.started_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return obj

    def cancel(self, db: Session, *, obj: DeviceCommand) -> DeviceCommand:
        obj.status = DeviceCommandStatus.CANCELLED
        obj.executed_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return obj

    def mark_expired_batch(self, db: Session) -> int:
        """Marca como EXPIRED todos os comandos cujo expires_at ja passou.

        Usado pela task Celery `expire_stale_commands` para limpeza global
        (independente de polling do player).
        """
        now = datetime.utcnow()
        stale = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.status.in_(PENDING_STATUSES),
                DeviceCommand.expires_at.isnot(None),
                DeviceCommand.expires_at < now,
            )
            .all()
        )
        for cmd in stale:
            cmd.status = DeviceCommandStatus.EXPIRED
            cmd.executed_at = now
            if not cmd.error_message:
                cmd.error_message = "Comando expirou sem ACK do player"
        if stale:
            db.commit()
        return len(stale)


crud_device_command = CRUDDeviceCommand()
