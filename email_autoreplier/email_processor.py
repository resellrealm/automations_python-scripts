"""
Email Processor
Core logic: fetch unread → AI classify → reply or escalate.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logger import get_logger
import database
import ai_handler
import escalation_queue

logger = get_logger("email_processor")

# Folders created in Zoho to organise processed mail
FOLDER_REPLIED   = "AI-Replied"
FOLDER_ESCALATED = "Needs-Human"


def process_inbox(zoho) -> dict:
    """
    Main cycle:
    1. Fetch unread emails
    2. Skip already-processed ones
    3. AI decision → auto-reply or escalate

    Returns stats dict.
    """
    stats = {"processed": 0, "replied": 0, "escalated": 0, "errors": 0}

    emails = zoho.get_unread_emails()
    if not emails:
        logger.info("Inbox clear — nothing to process.")
        return stats

    for email in emails:
        uid = email["uid"]

        if database.is_processed(uid):
            logger.debug(f"Already processed UID {uid} — skipping.")
            continue

        logger.info(f"Processing — '{email['subject']}' from {email['sender']}")
        stats["processed"] += 1

        try:
            # Get thread history for AI context
            email["thread_context"] = zoho.get_thread_context(
                email["subject"], email["sender"]
            )

            decision   = ai_handler.analyse_email(email)
            action     = decision["action"]
            confidence = decision.get("confidence", 0.0)

            if action == "AUTO_REPLY":
                reply_text = decision["reply_text"]

                zoho.send_reply(
                    to=email["sender"],
                    subject=email["subject"],
                    body=reply_text,
                    reply_to_uid=uid,
                )
                zoho.mark_as_read(uid)
                zoho.move_to_folder(uid, FOLDER_REPLIED)

                database.record_email(
                    message_id=uid,
                    thread_id=uid,
                    sender=email["sender"],
                    subject=email["subject"],
                    received_at=email["received_at"],
                    action="replied",
                    ai_confidence=confidence,
                    reply_preview=reply_text,
                )
                stats["replied"] += 1
                logger.info(f"  Auto-replied (confidence={confidence:.2f})")

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
                message_id=uid,
                thread_id=uid,
                sender=email.get("sender", ""),
                subject=email.get("subject", ""),
                received_at=email.get("received_at", ""),
                action="error",
                error=str(e),
            )
            stats["errors"] += 1

    logger.info(
        f"Cycle done — processed:{stats['processed']} "
        f"replied:{stats['replied']} escalated:{stats['escalated']} errors:{stats['errors']}"
    )
    return stats
