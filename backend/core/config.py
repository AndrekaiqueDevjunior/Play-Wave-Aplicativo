from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

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


settings = Settings()
