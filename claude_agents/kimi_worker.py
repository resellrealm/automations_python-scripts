"""
Kimi Worker — Fast/cheap AI task executor
==========================================
Kimi handles: research, summaries, quick decisions, cover letters, classifications.
Claude handles: code, architecture, debugging, complex reasoning.

Usage:
    from kimi_worker import kimi
    result = kimi("Summarise this job listing and score it 0-100: ...")
    result = kimi("Research Polymarket flash crash strategies", task="research")
"""

import os
import json
import subprocess
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try Kimi CLI first, fallback to direct API ─────────────────
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_API_KEY = os.getenv("AI_API_KEY") or os.getenv("MOONSHOT_API_KEY", "")
KIMI_MODEL   = os.getenv("AI_MODEL", "moonshot-v1-8k")

TASK_PROMPTS = {
    "research":     "You are a research assistant. Be concise and factual.",
    "summarise":    "Summarise in bullet points. Be brief.",
    "score":        "Score 0-100. Reply with JSON: {score: N, reason: '...'}",
    "cover_letter": "Write a professional cover letter. 3 paragraphs max.",
    "classify":     "Classify and reply with JSON only.",
    "decision":     "Make a clear YES/NO decision with one-line reason.",
    "code_review":  "Review this code briefly. List issues only.",
    "default":      "Be concise and helpful.",
}


def kimi(prompt: str, task: str = "default", max_tokens: int = 500,
         system: str = None) -> str:
    """
    Run a prompt through Kimi AI.
    Falls back to direct API if Kimi CLI not installed.
    """
    # Try Kimi CLI first
    result = _try_kimi_cli(prompt, task)
    if result:
        return result

    # Fallback: direct API
    return _api_call(prompt, task, max_tokens, system)


def _try_kimi_cli(prompt: str, task: str) -> Optional[str]:
    """Attempt to use Kimi CLI if installed."""
    try:
        result = subprocess.run(
            ["kimi", "ask", prompt, "--no-stream"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass  # CLI not installed, use API
    except Exception as e:
        logger.debug(f"Kimi CLI error: {e}")
    return None


def _api_call(prompt: str, task: str, max_tokens: int, system: str) -> str:
    """Direct Moonshot API call."""
    if not KIMI_API_KEY:
        return f"[Kimi unavailable — no API key. Set AI_API_KEY in .env]"

    sys_prompt = system or TASK_PROMPTS.get(task, TASK_PROMPTS["default"])

    try:
        r = httpx.post(
            KIMI_API_URL,
            headers={"Authorization": f"Bearer {KIMI_API_KEY}",
                     "Content-Type": "application/json"},
            json={
                "model": KIMI_MODEL,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user",   "content": prompt[:3000]},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Kimi API error: {e}")
        return f"[Kimi error: {e}]"


def kimi_json(prompt: str, task: str = "classify") -> dict:
    """Run Kimi and parse JSON response."""
    text = kimi(prompt + "\n\nReply with valid JSON only.", task=task, max_tokens=300)
    try:
        # Extract JSON from response
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return {"error": "could not parse JSON", "raw": text}


def kimi_research(topic: str, depth: str = "brief") -> str:
    """Research a topic using Kimi."""
    prompt = f"Research: {topic}\nDepth: {depth}\nFocus on actionable facts and real data."
    return kimi(prompt, task="research", max_tokens=800)


def kimi_score_job(title: str, company: str, description: str) -> dict:
    """Score a job listing for George Bailey."""
    prompt = (
        f"Score this apprenticeship for a 18yo student studying Maths A-Level and Business/Law BTEC:\n"
        f"Title: {title}\nCompany: {company}\n"
        f"Description: {description[:500]}\n\n"
        f"Reply JSON: {{score: 0-100, reason: '...', apply: true/false}}"
    )
    return kimi_json(prompt, task="score")
