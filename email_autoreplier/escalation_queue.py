"""
Escalation Queue
Stores emails that require human review in a JSON file.
You check this file when you want to see what needs your attention.

Queue file: escalation_queue.json (in this folder)
Each entry has a 'status' field: "pending" or "resolved"
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import Config
from shared.logger import get_logger

logger = get_logger("escalation_queue")


def _load_queue() -> List[dict]:
    """Load the current queue from disk."""
    if not Path(Config.ESCALATION_FILE).exists():
        return []
    try:
        with open(Config.ESCALATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_queue(queue: List[dict]):
    """Write the queue back to disk."""
    with open(Config.ESCALATION_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def add_to_queue(
    email: dict,
    reason: str,
    confidence: Optional[float] = None,
):
    """
    Add an email to the escalation queue.

    Args:
        email:      The email dict from GmailClient
        reason:     Why the AI flagged this for human review
        confidence: AI confidence score (0.0–1.0)
    """
    queue = _load_queue()

    entry = {
        "id": email["message_id"],
        "thread_id": email["thread_id"],
        "sender": email["sender"],
        "subject": email["subject"],
        "snippet": email.get("snippet", "")[:300],
        "received_at": email["received_at"],
        "escalation_reason": reason,
        "ai_confidence": confidence,
        "queued_at": datetime.utcnow().isoformat(),
        "status": "pending",   # pending | resolved
        "human_notes": None,
    }

    # Avoid duplicate entries
    existing_ids = {e["id"] for e in queue}
    if email["message_id"] not in existing_ids:
        queue.append(entry)
        _save_queue(queue)
        logger.warning(
            f"ESCALATED — '{email['subject']}' from {email['sender']} | Reason: {reason}"
        )
        _print_escalation_alert(entry)
    else:
        logger.debug(f"Email {email['message_id']} already in escalation queue.")


def get_pending() -> List[dict]:
    """Return all pending (unresolved) escalations."""
    return [e for e in _load_queue() if e.get("status") == "pending"]


def mark_resolved(email_id: str, notes: Optional[str] = None):
    """Mark an escalated email as resolved."""
    queue = _load_queue()
    for entry in queue:
        if entry["id"] == email_id:
            entry["status"] = "resolved"
            entry["resolved_at"] = datetime.utcnow().isoformat()
            if notes:
                entry["human_notes"] = notes
            break
    _save_queue(queue)
    logger.info(f"Marked escalation {email_id} as resolved.")


def print_pending_summary():
    """Print a human-readable summary of all pending escalations to the console."""
    pending = get_pending()
    if not pending:
        print("\n  No pending escalations.\n")
        return

    print(f"\n{'='*60}")
    print(f"  ESCALATION QUEUE — {len(pending)} pending")
    print(f"{'='*60}")
    for i, entry in enumerate(pending, 1):
        print(f"\n  [{i}] From:    {entry['sender']}")
        print(f"       Subject: {entry['subject']}")
        print(f"       Reason:  {entry['escalation_reason']}")
        print(f"       Queued:  {entry['queued_at'][:19]}")
        print(f"       Snippet: {entry['snippet'][:100]}...")
    print(f"\n{'='*60}\n")


def _print_escalation_alert(entry: dict):
    """Print a bold alert to the console when a new escalation is added."""
    print(f"\n{'!'*60}")
    print(f"  ACTION REQUIRED — New email needs your attention:")
    print(f"  From:    {entry['sender']}")
    print(f"  Subject: {entry['subject']}")
    print(f"  Reason:  {entry['escalation_reason']}")
    print(f"  File:    {Config.ESCALATION_FILE}")
    print(f"{'!'*60}\n")
