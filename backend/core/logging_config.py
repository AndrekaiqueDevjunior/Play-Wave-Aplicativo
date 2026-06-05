"""
Configuração de logging estruturado para PlayWave
TASK 08: Logs estruturados para radio scheduler e player
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

# Criar loggers específicos por módulo
radio_scheduler_logger = logging.getLogger("radio.scheduler")
radio_player_logger = logging.getLogger("radio.player")
radio_spots_logger = logging.getLogger("radio.spots")

# Garantir que têm handlers
def _ensure_handler(logger):
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

radio_scheduler_logger = _ensure_handler(radio_scheduler_logger)
radio_player_logger = _ensure_handler(radio_player_logger)
radio_spots_logger = _ensure_handler(radio_spots_logger)


def log_spot_check(
    playlist_id: str,
    spot_count: int,
    active_count: int,
    now: Optional[datetime] = None,
):
    """Log quando verificamos spots elegíveis"""
    msg = f"spot_check playlist_id={playlist_id} total_schedules={spot_count} eligible={active_count}"
    if now:
        msg += f" now={now.isoformat()}"
    radio_scheduler_logger.info(msg)


def log_spot_eligible(
    spot_id: str,
    spot_name: str,
    schedule_id: str,
    interval_seconds: int,
    priority: int,
):
    """Log quando um spot é elegível"""
    msg = f"spot_eligible spot_id={spot_id} name={spot_name} schedule_id={schedule_id} interval_seconds={interval_seconds} priority={priority}"
    radio_spots_logger.info(msg)


def log_spot_ineligible(
    schedule_id: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None,
):
    """Log quando um spot NÃO é elegível"""
    msg = f"spot_ineligible schedule_id={schedule_id} reason={reason}"
    if details:
        for k, v in details.items():
            msg += f" {k}={v}"
    radio_spots_logger.info(msg)


def log_spot_due(
    spot_id: str,
    spot_name: str,
    interval_seconds: int,
    time_until: float,
):
    """Log quando um spot está marcado para tocar"""
    msg = f"spot_due=true spot_id={spot_id} name={spot_name} interval_seconds={interval_seconds} time_until_seconds={time_until:.1f}"
    radio_scheduler_logger.info(msg)


def log_spot_selected(
    selected_spot_id: str,
    selected_spot_name: str,
    insertion_policy: str,
):
    """Log quando um spot é selecionado para reprodução"""
    msg = f"selected_spot_id={selected_spot_id} name={selected_spot_name} insertion_policy={insertion_policy}"
    radio_scheduler_logger.info(msg)


def log_spot_playing(
    spot_id: str,
    spot_name: str,
    device_id: Optional[str] = None,
):
    """Log quando spot começa a tocar"""
    msg = f"playing_spot=true spot_id={spot_id} name={spot_name}"
    if device_id:
        msg += f" device_id={device_id}"
    radio_player_logger.info(msg)


def log_returning_to_music_queue(
    device_id: Optional[str] = None,
):
    """Log quando voltamos para a fila de música após spot"""
    msg = f"returning_to_music_queue=true"
    if device_id:
        msg += f" device_id={device_id}"
    radio_player_logger.info(msg)


def log_spot_error(
    spot_id: str,
    error_reason: str,
    details: Optional[Dict[str, Any]] = None,
):
    """Log quando há erro ao tocar spot"""
    msg = f"spot_error=true spot_id={spot_id} reason={error_reason}"
    if details:
        for k, v in details.items():
            msg += f" {k}={v}"
    radio_spots_logger.info(msg)
