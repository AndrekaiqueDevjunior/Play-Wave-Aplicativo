import mimetypes
import os
import re
import traceback
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy import event, text
from sqlalchemy.orm import configure_mappers
from api.v1.auth import router as auth_router
from api.v1.devices import router as devices_router
from api.v1.campaigns import router as campaigns_router
from api.v1.media import router as media_router
from api.v1.users import router as users_router
from api.v1.locations import router as locations_router
from api.v1.user_logs import router as user_logs_router
from api.v1.audio.tracks import router as tracks_router
from api.v1.audio.categories import router as categories_router
from api.v1.audio.playlists import router as playlists_router
from api.v1.audio.devices import router as audio_devices_router
from api.v1.audio.folders import router as audio_folders_router
from api.v1.audio.spots import router as spots_router
from api.v1.audio.events import router as audio_events_router
from api.v1.dashboard import router as dashboard_router
from api.v1.reports import router as reports_router
from api.v1.schedule import router as schedule_router
from api.v1.monitoring import router as monitoring_router
from api.v1.tenants import router as tenants_router
from api.v1.plans import router as plans_router
from api.v1.player_schedule import router as player_schedule_router
from core.database import engine, Base
from core.config import settings
from core.models import Device

if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

UPLOADS_DIR = Path("uploads").resolve()
RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")

# Registrar event listeners para limpar strings vazias de UUID
@event.listens_for(Device, 'before_insert')
@event.listens_for(Device, 'before_update')
def clean_empty_uuid_strings(mapper, connection, target):
    if hasattr(target, 'audio_playlist_id') and target.audio_playlist_id == "":
        target.audio_playlist_id = None
    if hasattr(target, 'current_campaign_id') and target.current_campaign_id == "":
        target.current_campaign_id = None

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para sistema de Digital Signage",
    version=settings.VERSION,
)


@app.on_event("startup")
def warmup_database() -> None:
    try:
        configure_mappers()
    except Exception as exc:
        print(f"[startup] SQLAlchemy mapper warmup failed: {exc}")

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"[startup] database warmup failed: {exc}")


os.makedirs(UPLOADS_DIR, exist_ok=True)


def _resolve_upload_path(file_path: str) -> Path:
    path = (UPLOADS_DIR / file_path).resolve()
    if not path.is_relative_to(UPLOADS_DIR) or not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return path


def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
    match = RANGE_RE.match(range_header.strip())
    if not match:
        raise HTTPException(
            status_code=416,
            detail="Range inválido",
            headers={"Content-Range": f"bytes */{file_size}", "Accept-Ranges": "bytes"},
        )

    start_text, end_text = match.groups()
    if not start_text and not end_text:
        raise HTTPException(
            status_code=416,
            detail="Range inválido",
            headers={"Content-Range": f"bytes */{file_size}", "Accept-Ranges": "bytes"},
        )

    if start_text:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
    else:
        suffix_length = int(end_text)
        if suffix_length <= 0:
            raise HTTPException(
                status_code=416,
                detail="Range inválido",
                headers={"Content-Range": f"bytes */{file_size}", "Accept-Ranges": "bytes"},
            )
        start = max(file_size - suffix_length, 0)
        end = file_size - 1

    end = min(end, file_size - 1)
    if start >= file_size or end < start:
        raise HTTPException(
            status_code=416,
            detail="Range fora do arquivo",
            headers={"Content-Range": f"bytes */{file_size}", "Accept-Ranges": "bytes"},
        )
    return start, end


def _iter_file_range(path: Path, start: int, end: int, chunk_size: int = 1024 * 1024):
    with path.open("rb") as file:
        file.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = file.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@app.api_route("/uploads/{file_path:path}", methods=["GET", "HEAD"])
async def serve_upload(
    file_path: str,
    request: Request,
    range_header: str | None = Header(default=None, alias="Range"),
):
    """Serve mídias com suporte a Range Requests para Android WebView."""
    path = _resolve_upload_path(file_path)
    file_size = path.stat().st_size
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    base_headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=604800",
    }

    if request.method == "HEAD":
        return Response(
            status_code=200,
            media_type=media_type,
            headers={**base_headers, "Content-Length": str(file_size)},
        )

    if not range_header:
        return FileResponse(path, media_type=media_type, headers=base_headers)

    start, end = _parse_range(range_header, file_size)
    content_length = end - start + 1
    headers = {
        **base_headers,
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
    }
    return StreamingResponse(
        _iter_file_range(path, start, end),
        status_code=206,
        media_type=media_type,
        headers=headers,
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_error_handler(request: Request, exc: ResponseValidationError):
    print(f"[ResponseValidationError] {request.method} {request.url}")
    print(traceback.format_exc())
    detail = "Erro de serialização da resposta"
    if settings.DEBUG:
        detail = f"{detail}: {exc.errors()}"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"[UnhandledException] {request.method} {request.url}: {repr(exc)}")
    print(traceback.format_exc())
    detail = "Erro interno do servidor"
    if settings.DEBUG:
        detail = f"Erro interno: {repr(exc)}"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routers
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(campaigns_router)
app.include_router(media_router)
app.include_router(users_router)
app.include_router(locations_router)
app.include_router(user_logs_router)
app.include_router(tracks_router)
app.include_router(categories_router)
app.include_router(playlists_router)
app.include_router(audio_devices_router)
app.include_router(audio_folders_router)
app.include_router(spots_router)
app.include_router(audio_events_router)

# New routers
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(schedule_router)
app.include_router(monitoring_router)
app.include_router(tenants_router)
app.include_router(plans_router)
app.include_router(player_schedule_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
