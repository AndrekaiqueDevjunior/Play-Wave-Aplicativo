from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime

from core.database import get_db
from core.dependencies import get_current_user
from core.models import Campaign, Device, Media, MediaStatus, MediaVersion, PlaybackLog, User, ViewReport
from core.schemas_completos import (
    MediaCreate, MediaUpdate, MediaResponse, MediaTypeEnum, MediaStatusEnum, MediaVersionResponse,
    RecomputeAudioDetectionResponse,
    MediaBulkActionRequest, MediaBulkActionResponse, MediaBulkActionItemResult,
)
from crud.entidades import crud_media
from core.config import settings

router = APIRouter(prefix="/media", tags=["media"])
MAX_UPLOAD_BYTES = 500 * 1024 * 1024

# ─── MIME / extension mappings ───────────────────────────────────────────────

ALLOWED_MIME = {
    "image": [
        "image/jpeg", "image/jpg", "image/png", "image/webp",
        "image/gif", "image/svg+xml",
    ],
    "video": [
        "video/mp4", "video/webm", "video/quicktime",
        "video/x-matroska", "video/x-msvideo", "video/avi",
    ],
    "audio": [
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg",
        "audio/m4a", "audio/x-m4a",
    ],
}

ALLOWED_EXT = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"},
    "video": {".mp4", ".webm", ".mov", ".mkv", ".avi"},
    "audio": {".mp3", ".wav", ".ogg", ".m4a"},
}

YOUTUBE_RE = re.compile(r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/)([^&?/]+)")
VIMEO_RE   = re.compile(r"vimeo\.com/(\d+)")


def _detect_url_subtype(url: str) -> str:
    """Return a hint about the URL: 'youtube', 'vimeo', 'image', 'video', or 'external_url'."""
    if not url:
        return "external_url"
    lower = url.lower().split("?")[0]
    if YOUTUBE_RE.search(url):
        return "youtube"
    if VIMEO_RE.search(url):
        return "vimeo"
    ext = os.path.splitext(lower)[1]
    if ext in ALLOWED_EXT["image"]:
        return "image"
    if ext in ALLOWED_EXT["video"]:
        return "video"
    if ext in ALLOWED_EXT["audio"]:
        return "audio"
    return "external_url"


def _validate_file(file: UploadFile, media_type: str) -> None:
    """Raise 400 if the file MIME type or extension is not allowed for media_type."""
    allowed_mimes = ALLOWED_MIME.get(media_type, [])
    content_type = (file.content_type or "").lower()
    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed_exts = ALLOWED_EXT.get(media_type, set())

    if content_type not in allowed_mimes and ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido para '{media_type}'. "
                   f"MIME recebido: {content_type}, extensão: {ext}",
        )


def _validate_period(starts_at: Optional[datetime], ends_at: Optional[datetime]) -> None:
    if starts_at and ends_at and ends_at < starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data final da mídia deve ser maior ou igual à data inicial",
        )


def _parse_datetime_input(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    normalized = value.strip()
    if len(normalized) == 10 and "T" not in normalized:
        normalized = f"{normalized}T00:00:00"
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data da mídia inválida. Use YYYY-MM-DD ou ISO datetime.",
        )


def _media_availability(media: Media, *, now: Optional[datetime] = None) -> str:
    if media.status == MediaStatus.PROCESSING:
        return "processing"
    if media.status == MediaStatus.ERROR:
        return "error"
    if media.is_active is False:
        return "inactive"

    now = now or datetime.utcnow()
    if media.starts_at and media.starts_at > now:
        return "scheduled"
    if media.ends_at and media.ends_at < now:
        return "expired"
    return "active"


def _is_media_playable(media: Media, *, now: Optional[datetime] = None) -> bool:
    return _media_availability(media, now=now) == "active"


