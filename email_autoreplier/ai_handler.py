"""
AI Handler
Uses Kimi AI to analyse incoming emails and decide:
  - AUTO_REPLY  → generate a reply and send it
  - ESCALATE    → flag for human review with a reason

The AI also generates the reply text if action is AUTO_REPLY.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.kimi_client import KimiClient
from shared.logger import get_logger
from config import Config

logger = get_logger("ai_handler")

# Compact system prompt — fewer tokens, same accuracy
SYSTEM_PROMPT = """Email assistant for {name} ({role}). Tone: {tone}.
AUTO_REPLY: questions, FAQs, scheduling, follow-ups, feedback.
ESCALATE_TO_HUMAN: legal, complaints, refunds, urgent, personal, hostile.
Reply as {name}. JSON only: {{"action":"AUTO_REPLY"|"ESCALATE_TO_HUMAN","reply_text":str|null,"escalation_reason":str|null,"confidence":0-1}}"""


def analyse_email(email: dict) -> dict:
    """
    Analyse an email and return an action decision.

    Returns:
        {
            "action": "AUTO_REPLY" | "ESCALATE_TO_HUMAN",
            "reply_text": str | None,
            "escalation_reason": str | None,
            "confidence": float
        }
    """
    client = KimiClient()

    system_prompt = SYSTEM_PROMPT.format(
        name=Config.YOUR_NAME,
        role=Config.YOUR_ROLE,
        tone=Config.REPLY_TONE,
    )

    # Keep body short — 1200 chars is enough for classification + reply
    body = email['body'][:1200].rsplit(' ', 1)[0]
    thread = _format_thread_context(email.get('thread_context', ''))

    user_message = f"From:{email['sender']}\nSubject:{email['subject']}\n\n{body}{thread}"

    logger.debug(f"Sending email to Kimi AI — subject: {email['subject']}")

    try:
        result = client.chat_json(user_message, system_prompt=system_prompt, temperature=0.3, max_tokens=500)

        # Validate fields
        if "action" not in result:
            raise ValueError("Missing 'action' field in AI response")

        action = result["action"]
        if action not in ("AUTO_REPLY", "ESCALATE_TO_HUMAN"):
            raise ValueError(f"Unknown action: {action}")

        if action == "AUTO_REPLY" and not result.get("reply_text"):
            raise ValueError("AUTO_REPLY action but no reply_text provided")

        logger.info(
            f"AI decision: {action} "
            f"(confidence={result.get('confidence', '?')}) "
            f"— subject: {email['subject']}"
        )
        return result

    except Exception as e:
        logger.error(f"AI handler error: {e}")
        # Safe fallback: escalate to human
        return {
            "action": "ESCALATE_TO_HUMAN",
            "reply_text": None,
            "escalation_reason": f"AI processing error: {str(e)}",
            "confidence": 0.0,
        }


def _format_thread_context(context: str) -> str:
    if not context:
        return ""
    return f"\nCONTEXT:\n{context[:600]}"
