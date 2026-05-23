"""
FFprobe Service — Extrai metadados de áudio via ffprobe.

Obtém:
- duration_seconds (duração exata)
- bitrate
- sample_rate
- channels
- codec

Usado para validar e extrair metadados de uploads de áudio/vídeo.
"""

import subprocess
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path


class FFprobeError(Exception):
    """Erro ao executar ffprobe."""
    pass


def is_ffprobe_available() -> bool:
    """Verifica se ffprobe está instalado."""
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_audio_duration(file_path: str) -> Optional[int]:
    """
    Extrai duração de um arquivo de áudio em segundos.

    Args:
        file_path: Caminho local ou URL do arquivo.

    Returns:
        Duração em segundos (inteiro), ou None se não conseguir.

    Raises:
        FFprobeError: Se ffprobe falhar.
    """
    if not os.path.exists(file_path) and not file_path.startswith("http"):
        raise FFprobeError(f"Arquivo não encontrado: {file_path}")

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise FFprobeError(f"ffprobe failed: {result.stderr}")

        data = json.loads(result.stdout)
        duration_str = data.get("format", {}).get("duration")

        if duration_str:
            return int(float(duration_str))

        return None

    except subprocess.TimeoutExpired:
        raise FFprobeError("ffprobe timeout (arquivo muito grande ou acesso de rede lento)")
    except json.JSONDecodeError as e:
        raise FFprobeError(f"ffprobe output parse error: {e}")
    except Exception as e:
        raise FFprobeError(f"ffprobe error: {str(e)}")


def get_audio_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extrai todos os metadados de áudio de um arquivo.

    Args:
        file_path: Caminho local ou URL do arquivo.

    Returns:
        Dict com: duration_seconds, bitrate, sample_rate, channels, codec.
    """
    if not os.path.exists(file_path) and not file_path.startswith("http"):
        return None

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_format",
                "-show_streams",
                "-of", "json",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        format_data = data.get("format", {})
        streams = data.get("streams", [])

        audio_stream = next(
            (s for s in streams if s.get("codec_type") == "audio"),
            None,
        )

        if not audio_stream:
            return None

        duration_str = format_data.get("duration")
        duration_seconds = int(float(duration_str)) if duration_str else None

        return {
            "duration_seconds": duration_seconds,
            "bitrate": format_data.get("bit_rate"),
            "sample_rate": audio_stream.get("sample_rate"),
            "channels": audio_stream.get("channels"),
            "codec": audio_stream.get("codec_name"),
            "codec_long_name": audio_stream.get("codec_long_name"),
            "time_base": audio_stream.get("time_base"),
        }

    except Exception:
        return None


def validate_audio_file(file_path: str) -> bool:
    """
    Valida se um arquivo é áudio válido.

    Retorna True se conseguir extrair duração.
    """
    try:
        duration = get_audio_duration(file_path)
        return duration is not None and duration > 0
    except FFprobeError:
        return False
