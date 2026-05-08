import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import event
from api.v1 import (
    auth_router, devices_router, campaigns_router, media_router,
    users_router, locations_router, user_logs_router,
    tracks_router, playlists_router,
    dashboard_router, reports_router, schedule_router,
    monitoring_router, tenants_router, plans_router,
)
from core.database import engine, Base
from core.config import settings
from core.models import Device

Base.metadata.create_all(bind=engine)

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


@app.exception_handler(ResponseValidationError)
async def response_validation_error_handler(request: Request, exc: ResponseValidationError):
    print(f"[ResponseValidationError] {request.method} {request.url}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro de serialização da resposta", "errors": str(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"[UnhandledException] {request.method} {request.url}: {repr(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro interno: {repr(exc)}"},
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
app.include_router(playlists_router)

# New routers
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(schedule_router)
app.include_router(monitoring_router)
app.include_router(tenants_router)
app.include_router(plans_router)


@app.get("/")
def root():
    return {"message": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
