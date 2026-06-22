"""Serviço de envio de e-mail (SPEC 019 — convite de usuário e reset de senha).

Quando SMTP_HOST não está configurado (ambiente dev/sem credenciais reais),
o envio cai em modo de log: o conteúdo do e-mail é registrado no logger em
vez de falhar a operação que originou o envio (criação de usuário, reenvio
de convite, solicitação de reset de senha).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings

log = logging.getLogger("playwave.email_service")


def _send(to_email: str, subject: str, html_body: str) -> bool:
    if not settings.SMTP_HOST:
        log.info(
            "SMTP não configurado — e-mail não enviado (modo log). to=%s subject=%s body=%s",
            to_email, subject, html_body,
        )
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], message.as_string())
        log.info("E-mail enviado com sucesso. to=%s subject=%s", to_email, subject)
        return True
    except Exception:
        log.exception("Falha ao enviar e-mail. to=%s subject=%s", to_email, subject)
        return False


def send_invite_email(to_email: str, name: str, invite_token: str) -> bool:
    link = f"{settings.FRONTEND_BASE_URL}/aceitar-convite?token={invite_token}"
    subject = "Você foi convidado para o Play Wave"
    body = (
        f"<p>Olá, {name}.</p>"
        f"<p>Você foi convidado a acessar o Play Wave. "
        f'Clique no link abaixo para definir sua senha e ativar sua conta:</p>'
        f'<p><a href="{link}">{link}</a></p>'
        f"<p>Este link expira em {settings.INVITE_TOKEN_EXPIRE_HOURS} horas.</p>"
    )
    return _send(to_email, subject, body)


def send_password_reset_email(to_email: str, name: str, reset_token: str) -> bool:
    link = f"{settings.FRONTEND_BASE_URL}/redefinir-senha?token={reset_token}"
    subject = "Redefinição de senha — Play Wave"
    body = (
        f"<p>Olá, {name}.</p>"
        f"<p>Recebemos uma solicitação para redefinir sua senha. "
        f'Clique no link abaixo para escolher uma nova senha:</p>'
        f'<p><a href="{link}">{link}</a></p>'
        f"<p>Este link expira em {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} horas. "
        f"Se você não solicitou isso, ignore este e-mail.</p>"
    )
    return _send(to_email, subject, body)
