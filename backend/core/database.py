from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings


def _engine_kwargs() -> dict:
    url = make_url(settings.DATABASE_URL)
    if url.drivername.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}

    kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": settings.DB_POOL_RECYCLE_SECONDS,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
    }
    if url.get_backend_name() == "postgresql":
        kwargs["connect_args"] = {"connect_timeout": settings.DB_CONNECT_TIMEOUT_SECONDS}
    return kwargs


engine = create_engine(settings.DATABASE_URL, **_engine_kwargs())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
