# Pipeline stage 6: build the email digest and actually send it
from __future__ import annotations

from app.db.models import Digest
from app.email.emailer import send_email_to_self
from app.pipeline.build_email import run as build_digest


def run(hours: int = 24, digests: list[Digest] | None = None) -> None:
    digest = build_digest(hours=hours, digests=digests)
    subject = f"Your AI Digest - {digest.date.strftime('%B %d, %Y')}"
    send_email_to_self(subject, digest.to_html())
