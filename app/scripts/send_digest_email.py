# Stage 6: build the email digest and actually send it
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.digest.emailer import send_email_to_self
from app.scripts.generate_email_intro import run as build_digest


def run(hours: int = 24) -> None:
    digest = build_digest(hours=hours)
    subject = f"Your AI Digest - {digest.date.strftime('%B %d, %Y')}"
    send_email_to_self(subject, digest.to_html())


if __name__ == "__main__":
    run(hours=24)
