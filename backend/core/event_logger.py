"""
Event Logger — Logs estruturados padronizados para radio, player e campanhas
TASK 35: Padronizar logs da rádio e do player
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

# Criar logger estruturado
event_logger = logging.getLogger("playwave.events")

# Garantir que tem handler
if not event_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    event_logger.addHandler(handler)
    event_logger.setLevel(logging.INFO)


class EventType(str, Enum):
    """Tipos de eventos padronizados"""

    # Eventos de playlist
    RADIO_PLAYLIST_LOADED = "radio.playlist.loaded"
    RADIO_FOLDER_RESOLVED = "radio.folder.resolved"
    RADIO_SCHEDULE_UPDATED = "radio.schedule.updated"

    # Eventos de track
    RADIO_TRACK_STARTED = "radio.track.started"
    RADIO_TRACK_ENDED = "radio.track.ended"
    RADIO_TRACK_FAILED = "radio.track.failed"
    RADIO_TRACK_SKIPPED = "radio.track.skipped"

    # Eventos de spot
    RADIO_SPOT_DUE = "radio.spot.due"
    RADIO_SPOT_STARTED = "radio.spot.started"
    RADIO_SPOT_FINISHED = "radio.spot.finished"
    RADIO_SPOT_FAILED = "radio.spot.failed"

    # Eventos de player
    PLAYER_SCHEDULE_UPDATED = "player.schedule.updated"
    PLAYER_COMMAND_RECEIVED = "player.command.received"
    PLAYER_COMMAND_EXECUTED = "player.command.executed"
    PLAYER_COMMAND_FAILED = "player.command.failed"
    PLAYER_CACHE_INVALIDATED = "player.cache.invalidated"

    # Eventos de campanha
    CAMPAIGN_MEDIA_SELECTED = "campaign.media.selected"
    CAMPAIGN_MEDIA_IGNORED = "campaign.media.ignored"
    CAMPAIGN_LOADED = "campaign.loaded"
    CAMPAIGN_UPDATED = "campaign.updated"


def log_event(
    event_type: EventType,
    device_id: Optional[str] = None,
    playlist_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log um evento estruturado.

    Args:
        event_type: Tipo de evento (EventType enum)
        device_id: ID do dispositivo (obrigatório para maioria dos eventos)
        playlist_id: ID da playlist (quando aplicável)
        details: Dicionário com detalhes adicionais
    """
    msg = f"event={event_type.value}"

    if device_id:
        msg += f" device_id={device_id}"

    if playlist_id:
        msg += f" playlist_id={playlist_id}"

    if details:
        for key, value in details.items():
            if isinstance(value, str) and ' ' in value:
                msg += f' {key}="{value}"'
            else:
                msg += f" {key}={value}"

    event_logger.info(msg)


# Funções auxiliares para eventos comuns

def log_playlist_loaded(
    device_id: str,
    playlist_id: str,
    folder_count: int,
    track_count: int,
):
    """Log quando playlist é carregada"""
    log_event(
        EventType.RADIO_PLAYLIST_LOADED,
        device_id=device_id,
        playlist_id=playlist_id,
        details={
            "folder_count": folder_count,
            "track_count": track_count,
        },
    )


def log_track_started(
    device_id: str,
    playlist_id: str,
    track_id: str,
    track_name: str,
    duration_seconds: int,
):
    """Log quando track começa a tocar"""
    log_event(
        EventType.RADIO_TRACK_STARTED,
        device_id=device_id,
        playlist_id=playlist_id,
        details={
            "track_id": track_id,
            "track_name": track_name,
            "duration_seconds": duration_seconds,
        },
    )


def log_track_ended(
    device_id: str,
    playlist_id: str,
    track_id: str,
    duration_seconds: int,
):
    """Log quando track termina"""
    log_event(
        EventType.RADIO_TRACK_ENDED,
        device_id=device_id,
        playlist_id=playlist_id,
        details={
            "track_id": track_id,
            "duration_seconds": duration_seconds,
        },
    )


def log_track_failed(
    device_id: str,
    playlist_id: str,
    track_id: str,
    error_reason: str,
):
    """Log quando track falha"""
    log_event(
        EventType.RADIO_TRACK_FAILED,
        device_id=device_id,
        playlist_id=playlist_id,
        details={
            "track_id": track_id,
            "error_reason": error_reason,
        },
    )


def log_spot_started(
    device_id: str,
    playlist_id: str,
    spot_id: str,
    spot_name: str,
):
    """Log quando spot começa a tocar"""
    log_event(
        EventType.RADIO_SPOT_STARTED,
        device_id=device_id,
        playlist_id=playlist_id,
        details={
            "spot_id": spot_id,
            "spot_name": spot_name,
        },
    )


def log_spot_finished(
    device_id: str,
    playlist_id: str,
    spot_id: str,
):
    """Log quando spot termina"""
    log_event(
        EventType.RADIO_SPOT_FINISHED,
        device_id=device_id,
        playlist_id=playlist_id,
        details={
            "spot_id": spot_id,
        },
    )


def log_campaign_media_selected(
    device_id: str,
    campaign_id: str,
    media_id: str,
    media_name: str,
):
    """Log quando mídia de campanha é selecionada"""
    log_event(
        EventType.CAMPAIGN_MEDIA_SELECTED,
        device_id=device_id,
        details={
            "campaign_id": campaign_id,
            "media_id": media_id,
            "media_name": media_name,
        },
    )


def log_campaign_media_ignored(
    device_id: str,
    campaign_id: str,
    media_id: str,
    media_name: str,
    reason: str,
):
    """Log quando mídia é ignorada"""
    log_event(
        EventType.CAMPAIGN_MEDIA_IGNORED,
        device_id=device_id,
        details={
            "campaign_id": campaign_id,
            "media_id": media_id,
            "media_name": media_name,
            "reason": reason,
        },
    )


def log_player_command_received(
    device_id: str,
    command_type: str,
    command_id: str,
):
    """Log quando player recebe comando"""
    log_event(
        EventType.PLAYER_COMMAND_RECEIVED,
        device_id=device_id,
        details={
            "command_type": command_type,
            "command_id": command_id,
        },
    )


def log_player_command_executed(
    device_id: str,
    command_type: str,
    command_id: str,
):
    """Log quando comando é executado"""
    log_event(
        EventType.PLAYER_COMMAND_EXECUTED,
        device_id=device_id,
        details={
            "command_type": command_type,
            "command_id": command_id,
        },
    )


def log_cache_invalidated(
    device_id: str,
    reason: str,
    old_version: Optional[str] = None,
    new_version: Optional[str] = None,
):
    """Log quando cache é invalidado"""
    details = {"reason": reason}
    if old_version:
        details["old_version"] = old_version
    if new_version:
        details["new_version"] = new_version

    log_event(
        EventType.PLAYER_CACHE_INVALIDATED,
        device_id=device_id,
        details=details,
    )