def _sha256_file(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _extract_media_metadata(path: str) -> dict:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=width,height,codec_name,codec_type",
                "-of",
                "json",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        payload = json.loads(result.stdout or "{}")
    except FileNotFoundError:
        return {"ffprobe_available": False}
    except Exception as exc:  # noqa: BLE001
        return {"ffprobe_error": str(exc)}

    duration = None
    try:
        raw_duration = payload.get("format", {}).get("duration")
        duration = int(round(float(raw_duration))) if raw_duration else None
    except (TypeError, ValueError):
        duration = None

    resolution = None
    for stream in payload.get("streams", []):
        if stream.get("codec_type") == "video" and stream.get("width") and stream.get("height"):
            resolution = f"{stream.get('width')}x{stream.get('height')}"
            break

    return {
        "duration_seconds": duration,
        "resolution": resolution,
        "ffprobe_available": True,
        "streams": payload.get("streams", []),
    }


def _detect_audio_streams(path: str) -> Optional[bool]:
    """Retorna True se o arquivo tem streams de áudio, False se não tem, None se ffprobe indisponível."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        payload = json.loads(result.stdout or "{}")
        return len(payload.get("streams", [])) > 0
    except FileNotFoundError:
        return None  # ffprobe não disponível
    except Exception:
        return None


def _save_upload_file(file: UploadFile, *, upload_dir: str = "uploads/media") -> tuple[str, str]:
    os.makedirs(upload_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "file")
    filename = f"{timestamp}_{safe_name}"
    file_path = os.path.join(upload_dir, filename)
    try:
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar arquivo: {exc}",
        )
    file_size = os.path.getsize(file_path)
    if file_size > MAX_UPLOAD_BYTES:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Arquivo maior que o limite de 500MB",
        )
    return filename, file_path


def _default_display_duration(media_type: str, display_duration: Optional[int]) -> Optional[int]:
    media_type_value = media_type.value if hasattr(media_type, "value") else media_type
    if display_duration and display_duration > 0:
        return display_duration
    if media_type_value == MediaTypeEnum.IMAGE.value:
        return 15
    if media_type_value == MediaTypeEnum.EXTERNAL_URL.value:
        return 15
    return None


def _create_media_version(
    db: Session,
    *,
    media: Media,
    file_name: Optional[str],
    created_by: Optional[str],
) -> MediaVersion:
    db.query(MediaVersion).filter(MediaVersion.media_id == media.id).update(
        {"is_current": False},
        synchronize_session=False,
    )
    version = MediaVersion(
        media_id=media.id,
        file_url=media.file_url,
        thumbnail_url=media.thumbnail_url,
        file_name=file_name,
        mime_type=media.mime_type,
        file_size=media.file_size,
        file_hash=media.file_hash,
        duration_seconds=media.duration_seconds,
        version_number=media.file_version or 1,
        is_current=True,
        created_by=created_by,
    )
    db.add(version)
    return version


def _campaigns_using_media(db: Session, *, media_id: str) -> List[Campaign]:
    campaigns = db.query(Campaign).filter(
        (Campaign.media_ids.isnot(None)) | (Campaign.media_order.isnot(None))
    ).all()
    used = []
    for campaign in campaigns:
        media_ids = {str(item) for item in (campaign.media_ids or []) if item}
        if campaign.media_order:
            media_ids.update(
                str(item.get("media_id"))
                for item in campaign.media_order
                if isinstance(item, dict) and item.get("media_id")
            )
        if media_id in media_ids:
            used.append(campaign)
    return used


def _decorate_media(db: Session, media: Media) -> Media:
    media.availability_status = _media_availability(media)
    media.usage_count = len(_campaigns_using_media(db, media_id=str(media.id)))
    return media


def _decorate_media_list(db: Session, media_list: List[Media]) -> List[Media]:
    for media in media_list:
        _decorate_media(db, media)
    return media_list


def _invalidate_device_playlist_cache(device_ids: Optional[set[str]] = None) -> None:
    from core.config import get_redis_client

    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        if device_ids is not None:
            if not device_ids:
                return
            pipe = redis_client.pipeline(transaction=False)
            for device_id in device_ids:
                pipe.delete(f"device_playlist:{device_id}")
            pipe.execute()
            return
        for key in redis_client.scan_iter("device_playlist:*"):
            redis_client.delete(key)
    except Exception as exc:
        print(f"[media] Redis cache invalidation error: {exc}")


def _device_ids_for_campaigns(db: Session, campaigns: List[Campaign]) -> set[str]:
    device_ids = {
        str(device_id)
        for campaign in campaigns
        for device_id in (campaign.device_ids or [])
        if device_id
    }
    campaign_ids = [campaign.id for campaign in campaigns if campaign.id]
    if campaign_ids:
        rows = db.query(Device.id).filter(Device.current_campaign_id.in_(campaign_ids)).all()
        device_ids.update(str(row.id) for row in rows)
    return device_ids


def _remove_media_from_campaigns(db: Session, *, media_id: str) -> List[Campaign]:
    changed_campaigns: List[Campaign] = []
    campaigns = db.query(Campaign).filter(
        (Campaign.media_ids.isnot(None)) | (Campaign.media_order.isnot(None))
    ).all()

    for campaign in campaigns:
        changed = False
        original_media_ids = [str(item) for item in (campaign.media_ids or [])]
        next_media_ids = [item for item in original_media_ids if item != media_id]
        if next_media_ids != original_media_ids:
            campaign.media_ids = next_media_ids
            changed = True

        if campaign.media_order:
            next_media_order = []
            for item in campaign.media_order:
                item_media_id = item.get("media_id") if isinstance(item, dict) else None
                if str(item_media_id) != media_id:
                    next_media_order.append(item)
            if next_media_order != campaign.media_order:
                campaign.media_order = next_media_order
                changed = True

        if changed:
            campaign.config_version = str(uuid.uuid4())
            db.add(campaign)
            changed_campaigns.append(campaign)

    if changed_campaigns:
        db.commit()
        for campaign in changed_campaigns:
            db.refresh(campaign)

    return changed_campaigns


def _touch_campaigns_for_media_change(db: Session, *, media_id: str) -> List[Campaign]:
    changed_campaigns = _campaigns_using_media(db, media_id=media_id)
    for campaign in changed_campaigns:
        campaign.config_version = str(uuid.uuid4())
        db.add(campaign)
    if changed_campaigns:
        db.commit()
        for campaign in changed_campaigns:
            db.refresh(campaign)
    return changed_campaigns


def _broadcast_media_changed(
    db: Session,
    campaigns: List[Campaign],
    *,
    media_id: str,
    reason: str,
) -> None:
    from services.event_bus import publish_campaign_event

    for campaign in campaigns:
        try:
            publish_campaign_event(
                db,
                campaign,
                event_type="playlist_invalidated",
                data={
                    "config_version": campaign.config_version,
                    "reason": reason,
                    "media_id": media_id,
                },
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[media] broadcast {reason} failed for campaign={campaign.id}: {exc}")


@router.get("/", response_model=List[MediaResponse])
def get_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    media_type: Optional[MediaTypeEnum] = Query(None),
    status: Optional[MediaStatusEnum] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    # SPEC 018 — mesmo padrão das SPECs 016/017: por padrão, mídias
    # arquivadas não aparecem em nenhuma listagem/seletor de campanha.
    # include_archived=true mostra também as arquivadas; status explícito
    # (ex.: status=archived) tem precedência.
    include_archived: bool = Query(False),
):
    """
    Lista mídias com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)

    # Aplicar filtros específicos
    if media_type:
        media_list = crud_media.get_by_type(db, media_type=media_type)
    elif status:
        media_list = crud_media.get_by_status(db, status=status)
    elif category:
        media_list = crud_media.get_by_category(db, category=category)
    elif tags:
        tag_list = tags.split(",") if tags else []
        media_list = crud_media.get_by_tags(db, tags=tag_list)
    elif tenant_id:
        media_list = crud_media.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        media_list = crud_media.search(db, query=search, skip=skip, limit=limit)
    else:
        media_list = crud_media.get_multi(db, skip=skip, limit=limit)

    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]

    if not status and not include_archived:
        media_list = [m for m in media_list if m.status != "archived"]

    return media_list


