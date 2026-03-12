"""
Email Processor — Nutrio+ Support with 1-Hour Reply Delay
==========================================================
Flow:
  1. Fetch unread emails
  2. AI analyses each one (with Nutrio knowledge baked in)
  3. AUTO_REPLY → queued for 1 hour (looks human, not instant bot)
  4. ESCALATE   → added to escalation queue for you to handle
  5. Every cycle also checks for due queued replies and sends them
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logger import get_logger
import database
import ai_handler
import escalation_queue

logger = get_logger("email_processor")

FOLDER_REPLIED   = "AI-Replied"
FOLDER_ESCALATED = "Needs-Human"
REPLY_DELAY_HOURS = 1.0   # how long to wait before sending auto-reply


def process_inbox(zoho) -> dict:
    """Main cycle — reads inbox, classifies emails, queues replies or escalates."""
    stats = {"processed": 0, "queued": 0, "escalated": 0, "sent": 0, "errors": 0}

    # ── Step 1: Send any replies that are now due ──────────────────
    sent = _flush_pending_replies(zoho)
    stats["sent"] = sent

    # ── Step 2: Read new unread emails ────────────────────────────
    emails = zoho.get_unread_emails()
    if not emails:
        logger.info("Inbox clear.")
        return stats

    for email in emails:
        uid = email["uid"]

        # Skip if already processed OR already queued for reply
        if database.is_processed(uid) or database.is_reply_pending(uid):
            logger.debug(f"Already handled UID {uid} — skipping.")
            continue

        logger.info(f"Analysing — '{email['subject']}' from {email['sender']}")
        stats["processed"] += 1

        try:
            email["thread_context"] = zoho.get_thread_context(email["subject"], email["sender"])
            decision   = ai_handler.analyse_email(email)
            action     = decision["action"]
            confidence = decision.get("confidence", 0.0)

            if action == "AUTO_REPLY":
                # Queue reply — don't send immediately (1 hour delay)
                database.queue_reply(
                    uid=uid,
                    message_id=uid,
                    sender=email["sender"],
                    subject=email["subject"],
                    reply_text=decision["reply_text"],
                    received_at=email["received_at"],
                    delay_hours=REPLY_DELAY_HOURS,
                )
                # Record in DB as "queued" so we don't re-process
                database.record_email(
                    message_id=uid,
                    thread_id=uid,
                    sender=email["sender"],
                    subject=email["subject"],
                    received_at=email["received_at"],
                    action="queued",
                    ai_confidence=confidence,
                    reply_preview=decision["reply_text"],
                )
                zoho.mark_as_read(uid)
                stats["queued"] += 1
                logger.info(f"  Queued reply (sends in {REPLY_DELAY_HOURS}h) — conf={confidence:.2f}")

            elif action == "ESCALATE_TO_HUMAN":
                reason = decision.get("escalation_reason", "No reason given")
                escalation_queue.add_to_queue(email, reason=reason, confidence=confidence)
                zoho.mark_as_read(uid)
                zoho.move_to_folder(uid, FOLDER_ESCALATED)
                database.record_email(
                    message_id=uid,
                    thread_id=uid,
                    sender=email["sender"],
                    subject=email["subject"],
                    received_at=email["received_at"],
                    action="escalated",
                    ai_confidence=confidence,
                    escalation_reason=reason,
                )
                stats["escalated"] += 1

        except Exception as e:
            logger.error(f"Error on '{email['subject']}': {e}", exc_info=True)
            database.record_email(
                message_id=uid, thread_id=uid,
                sender=email.get("sender", ""), subject=email.get("subject", ""),
                received_at=email.get("received_at", ""), action="error", error=str(e),
            )
            stats["errors"] += 1

    logger.info(
        f"Cycle — processed:{stats['processed']} queued:{stats['queued']} "
        f"sent:{stats['sent']} escalated:{stats['escalated']} errors:{stats['errors']}"
    )
    return stats


def _flush_pending_replies(zoho) -> int:
    """Send all queued replies whose 1-hour wait is up."""
    due = database.get_due_replies()
    sent_count = 0

    for row in due:
        try:
            zoho.send_reply(
                to=row["sender"],
                subject=row["subject"],
                body=row["reply_text"],
            )
            database.mark_reply_sent(row["message_id"])

            # Move original email to AI-Replied folder
            try:
                zoho.move_to_folder(row["uid"], "AI-Replied")
            except Exception:
                pass  # non-critical

            sent_count += 1
            logger.info(f"Sent delayed reply → {row['sender']} | {row['subject']}")

        except Exception as e:
            logger.error(f"Failed to send queued reply to {row['sender']}: {e}")

    if sent_count:
        logger.info(f"Flushed {sent_count} queued reply/replies.")
    return sent_count
