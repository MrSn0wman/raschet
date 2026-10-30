"""POST /api/feedback — обратная связь.

Поток: honeypot → rate limit (10/час по IP) → сохранить в SQLite → отправить
email через SMTP (если настроен). В логи пишем только метаданные (id, факт
отправки), никогда — текст сообщения.
"""
import asyncio
import logging
import os
import re
import smtplib
import time
from email.message import EmailMessage
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

import db

log = logging.getLogger("raschet.feedback")
router = APIRouter()

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
LIMIT_PER_HOUR = 10
RATE_WINDOW = 3600


class FeedbackIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=254)
    topic: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=5000)
    page: Optional[str] = Field(default=None, max_length=200)
    website: Optional[str] = Field(default=None, max_length=200)  # honeypot для ботов

    @field_validator("name", "topic", "message", "page", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v

    @field_validator("email")
    @classmethod
    def _check_email(cls, v):
        if v is None:
            return None
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email")
        return v


def _save(item: FeedbackIn, ip_hash: str) -> int:
    conn = db.connect()
    try:
        cur = conn.execute(
            "INSERT INTO feedback (created_at, name, email, topic, message, page, ip_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                int(time.time()),
                item.name,
                item.email,
                item.topic,
                item.message,
                item.page,
                ip_hash,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _mark_emailed(feedback_id: int) -> None:
    conn = db.connect()
    try:
        conn.execute("UPDATE feedback SET emailed = 1 WHERE id = ?", (feedback_id,))
        conn.commit()
    finally:
        conn.close()


def _header_safe(value: Optional[str]) -> str:
    """Убрать переводы строк — защита от инъекции в заголовки письма."""
    return (value or "").replace("\r", " ").replace("\n", " ").strip()


def _send_mail(item: FeedbackIn) -> None:
    """Отправка письма. Бросает исключение при ошибке — ловит вызывающий код."""
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        log.info("SMTP not configured, feedback stored in DB only")
        return
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    mail_from = (os.environ.get("SMTP_FROM", "").strip() or user) or "noreply@localhost"
    mail_to = os.environ.get("FEEDBACK_TO", "").strip()
    if not mail_to:
        log.warning("FEEDBACK_TO is empty, email skipped")
        return

    msg = EmailMessage()
    msg["Subject"] = _header_safe("[Расчёт.net] " + item.topic)[:200]
    msg["From"] = mail_from
    msg["To"] = mail_to
    if item.email:
        msg["Reply-To"] = _header_safe(item.email)
    body = (
        "Новое сообщение с формы обратной связи\n"
        "======================================\n"
        "Имя: %s\n"
        "Email: %s\n"
        "Страница: %s\n"
        "Тема: %s\n\n"
        "%s\n"
    ) % (
        item.name or "—",
        item.email or "—",
        item.page or "—",
        item.topic,
        item.message,
    )
    msg.set_content(body)

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=15) as smtp:
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)


@router.post("/api/feedback")
async def submit_feedback(item: FeedbackIn, request: Request):
    # Honeypot: люди это поле не видят и не заполняют. Отвечаем как обычно,
    # но ничего не сохраняем и не шлём.
    if item.website:
        return {"ok": True}

    ip = request.client.host if request.client else "unknown"
    key = db.client_key(ip)
    allowed = await asyncio.to_thread(
        db.rate_limit, "feedback", key, LIMIT_PER_HOUR, RATE_WINDOW
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="too many requests")

    feedback_id = await asyncio.to_thread(_save, item, key)
    try:
        await asyncio.to_thread(_send_mail, item)
        await asyncio.to_thread(_mark_emailed, feedback_id)
    except Exception:
        # Содержимое сообщения в лог не попадает — только id записи.
        log.exception("feedback email failed, id=%s", feedback_id)
    return {"ok": True}
