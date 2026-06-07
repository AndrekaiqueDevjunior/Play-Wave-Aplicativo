from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_CONNECT_TIMEOUT_SECONDS: int = 5
    AUTO_CREATE_TABLES: bool = False

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: float = 2.0
    REDIS_SOCKET_CONNECT_TIMEOUT: float = 2.0

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_USER: Optional[str] = "guest"
    RABBITMQ_PASSWORD: Optional[str] = "guest"

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # CORS — valor padrão para dev; em prod sobrescreva via .env
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # App metadata (informational)
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    PROJECT_NAME: str = "Play Wave API"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    APP_TIMEZONE: str = "America/Sao_Paulo"

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 104857600  # 100 MB

    # Inicialização do banco
    ADMIN_INITIAL_EMAIL: str = "admin@playwave.com"
    ADMIN_INITIAL_PASSWORD: str = "Troque@123!"
    OPERATOR_INITIAL_EMAIL: str = "operador@playwave.com"
    OPERATOR_INITIAL_PASSWORD: str = "Troque@456!"

    def get_allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        # O .env carrega chaves informativas (ex.: URL_HOST) usadas por outras
        # ferramentas; ignorar extras evita quebrar o boot por variáveis desconhecidas.
        extra = "ignore"


settings = Settings()

_redis_client = None


def get_redis_client():
    """Get shared Redis client connection.

    redis-py clients are thread-safe and maintain an internal connection pool.
    Reusing one client per process avoids reconnect overhead on hot player paths.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis

        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            health_check_interval=30,
            retry_on_timeout=True,
        )
        return _redis_client
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return None


def get_async_redis_client():
    """Get async Redis client connection for use inside async generators (SSE)."""
    try:
        import redis.asyncio as aioredis
        return aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            health_check_interval=30,
            retry_on_timeout=True,
        )
    except Exception as e:
        print(f"Failed to connect to Redis (async): {e}")
        return None
