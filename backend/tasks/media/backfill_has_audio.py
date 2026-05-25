"""Backfill `media.has_audio` for legacy video files.

Manual usage from `backend/`:
    python -m tasks.media.backfill_has_audio --limit 100
    python -m tasks.media.backfill_has_audio --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Optional

try:
    from celery import shared_task
except ModuleNotFoundError:
    def shared_task(*_args, **_kwargs):
        def decorator(func):
            return func
        return decorator


def media_type_value(media_type) -> str:
    return (media_type.value if hasattr(media_type, "value") else str(media_type or "")).lower()


def local_media_path(file_url: Optional[str], *, root: Path | None = None) -> Path | None:
    if not file_url:
        return None
    if file_url.startswith(("http://", "https://")):
        return None
    root = root or Path.cwd()
    return root / file_url.lstrip("/")


def detect_audio_streams(path: Path) -> Optional[bool]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return None
    except Exception:
        return None

    payload = json.loads(result.stdout or "{}")
    return bool(payload.get("streams"))


def backfill_has_audio(*, limit: int = 100, dry_run: bool = False, root: Path | None = None) -> dict:
    from core.database import SessionLocal
    from core.models import Media, MediaType

    db = SessionLocal()
    root = root or Path.cwd()
    stats = {
        "scanned": 0,
        "updated": 0,
        "missing_file": 0,
        "ffprobe_failed": 0,
        "skipped": 0,
        "dry_run": dry_run,
    }

    try:
        media_rows = (
            db.query(Media)
            .filter(Media.type == MediaType.VIDEO, Media.has_audio.is_(None))
            .order_by(Media.created_at.asc())
            .limit(limit)
            .all()
        )

        for media in media_rows:
            stats["scanned"] += 1
            path = local_media_path(media.file_url, root=root)
            if path is None:
                stats["skipped"] += 1
                continue
            if not path.is_file():
                stats["missing_file"] += 1
                continue

            has_audio = detect_audio_streams(path)
            if has_audio is None:
                stats["ffprobe_failed"] += 1
                continue

            if not dry_run:
                media.has_audio = has_audio
                db.add(media)
            stats["updated"] += 1

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return stats


@shared_task(name="tasks.media.backfill_has_audio")
def backfill_has_audio_task(limit: int = 100, dry_run: bool = False) -> dict:
    return backfill_has_audio(limit=limit, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill media.has_audio for legacy videos.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = backfill_has_audio(limit=args.limit, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
