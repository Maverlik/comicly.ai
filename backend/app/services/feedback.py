from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import Settings


class FeedbackDeliveryError(Exception):
    """Raised when configured feedback delivery fails."""


@dataclass(frozen=True)
class FeedbackAttachment:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class FeedbackMessage:
    name: str | None
    email: str | None
    message: str
    attachments: tuple[FeedbackAttachment, ...] = ()


class FeedbackMailer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.smtp_host
            and self.settings.smtp_username
            and self.settings.smtp_password
            and (self.settings.feedback_from_email or self.settings.smtp_username)
            and self.settings.feedback_recipient_email
        )

    async def send(self, feedback: FeedbackMessage) -> None:
        if not self.is_configured:
            raise FeedbackDeliveryError("Feedback email delivery is not configured.")
        await asyncio.to_thread(self._send_sync, feedback)

    def _send_sync(self, feedback: FeedbackMessage) -> None:
        settings = self.settings
        from_email = settings.feedback_from_email or settings.smtp_username
        assert from_email is not None

        message = EmailMessage()
        message["Subject"] = "Обратная связь Comicly"
        message["From"] = from_email
        message["To"] = settings.feedback_recipient_email
        if feedback.email:
            message["Reply-To"] = feedback.email

        body = [
            f"Имя: {feedback.name or 'не указано'}",
            f"Email: {feedback.email or 'не указан'}",
            "",
            feedback.message,
        ]
        message.set_content("\n".join(body))
        for attachment in feedback.attachments:
            maintype, _, subtype = attachment.content_type.partition("/")
            if not maintype or not subtype:
                maintype, subtype = "application", "octet-stream"
            message.add_attachment(
                attachment.content,
                maintype=maintype,
                subtype=subtype,
                filename=attachment.filename,
            )

        try:
            if settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=20,
                ) as smtp:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                    smtp.send_message(message)
                return

            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=20,
            ) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        except smtplib.SMTPException as exc:
            raise FeedbackDeliveryError("Feedback email delivery failed.") from exc