@router.get("/{media_id}", response_model=MediaResponse)
def get_media_by_id(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str
):
    """
    Obtém mídia por ID
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta mídia"
        )
    
    return _decorate_media(db, media)


@router.post("/", response_model=MediaResponse)
def create_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_in: MediaCreate
):
    """
    Cria nova mídia (metadados)
    """
    _validate_period(media_in.starts_at, media_in.ends_at)
    if media_in.display_duration_seconds:
        media_in.duration = media_in.display_duration_seconds
    elif media_in.type in (MediaTypeEnum.IMAGE, MediaTypeEnum.EXTERNAL_URL) and not media_in.duration:
        media_in.duration = 15
        media_in.display_duration_seconds = 15

    media_in.created_by = str(current_user.id)
    media_in.updated_by = str(current_user.id)

    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        media_in.tenant_id = str(current_user.tenant_id)
    
    media = crud_media.create(db, obj_in=media_in)
    return _decorate_media(db, media)


@router.post("/upload", response_model=MediaResponse)
def upload_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    name: str = Form(...),
    media_type: MediaTypeEnum = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    display_duration_seconds: Optional[int] = Form(None),
    starts_at: Optional[str] = Form(None),
    ends_at: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    _validate_file(file, media_type)
    starts_at_dt = _parse_datetime_input(starts_at)
    ends_at_dt = _parse_datetime_input(ends_at)
    _validate_period(starts_at_dt, ends_at_dt)

    filename, file_path = _save_upload_file(file)
    is_av = media_type in (MediaTypeEnum.VIDEO, MediaTypeEnum.AUDIO)
    metadata = _extract_media_metadata(file_path) if is_av else {}
    real_duration = metadata.get("duration_seconds") if is_av else None
    display_duration = _default_display_duration(media_type, display_duration_seconds or duration)
    file_hash = _sha256_file(file_path)

    # SPEC 005 — detectar has_audio via ffprobe para vídeos
    if media_type == MediaTypeEnum.VIDEO:
        has_audio = _detect_audio_streams(file_path)
    elif media_type in (MediaTypeEnum.IMAGE, MediaTypeEnum.EXTERNAL_URL):
        has_audio = False
    else:
        has_audio = None  # áudio puro: não relevante para o resolver

    media_data = {
        "name": name,
        "description": description,
        "file_url": f"/uploads/media/{filename}",
        "thumbnail_url": f"/uploads/media/{filename}" if media_type == MediaTypeEnum.IMAGE else None,
        "type": media_type,
        "mime_type": file.content_type,
        "file_size": os.path.getsize(file_path),
        "duration": display_duration,
        "duration_seconds": real_duration,
        "display_duration_seconds": display_duration,
        "file_hash": file_hash,
        "file_version": 1,
        "resolution": metadata.get("resolution"),
        "starts_at": starts_at_dt,
        "ends_at": ends_at_dt,
        "extra_metadata": metadata or None,
        "tags": [t.strip() for t in tags.split(",") if t.strip()] if tags else [],
        "category": category,
        "notes": notes,
        "created_by": str(current_user.id),
        "updated_by": str(current_user.id),
        "has_audio": has_audio,  # SPEC 005
    }
    if current_user.role != "admin":
        media_data["tenant_id"] = str(current_user.tenant_id)

    media = crud_media.create(db, obj_in=MediaCreate(**media_data))
    _create_media_version(db, media=media, file_name=file.filename, created_by=str(current_user.id))
    db.commit()
    db.refresh(media)
    return _decorate_media(db, media)


@router.put("/{media_id}", response_model=MediaResponse)
def update_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    media_in: MediaUpdate
):
    """
    Atualiza mídia
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta mídia"
        )
    
    starts_at = media_in.starts_at if media_in.starts_at is not None else media.starts_at
    ends_at = media_in.ends_at if media_in.ends_at is not None else media.ends_at
    _validate_period(starts_at, ends_at)

    update_data = media_in.model_dump(exclude_unset=True)
    if "display_duration_seconds" in update_data:
        update_data["duration"] = update_data["display_duration_seconds"]
    elif "duration" in update_data and update_data["duration"]:
        update_data["display_duration_seconds"] = update_data["duration"]
    update_data["updated_by"] = str(current_user.id)

    media = crud_media.update(db, db_obj=media, obj_in=update_data)
    changed_campaigns = _touch_campaigns_for_media_change(db, media_id=media_id)
    if changed_campaigns:
        _invalidate_device_playlist_cache(_device_ids_for_campaigns(db, changed_campaigns))
        _broadcast_media_changed(db, changed_campaigns, media_id=media_id, reason="media_updated")
    return _decorate_media(db, media)


