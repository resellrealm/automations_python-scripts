"""
Token Budget Manager
====================
Keeps AI costs minimal by:
  1. Caching results by content hash — never re-calls AI for same video
  2. Tracking daily token usage — hard-stops at budget limit
  3. Auto-selecting cheapest Kimi model that fits the task
  4. Deduplicating prompts — same prompt in same session reuses cached response
  5. Adaptive truncation — trims input based on remaining daily budget

Cache file: ~/.video_editor_cache.json
Budget file: ~/.video_editor_budget.json
"""

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

_CACHE_FILE  = Path.home() / ".video_editor_cache.json"
_BUDGET_FILE = Path.home() / ".video_editor_budget.json"

# Model selection: pick cheapest that fits context size
_MODELS = [
    ("moonshot-v1-8k",   8_000),
    ("moonshot-v1-32k",  32_000),
    ("moonshot-v1-128k", 128_000),
]

# 1 token ≈ 4 chars (rough estimate for English text)
_CHARS_PER_TOKEN = 4

# Daily soft limit (tokens). Overridable via TOKEN_DAILY_BUDGET env var.
_DEFAULT_DAILY_BUDGET = int(os.getenv("TOKEN_DAILY_BUDGET", "50000"))


# ── Cache ──────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def _save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))


def content_hash(text: str) -> str:
    """SHA256 of text — used as cache key."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def cache_get(key: str) -> Optional[dict]:
    """Retrieve a cached result. Returns None on miss."""
    store = _load_json(_CACHE_FILE)
    entry = store.get(key)
    if not entry:
        return None
    if entry.get("date") != str(date.today()):
        return entry.get("value")  # keep cache across days — metadata doesn't expire
    return entry.get("value")


def cache_set(key: str, value: dict):
    """Store a result in the cache."""
    store = _load_json(_CACHE_FILE)
    store[key] = {"date": str(date.today()), "value": value}
    # Trim cache to last 200 entries to avoid unbounded growth
    if len(store) > 200:
        oldest_keys = list(store.keys())[:-200]
        for k in oldest_keys:
            del store[k]
    _save_json(_CACHE_FILE, store)


# ── Budget tracking ────────────────────────────────────────────────────────

def _load_budget() -> dict:
    b = _load_json(_BUDGET_FILE)
    today = str(date.today())
    if b.get("date") != today:
        b = {"date": today, "used": 0}
    return b


def _save_budget(b: dict):
    _save_json(_BUDGET_FILE, b)


def tokens_used_today() -> int:
    return _load_budget()["used"]


def daily_budget() -> int:
    return _DEFAULT_DAILY_BUDGET


def budget_remaining() -> int:
    return max(0, daily_budget() - tokens_used_today())


def record_tokens(count: int):
    """Increment today's token counter."""
    b = _load_budget()
    b["used"] += count
    _save_budget(b)


def budget_ok(estimated_tokens: int = 0) -> bool:
    """True if we have room for this call."""
    return budget_remaining() >= max(estimated_tokens, 150)


# ── Model selection ────────────────────────────────────────────────────────

def pick_model(prompt_chars: int) -> str:
    """
    Pick the cheapest Kimi model that fits the prompt.
    Always uses 8k unless the prompt is genuinely huge.
    """
    estimated_tokens = prompt_chars // _CHARS_PER_TOKEN
    for model_name, ctx_limit in _MODELS:
        if estimated_tokens < ctx_limit * 0.7:  # 70% headroom
            return model_name
    return _MODELS[-1][0]  # fallback to 128k


# ── Adaptive truncation ────────────────────────────────────────────────────

def smart_truncate(text: str, max_tokens: int = 400) -> str:
    """
    Truncate text to fit within max_tokens budget.
    Scales down further if daily budget is running low.
    """
    ratio = budget_remaining() / max(daily_budget(), 1)
    # If below 20% budget, be aggressive
    if ratio < 0.2:
        max_tokens = min(max_tokens, 150)
    elif ratio < 0.5:
        max_tokens = min(max_tokens, 250)

    char_limit = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= char_limit:
        return text
    # Cut at last word boundary
    return text[:char_limit].rsplit(" ", 1)[0]


# ── High-level helper ──────────────────────────────────────────────────────

def cached_ai_call(cache_key: str, call_fn, estimated_tokens: int = 500) -> Optional[dict]:
    """
    Check cache first. If miss and budget allows, call the AI function.
    Records token usage. Returns None if over budget.

    Usage:
        result = cached_ai_call(
            cache_key  = content_hash(transcript),
            call_fn    = lambda: generate_metadata(transcript, platform),
            estimated_tokens = 500,
        )
    """
    # Cache hit — zero tokens spent
    hit = cache_get(cache_key)
    if hit is not None:
        return hit

    # Budget check
    if not budget_ok(estimated_tokens):
        return None

    # Call AI
    result = call_fn()

    # Store + record
    if result:
        cache_set(cache_key, result)
        record_tokens(estimated_tokens)

    return result


def status() -> str:
    """Human-readable budget status string."""
    used = tokens_used_today()
    total = daily_budget()
    pct = int(used / max(total, 1) * 100)
    return f"Tokens today: {used:,}/{total:,} ({pct}%) — {budget_remaining():,} remaining"
