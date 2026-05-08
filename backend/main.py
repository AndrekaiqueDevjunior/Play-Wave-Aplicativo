from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import (
    auth_router, devices_router, campaigns_router, media_router,
    users_router, locations_router, user_logs_router,
    tracks_router, playlists_router,
    dashboard_router, reports_router, schedule_router,
    monitoring_router, tenants_router, plans_router,
)
from core.database import engine, Base
from core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para sistema de Digital Signage",
    version=settings.VERSION,
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
