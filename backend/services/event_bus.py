"""Real-time event bus on top of Redis Pub/Sub.

Eventos transientes (audio toggle, refresh, command broadcast) viajam por aqui
para entrega em ~milissegundos via SSE. Comandos persistentes continuam na fila
DB (DeviceCommand). Tarefas pesadas continuam no Celery.

Canal por dispositivo: ``pw:device:{device_id}:events``.
Eventos de campanha fazem fanout no publisher (resolve devices alvo no banco e
publica N vezes, uma por device).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Iterable, Optional

from sqlalchemy import and_, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from core.config import get_redis_client
from core.models import Campaign, Device


CHANNEL_PREFIX = "pw:device"


def channel_for_device(device_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{device_id}:events"


def _envelope(
    event_type: str,
    *,
    device_id: str,
    campaign_id: Optional[str],
    data: Optional[dict],
) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "device_id": str(device_id),
        "campaign_id": str(campaign_id) if campaign_id else None,
        "ts": datetime.utcnow().isoformat() + "Z",
        "data": data or {},
    }


def _publish(channel: str, envelope: dict) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.publish(channel, json.dumps(envelope))
        return True
    except Exception as exc:  # noqa: BLE001 — pub/sub é best-effort
        print(f"[event_bus] publish failed on {channel}: {exc}")
        return False


def publish_device_event(
    device_id: str,
    *,
    event_type: str,
    data: Optional[dict] = None,
    campaign_id: Optional[str] = None,
) -> bool:
    """Publica evento direto no canal de um dispositivo específico."""
    envelope = _envelope(event_type, device_id=device_id, campaign_id=campaign_id, data=data)
    return _publish(channel_for_device(device_id), envelope)


def _devices_for_campaign(db: Session, campaign: Campaign) -> Iterable[str]:
    """Retorna IDs (str) de devices que devem reagir a um evento da campanha.

    Combina:
    - Devices cujo current_campaign_id aponta para a campanha;
    - Devices listados em campaign.device_ids (JSONB).
    """
    bound_ids: set[str] = set()

    rows = (
        db.query(Device.id)
        .filter(Device.current_campaign_id == campaign.id)
        .all()
    )
    bound_ids.update(str(row.id) for row in rows)

    if campaign.device_ids:
        bound_ids.update(str(dev_id) for dev_id in campaign.device_ids if dev_id)

    return bound_ids


def publish_campaign_event(
    db: Session,
    campaign: Campaign,
    *,
    event_type: str,
    data: Optional[dict] = None,
) -> int:
    """Faz fanout de um evento de campanha para todos os devices alvo.

    Retorna a quantidade de canais alcançados (best-effort — Redis pub/sub é
    fire-and-forget; quem garante reconciliação é o snapshot inicial do SSE +
    o Celery beat de recálculo).
    """
    count = 0
    campaign_id = str(campaign.id)
    for device_id in _devices_for_campaign(db, campaign):
        envelope = _envelope(
            event_type,
            device_id=device_id,
            campaign_id=campaign_id,
            data=data,
        )
        if _publish(channel_for_device(device_id), envelope):
            count += 1
    return count


def publish_campaign_event_by_id(
    db: Session,
    campaign_id: str,
    *,
    event_type: str,
    data: Optional[dict] = None,
) -> int:
    """Conveniência: busca a campanha e delega para publish_campaign_event."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return 0
    return publish_campaign_event(db, campaign, event_type=event_type, data=data)
