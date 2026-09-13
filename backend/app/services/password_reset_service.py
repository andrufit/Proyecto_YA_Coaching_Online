"""Opaque reset tokens: only their SHA-256 hashes are persisted."""
import hashlib
import logging
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlencode

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.password_reset import PasswordReset

logger = logging.getLogger(__name__)
GENERIC_MESSAGE = "Si el correo pertenece a una cuenta activa, recibirás un enlace para restablecer tu contraseña. Revisa también la carpeta de spam."


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def send_reset_email(recipient: str, token: str):
    # Fragment keeps the token out of HTTP access logs and Referer headers.
    link = settings.frontend_url.rstrip("/") + "/#" + urlencode({"reset_token": token})
    message = EmailMessage()
    message["Subject"] = "Restablece tu contraseña · Y&A Coaching Online"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(
        f"Recibimos una solicitud para cambiar tu contraseña.\n\n{link}\n\n"
        f"Este enlace vence en {settings.password_reset_minutes} minutos y solo puede usarse una vez. "
        "Si no lo solicitaste, ignora este mensaje."
    )
    context = ssl.create_default_context()
    smtp_class = smtplib.SMTP_SSL if settings.smtp_security == "ssl" else smtplib.SMTP
    kwargs = {"context": context} if settings.smtp_security == "ssl" else {}
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=10, **kwargs) as server:
        if settings.smtp_security == "starttls":
            server.starttls(context=context)
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def request_reset(db: Session, email: str):
    # Uniform availability check, independent of whether the address exists.
    if not settings.smtp_host or not settings.smtp_from or settings.smtp_security not in ("ssl", "starttls"):
        raise HTTPException(503, "La recuperación por correo todavía no está disponible. Contacta al administrador.")
    user = db.scalar(select(User).where(User.email == email.strip().lower()).with_for_update())
    if user is None or not user.is_active:
        return
    now = datetime.now(timezone.utc)
    record = db.scalar(select(PasswordReset).where(PasswordReset.user_id == user.id))
    # Persistent per-account cooldown works across server workers.
    if record is not None and now - utc(record.created_at) < timedelta(minutes=2):
        return
    token = secrets.token_urlsafe(32)
    if record is None:
        record = PasswordReset(user_id=user.id)
        db.add(record)
    record.token_hash = hashlib.sha256(token.encode()).hexdigest()
    record.created_at = now
    record.expires_at = now + timedelta(minutes=settings.password_reset_minutes)
    db.commit()
    return user.email, token


def deliver_reset(bind, recipient: str, token: str):
    # Runs after the HTTP response, so SMTP timing does not reveal accounts.
    try:
        send_reset_email(recipient, token)
    except (smtplib.SMTPException, OSError):
        digest = hashlib.sha256(token.encode()).hexdigest()
        with Session(bind) as db:
            db.execute(delete(PasswordReset).where(PasswordReset.token_hash == digest))
            db.commit()
        logger.warning("Password recovery email delivery failed")


def reset_password(db: Session, token: str, password: str):
    digest = hashlib.sha256(token.encode()).hexdigest()
    record = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == digest))
    if record is None:
        raise HTTPException(400, "El enlace no es válido o ya venció. Solicita uno nuevo.")
    user = db.scalar(select(User).where(User.id == record.user_id).with_for_update())
    if user is None or not user.is_active:
        raise HTTPException(400, "El enlace no es válido o ya venció. Solicita uno nuevo.")
    # Atomic consume prevents replay, including concurrent requests.
    consumed = db.execute(delete(PasswordReset).where(
        PasswordReset.id == record.id,
        PasswordReset.token_hash == digest,
        PasswordReset.expires_at > datetime.now(timezone.utc),
    ).execution_options(synchronize_session=False))
    if consumed.rowcount != 1:
        db.rollback()
        raise HTTPException(400, "El enlace no es válido o ya venció. Solicita uno nuevo.")
    try:
        user.hashed_password = hash_password(password)
        user.auth_version += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
