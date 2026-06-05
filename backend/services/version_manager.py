"""
Version Manager - Gerencia versões numéricas do agendamento

TASK 31: Versionamento numérico
- schedule_version: Incrementa quando programação estrutural muda (campaign/playlist assignment)
- campaign_version: Incrementa quando mídia da campanha muda
- version (AudioPlaylist): Incrementa quando tracks da playlist mudam
"""

from sqlalchemy.orm import Session
from core.models import Device, Campaign, AudioPlaylist
from datetime import datetime


def increment_device_schedule_version(db: Session, device_id: str) -> int:
    """
    Incrementa schedule_version do device.
    Usado quando campaign ou playlist é alterado.

    Exemplo: Admin altera campaign_id do dispositivo
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if device:
        device.schedule_version = (device.schedule_version or 0) + 1
        device.updated_at = datetime.utcnow()
        db.commit()
        return device.schedule_version
    return 0


def increment_campaign_version(db: Session, campaign_id: str) -> int:
    """
    Incrementa campaign_version.
    Usado quando mídia é adicionada/removida/reordenada na campanha.

    Exemplo: Admin adiciona novo vídeo à campanha
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign:
        campaign.campaign_version = (campaign.campaign_version or 0) + 1
        campaign.updated_at = datetime.utcnow()
        db.commit()

        # Também incrementar schedule_version de todos os devices atribuídos
        devices = db.query(Device).filter(Device.current_campaign_id == campaign_id).all()
        for device in devices:
            device.schedule_version = (device.schedule_version or 0) + 1
            device.updated_at = datetime.utcnow()
        db.commit()

        return campaign.campaign_version
    return 0


def increment_playlist_version(db: Session, playlist_id: str) -> int:
    """
    Incrementa version (AudioPlaylist).
    Usado quando tracks são adicionados/removidos/reordenados.

    Exemplo: Admin adiciona nova música à playlist de rádio
    """
    playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist_id).first()
    if playlist:
        playlist.version = (playlist.version or 0) + 1
        playlist.updated_at = datetime.utcnow()
        db.commit()

        # Também incrementar schedule_version de todos os devices usando playlist
        devices = db.query(Device).filter(Device.audio_playlist_id == playlist_id).all()
        for device in devices:
            device.schedule_version = (device.schedule_version or 0) + 1
            device.updated_at = datetime.utcnow()
        db.commit()

        return playlist.version
    return 0


def get_device_schedule_info(db: Session, device_id: str) -> dict:
    """
    Retorna versões de agendamento do device.

    Response:
    {
      "device_id": "...",
      "schedule_version": 42,           # Version geral de agendamento
      "campaign_id": "...",
      "campaign_version": 9,            # Version específica da campanha
      "audio_playlist_id": "...",
      "audio_playlist_version": 5,      # Version específica da playlist
      "updated_at": "2026-06-04T16:00:00"
    }
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None

    result = {
        "device_id": str(device.id),
        "schedule_version": device.schedule_version or 0,
        "campaign_id": str(device.current_campaign_id) if device.current_campaign_id else None,
        "campaign_version": 0,
        "audio_playlist_id": str(device.audio_playlist_id) if device.audio_playlist_id else None,
        "audio_playlist_version": 0,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
    }

    if device.current_campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == device.current_campaign_id).first()
        if campaign:
            result["campaign_version"] = campaign.campaign_version or 0

    if device.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()
        if playlist:
            result["audio_playlist_version"] = playlist.version or 0

    return result