@router.post("/{media_id}/recompute-audio-detection", response_model=RecomputeAudioDetectionResponse)
def recompute_audio_detection(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
):
    """SPEC 005 — re-roda ffprobe e atualiza has_audio da mídia."""
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")

    media_type_val = media.type.value if hasattr(media.type, "value") else str(media.type)
    if media_type_val not in ("video",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Detecção de áudio disponível apenas para vídeos",
        )

    file_url = media.file_url or ""
    rel_path = file_url.lstrip("/")
    file_path = os.path.join(".", rel_path)

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo de mídia não encontrado no servidor para re-análise",
        )

    has_audio = _detect_audio_streams(file_path)
    if has_audio is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ffprobe indisponível ou falhou ao analisar o arquivo",
        )

    media.has_audio = has_audio
    db.add(media)
    db.commit()

    return RecomputeAudioDetectionResponse(
        media_id=str(media.id),
        has_audio=has_audio,
        detected_at=datetime.utcnow(),
    )


@router.get("/{media_id}/usage")
def get_media_usage(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
):
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta mídia")

    campaigns = _campaigns_using_media(db, media_id=media_id)
    return {
        "media_id": media_id,
        "usage_count": len(campaigns),
        "campaigns": [
            {
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status.value if hasattr(campaign.status, "value") else campaign.status,
                "config_version": campaign.config_version,
            }
            for campaign in campaigns
        ],
    }


