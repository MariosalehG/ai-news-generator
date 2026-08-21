# Daily pipeline: the one place to schedule (cron / Task Scheduler / etc).
# Runs every stage in order: ingest -> backfill content -> summarize -> curate & rank -> send email.
from __future__ import annotations

from app.pipeline import fetch_content, ingest, process_digest, send_email


def run(hours: int = 24) -> None:
    print(f"[1/4] Ingesting new items from the last {hours}h...")
    ingested = ingest.run(hours=hours)
    print(f"      {ingested}")

    print("[2/4] Backfilling content for any articles still missing it...")
    filled = fetch_content.run()
    print(f"      {filled}")

    print("[3/4] Summarizing articles that don't have a digest yet...")
    created = process_digest.run()
    print(f"      {len(created)} digest(s) created")

    print("[4/4] Ranking today's digests and sending the email...")
    send_email.run(hours=hours, digests=created)
    print("      Done.")
