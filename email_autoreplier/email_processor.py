"""
Email Processor
Core logic: fetch unread emails → classify → reply or escalate.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import re
from shared.logger import get_logger
import database
import ai_handler
import escalation_queue

logger = get_logger("email_processor")


def _extract_email_address(sender: str) -> str:
    """Extract plain email from 'Name <email@example.com>' format."""
    match = re.search(r"<(.+?)>", sender)
    return match.group(1) if match else sender.strip()


def process_inbox(gmail_client) -> dict:
    """
    Main processing cycle:
    1. Fetch unread emails
    2. Skip already-processed ones
    3. For each new email: ask AI → reply or escalate

    Returns stats: {processed, replied, escalated, errors}
    """
    stats = {"processed": 0, "replied": 0, "escalated": 0, "errors": 0}

    emails = gmail_client.get_unread_emails()

    if not emails:
        logger.info("No unread emails to process.")
        return stats

    for email in emails:
        msg_id = email["message_id"]

        if database.is_processed(msg_id):
            logger.debug(f"Skipping already-processed email: {email['subject']}")
            continue

        logger.info(f"Processing — '{email['subject']}' from {email['sender']}")
        stats["processed"] += 1

        try:
            # Attach thread context so AI can see the conversation history
            email["thread_context"] = gmail_client.get_thread_context(email["thread_id"])

            # Ask Kimi AI what to do
            decision = ai_handler.analyse_email(email)
            action = decision["action"]
            confidence = decision.get("confidence", 0.0)

            if action == "AUTO_REPLY":
                reply_text = decision["reply_text"]
                sender_address = _extract_email_address(email["sender"])

                gmail_client.send_reply(
                    original_message_id=msg_id,
                    thread_id=email["thread_id"],
                    to=sender_address,
                    subject=email["subject"],
                    body=reply_text,
                )
                gmail_client.mark_as_read(msg_id)
                gmail_client.apply_label(msg_id, "AI-Replied")

                database.record_email(
                    message_id=msg_id,
                    thread_id=email["thread_id"],
                    sender=email["sender"],
                    subject=email["subject"],
                    received_at=email["received_at"],
                    action="replied",
                    ai_confidence=confidence,
                    reply_preview=reply_text,
                )
                stats["replied"] += 1
                logger.info(f"Auto-replied to '{email['subject']}' (confidence={confidence:.2f})")

            elif action == "ESCALATE_TO_HUMAN":
                reason = decision.get("escalation_reason", "No reason given")

                escalation_queue.add_to_queue(email, reason=reason, confidence=confidence)
                gmail_client.apply_label(msg_id, "Needs-Human")
                gmail_client.mark_as_read(msg_id)

                database.record_email(
                    message_id=msg_id,
                    thread_id=email["thread_id"],
                    sender=email["sender"],
                    subject=email["subject"],
                    received_at=email["received_at"],
                    action="escalated",
                    ai_confidence=confidence,
                    escalation_reason=reason,
                )
                stats["escalated"] += 1

        except Exception as e:
            logger.error(f"Error processing email '{email['subject']}': {e}", exc_info=True)
            database.record_email(
                message_id=msg_id,
                thread_id=email.get("thread_id", ""),
                sender=email.get("sender", ""),
                subject=email.get("subject", ""),
                received_at=email.get("received_at", ""),
                action="error",
                error=str(e),
            )
            stats["errors"] += 1

    logger.info(
        f"Cycle complete — processed: {stats['processed']}, "
        f"replied: {stats['replied']}, escalated: {stats['escalated']}, "
        f"errors: {stats['errors']}"
    )
    return stats