@router.get("/{media_id}/versions", response_model=List[MediaVersionResponse])
def get_media_versions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
):
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta mídia")
    return (
        db.query(MediaVersion)
        .filter(MediaVersion.media_id == media_id)
        .order_by(MediaVersion.version_number.desc())
        .all()
    )


@router.post("/{media_id}/replace-file", response_model=MediaResponse)
def replace_media_file(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    file: UploadFile = File(...),
):
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para atualizar esta mídia")

    media_type = media.type.value if hasattr(media.type, "value") else media.type
    _validate_file(file, media_type)

    filename, file_path = _save_upload_file(file)
    metadata = _extract_media_metadata(file_path) if media_type in ("video", "audio") else {}
    real_duration = metadata.get("duration_seconds") if media_type in ("video", "audio") else None
    file_hash = _sha256_file(file_path)
    display_duration = _default_display_duration(media_type, media.display_duration_seconds or media.duration)

    old_file_url = media.file_url
    media.file_url = f"/uploads/media/{filename}"
    media.thumbnail_url = media.file_url if media_type == "image" else media.thumbnail_url
    media.mime_type = file.content_type
    media.file_size = os.path.getsize(file_path)
    media.file_hash = file_hash
    media.file_version = (media.file_version or 1) + 1
    media.duration_seconds = real_duration
    media.display_duration_seconds = display_duration
    media.duration = display_duration
    media.resolution = metadata.get("resolution")
    media.extra_metadata = {
        **(media.extra_metadata or {}),
        "last_replace": {
            "old_file_url": old_file_url,
            "new_file_url": media.file_url,
            "replaced_at": datetime.utcnow().isoformat(),
            "replaced_by": str(current_user.id),
        },
        "probe": metadata,
    }
    media.updated_by = current_user.id
    media.updated_at = datetime.utcnow()
    db.add(media)
    db.flush()
    _create_media_version(db, media=media, file_name=file.filename, created_by=str(current_user.id))
    changed_campaigns = _touch_campaigns_for_media_change(db, media_id=media_id)
    db.commit()
    db.refresh(media)
    if changed_campaigns:
        _invalidate_device_playlist_cache(_device_ids_for_campaigns(db, changed_campaigns))
        _broadcast_media_changed(db, changed_campaigns, media_id=media_id, reason="media_replaced")
    return _decorate_media(db, media)


