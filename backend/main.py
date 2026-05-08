from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import (
    auth_router, devices_router, campaigns_router, media_router,
    users_router, locations_router, user_logs_router,
    tracks_router, playlists_router
)
from core.database import engine, Base
from core.config import settings

# Criar tabelas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Play Wave API",
    description="API para sistema de Digital Signage",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # URLs do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(campaigns_router)
app.include_router(media_router)
app.include_router(users_router)
app.include_router(locations_router)
app.include_router(user_logs_router)
app.include_router(tracks_router)
app.include_router(playlists_router)


@app.get("/")
def root():
    return {"message": "Play Wave API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
