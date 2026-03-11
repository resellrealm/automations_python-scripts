"""
AI Enhancer
Uses Kimi AI to generate a punchy title, description, and hashtags.
Highly token-efficient — sends only the transcript (truncated) and platform.
Single API call, ~300 input tokens, ~150 output tokens.
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.kimi_client import KimiClient
from shared.logger import get_logger
from config import Config

logger = get_logger("ai_enhancer")

# Minimal system prompt — keeps token usage low
_SYSTEM = "You generate social media content metadata. Reply with valid JSON only, no extra text."

_USER_TMPL = """{platform} video. Transcript: \"{transcript}\"
Return JSON: {{"title":"<punchy title ≤60 chars>","description":"<2 sentence caption>","hashtags":["tag1","tag2",...10 tags],"cta":"<call to action ≤60 chars>"}}"""


def generate_metadata(transcript: str, platform: str = "tiktok") -> dict:
    """
    Generate title, description, hashtags and CTA for a video.
    Token-efficient: truncates transcript to 400 chars.

    Returns:
        {"title": str, "description": str, "hashtags": list[str], "cta": str}
    """
    if not Config.AI_API_KEY:
        logger.warning("No AI_API_KEY set — using placeholder metadata.")
        return _placeholder(transcript)

    # Truncate transcript to keep tokens minimal
    snippet = transcript[:400].rsplit(" ", 1)[0] if len(transcript) > 400 else transcript
    user_msg = _USER_TMPL.format(platform=platform.replace("_", " "), transcript=snippet)

    try:
        client = KimiClient()
        result = client.chat_json(user_msg, system_prompt=_SYSTEM, temperature=0.7, max_tokens=300)
        logger.info(f"AI metadata generated: title='{result.get('title', '')}'")
        return result
    except Exception as e:
        logger.warning(f"AI metadata failed ({e}) — using placeholder.")
        return _placeholder(transcript)


def _placeholder(transcript: str) -> dict:
    words = transcript.split()[:5]
    title = " ".join(words).title() if words else "My Video"
    return {
        "title": title,
        "description": transcript[:120] if transcript else "",
        "hashtags": ["#fyp", "#viral", "#foryou", "#trending", "#video"],
        "cta": "Follow for more!",
    }