@router.delete("/{media_id}")
def delete_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    force: bool = Query(False),
):
    """
    Remove mídia definitivamente.

    SPEC 018 — a checagem de uso agora também conta `CampaignPlaylistItem`
    (tabela relacional com FK RESTRICT, é o caminho real que o player usa
    para resolver a campanha), além dos campos legados `Campaign.media_ids`/
    `media_order` já verificados. `force=True` continua desvinculando os
    campos legados automaticamente, mas NUNCA remove itens de
    `CampaignPlaylistItem` — isso exige remoção explícita via
    `DELETE /campaigns/{id}/items/{item_id}`, pois é uma mudança de conteúdo
    real da campanha, não um campo de conveniência legado.
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )

    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta mídia"
        )

    refs = crud_media.get_in_use_references(db, media_id=media_id)
    if refs["campaign_playlist_items"] > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Mídia em uso em playlists de campanha "
                f"({refs['campaign_playlist_items']} item(s)) e não pode ser excluída "
                "definitivamente. Remova-a da playlist da campanha antes de excluir."
            ),
        )

    used_campaigns = _campaigns_using_media(db, media_id=media_id)
    if used_campaigns and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Mídia em uso por campanhas. Use exclusão forçada apenas se quiser remover vínculos.",
                "usage_count": len(used_campaigns),
                "campaigns": [{"id": str(c.id), "name": c.name} for c in used_campaigns],
            },
        )

    changed_campaigns = _remove_media_from_campaigns(db, media_id=media_id) if force else []

    db.query(PlaybackLog).filter(PlaybackLog.media_id == media_id).delete(synchronize_session=False)
    db.query(ViewReport).filter(ViewReport.media_id == media_id).delete(synchronize_session=False)

    # Remover arquivo físico se existir
    if media.file_url and media.file_url.startswith("/uploads/"):
        file_path = media.file_url[1:]  # Remove o /
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignora erro ao remover arquivo

    crud_media.remove(db, id=media_id)
    if changed_campaigns:
        _invalidate_device_playlist_cache(_device_ids_for_campaigns(db, changed_campaigns))
        _broadcast_media_changed(db, changed_campaigns, media_id=media_id, reason="media_deleted")
    return {"message": "Mídia removida com sucesso"}


@router.patch("/{media_id}/status")
def update_media_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    media_status: MediaStatusEnum
):
    """
    Atualiza status da mídia
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta mídia"
        )
    
    media = crud_media.update_status(db, db_obj=media, status=media_status)
    return {"message": f"Status atualizado para {media_status}"}


