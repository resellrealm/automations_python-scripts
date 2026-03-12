"""
AI Handler — Nutrio+ Support Edition
Analyses emails and decides: AUTO_REPLY or ESCALATE_TO_HUMAN.
Injects Nutrio+ knowledge base so the AI can answer product questions accurately.
Replies are queued with a 1-hour delay to appear human.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.kimi_client import KimiClient
from shared.logger import get_logger
from config import Config
from nutrio_kb.nutrio_info import get_short_context

logger = get_logger("ai_handler")

# Compact system prompt with Nutrio context baked in
_SYSTEM = (
    "You are a support agent for Nutrio+, an AI nutrition & fitness tracking iOS app. "
    "{nutrio_context}\n\n"
    "Tone: {tone}. Reply as {name} from Nutrio+ Support.\n"
    "AUTO_REPLY: general questions, FAQs, app help, subscription queries, troubleshooting.\n"
    "ESCALATE_TO_HUMAN: refund disputes, account deletion, GDPR, angry/distressed users, security issues, anything needing authority.\n"
    "Respond with JSON only: "
    '{"action":"AUTO_REPLY"|"ESCALATE_TO_HUMAN",'
    '"reply_text":str|null,'
    '"escalation_reason":str|null,'
    '"confidence":0-1}'
)


def analyse_email(email: dict) -> dict:
    """
    Analyse an email and return action + reply.
    Returns:
        {"action": str, "reply_text": str|None, "escalation_reason": str|None, "confidence": float}
    """
    client = KimiClient()

    system_prompt = _SYSTEM.format(
        nutrio_context=get_short_context(),
        tone=Config.REPLY_TONE,
        name=Config.YOUR_NAME,
    )

    body = email["body"][:1200].rsplit(" ", 1)[0]
    thread = f"\nCONTEXT:\n{email.get('thread_context','')[:600]}" if email.get("thread_context") else ""
    user_msg = f"From:{email['sender']}\nSubject:{email['subject']}\n\n{body}{thread}"

    try:
        result = client.chat_json(user_msg, system_prompt=system_prompt, temperature=0.3, max_tokens=500)

        if "action" not in result:
            raise ValueError("Missing action field")
        if result["action"] not in ("AUTO_REPLY", "ESCALATE_TO_HUMAN"):
            raise ValueError(f"Bad action: {result['action']}")
        if result["action"] == "AUTO_REPLY" and not result.get("reply_text"):
            raise ValueError("AUTO_REPLY with no reply_text")

        logger.info(f"AI: {result['action']} (conf={result.get('confidence','?')}) — {email['subject']}")
        return result

    except Exception as e:
        logger.error(f"AI handler error: {e}")
        return {
            "action": "ESCALATE_TO_HUMAN",
            "reply_text": None,
            "escalation_reason": f"AI error: {e}",
            "confidence": 0.0,
        }
