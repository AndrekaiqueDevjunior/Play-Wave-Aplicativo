from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from core.database import get_db
from core.models import User, UserLog, UserLogAction
from core.schemas import UserLogin, Token
from core.schemas_completos import (
    UserAcceptInviteRequest, PasswordForgotRequest, PasswordResetConfirmRequest,
)
from core.auth import (
    verify_password, create_access_token, get_password_hash,
    generate_secure_token, token_expiry,
)
from core.dependencies import get_current_user
from core.config import settings
from services.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status == "pending_invite":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Convite pendente: defina sua senha pelo link enviado por e-mail antes de entrar",
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.post("/accept-invite", response_model=Token)
def accept_invite(payload: UserAcceptInviteRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.invite_token == payload.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Convite inválido",
        )

    if not user.invite_expires_at or user.invite_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Convite expirado. Solicite o reenvio a um administrador",
        )

    user.password_hash = get_password_hash(payload.password)
    user.account_status = "active"
    user.invite_token = None
    user.invite_expires_at = None
    db.add(user)
    db.add(UserLog(
        target_user_id=user.id,
        target_user_email=user.email,
        action=UserLogAction.ACCEPT_INVITE,
        performed_by=user.email,
        tenant_id=user.tenant_id,
    ))
    db.commit()
    db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer", user=user)


@router.post("/forgot-password")
def forgot_password(payload: PasswordForgotRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Resposta genérica independente do e-mail existir, para não revelar
    # quais e-mails estão cadastrados (enumeração de usuários).
    if user and user.password_hash:
        user.password_reset_token = generate_secure_token()
        user.password_reset_expires_at = token_expiry(settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        db.add(user)
        db.commit()
        send_password_reset_email(user.email, user.name, user.password_reset_token)

    return {"message": "Se o e-mail existir, enviaremos instruções para redefinir a senha"}


@router.post("/reset-password", response_model=Token)
def reset_password(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == payload.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de redefinição inválido",
        )

    if not user.password_reset_expires_at or user.password_reset_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de redefinição expirado. Solicite novamente",
        )

    user.password_hash = get_password_hash(payload.password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.add(user)
    db.add(UserLog(
        target_user_id=user.id,
        target_user_email=user.email,
        action=UserLogAction.RESET_PASSWORD,
        performed_by=user.email,
        tenant_id=user.tenant_id,
    ))
    db.commit()
    db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer", user=user)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout():
    # No backend, o logout é apenas remover o token no frontend
    # Podemos adicionar blacklist de tokens se necessário
    return {"message": "Logout realizado"}