def _bulk_authorize_media(db: Session, *, media_id: str, current_user: User) -> tuple[Optional[Media], Optional[str]]:
    """Busca e autoriza uma mídia para uma ação em massa.

    Retorna (media, None) em sucesso, ou (None, motivo) quando a mídia não
    existe ou o usuário não tem permissão — usado pelos endpoints bulk para
    reportar falha por item sem interromper o lote inteiro.
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        return None, "Mídia não encontrada"
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        return None, "Sem permissão para esta mídia"
    return media, None


@router.post("/bulk-archive", response_model=MediaBulkActionResponse)
def bulk_archive_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: MediaBulkActionRequest,
):
    """
    Arquiva múltiplas mídias de uma vez.

    SPEC 018 — ação em massa segura: cada item é processado
    independentemente, então uma falha (404/403) em um item não impede os
    demais de serem arquivados. Arquivar nunca falha por "em uso" — ao
    contrário da exclusão definitiva, arquivar é reversível e não remove
    a mídia de campanhas que ainda a referenciam (ela só some das seleções
    futuras, ver GET /media com include_archived=false).
    """
    results: List[MediaBulkActionItemResult] = []
    for media_id in payload.media_ids:
        media, error = _bulk_authorize_media(db, media_id=media_id, current_user=current_user)
        if error:
            results.append(MediaBulkActionItemResult(media_id=media_id, success=False, reason=error))
            continue
        crud_media.update_status(db, db_obj=media, status="archived")
        results.append(MediaBulkActionItemResult(media_id=media_id, success=True))

    succeeded = sum(1 for r in results if r.success)
    return MediaBulkActionResponse(
        requested=len(payload.media_ids),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


@router.post("/bulk-delete", response_model=MediaBulkActionResponse)
def bulk_delete_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: MediaBulkActionRequest,
):
    """
    Exclui definitivamente múltiplas mídias de uma vez.

    SPEC 018 — cada item é processado independentemente: uma mídia em uso
    (referenciada por CampaignPlaylistItem ou pelos campos legados
    Campaign.media_ids/media_order) é reportada como falha com o motivo,
    sem impedir que as demais mídias do lote sejam excluídas. Não há
    parâmetro `force` no bulk — diferente do DELETE individual, uma ação em
    massa não deve desvincular campanhas silenciosamente; o usuário precisa
    arquivar ou desvincular explicitamente antes de tentar excluir em massa.
    """
    results: List[MediaBulkActionItemResult] = []
    for media_id in payload.media_ids:
        media, error = _bulk_authorize_media(db, media_id=media_id, current_user=current_user)
        if error:
            results.append(MediaBulkActionItemResult(media_id=media_id, success=False, reason=error))
            continue

        refs = crud_media.get_in_use_references(db, media_id=media_id)
        if refs["campaign_playlist_items"] > 0:
            results.append(MediaBulkActionItemResult(
                media_id=media_id,
                success=False,
                reason=f"Em uso em {refs['campaign_playlist_items']} item(s) de playlist de campanha",
            ))
            continue

        used_campaigns = _campaigns_using_media(db, media_id=media_id)
        if used_campaigns:
            results.append(MediaBulkActionItemResult(
                media_id=media_id,
                success=False,
                reason=f"Em uso em {len(used_campaigns)} campanha(s) (vínculo legado)",
            ))
            continue

        db.query(PlaybackLog).filter(PlaybackLog.media_id == media_id).delete(synchronize_session=False)
        db.query(ViewReport).filter(ViewReport.media_id == media_id).delete(synchronize_session=False)

        if media.file_url and media.file_url.startswith("/uploads/"):
            file_path = media.file_url[1:]
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        crud_media.remove(db, id=media_id)
        results.append(MediaBulkActionItemResult(media_id=media_id, success=True))

    succeeded = sum(1 for r in results if r.success)
    return MediaBulkActionResponse(
        requested=len(payload.media_ids),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


@router.get("/statistics/overview")
def get_media_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas das mídias
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_media.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/available/list", response_model=List[MediaResponse])
def get_available_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias disponíveis para uso
    """
    media_list = crud_media.get_available(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/processing/list", response_model=List[MediaResponse])
def get_processing_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias em processamento
    """
    media_list = crud_media.get_processing(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/error/list", response_model=List[MediaResponse])
def get_error_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias com erro
    """
    media_list = crud_media.get_with_error(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/by-type/{media_type}", response_model=List[MediaResponse])
def get_media_by_type(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_type: MediaTypeEnum,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias por tipo
    """
    media_list = crud_media.get_by_type(db, media_type=media_type)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/by-category/{category}", response_model=List[MediaResponse])
def get_media_by_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias por categoria
    """
    media_list = crud_media.get_by_category(db, category=category)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]
