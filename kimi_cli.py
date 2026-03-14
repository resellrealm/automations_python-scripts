#!/usr/bin/env python3
"""
Kimi CLI — Drop-in equivalent of `claude -p "message"`
=======================================================
Usage:
    python kimi_cli.py "your message here"
    python kimi_cli.py "your message" --task research
    python kimi_cli.py "your message" --max-tokens 1000

Works exactly like `claude -p` but routes to Moonshot/Kimi API.
bot.py calls this via subprocess the same way it calls claude.
"""

import os
import sys
import argparse
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).parent / ".env")

API_URL = "https://api.moonshot.cn/v1/chat/completions"
API_KEY = os.getenv("AI_API_KEY") or os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY", "")
MODEL   = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

TASK_PROMPTS = {
    "research":     "You are a research assistant. Be concise and factual.",
    "summarise":    "Summarise in bullet points. Be brief.",
    "code":         "You are an expert Python programmer. Be precise.",
    "decision":     "Make a clear YES/NO decision with a one-line reason.",
    "default":      "Be concise and helpful.",
}


def ask(prompt: str, task: str = "default", max_tokens: int = 800) -> str:
    if not API_KEY:
        print("[kimi_cli] ERROR: No API key. Set AI_API_KEY in .env", file=sys.stderr)
        sys.exit(1)

    system = TASK_PROMPTS.get(task, TASK_PROMPTS["default"])

    try:
        r = httpx.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":    MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt[:6000]},
                ],
                "max_tokens":  max_tokens,
                "temperature": 0.3,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        print(f"[kimi_cli] API error {e.response.status_code}: {e.response.text[:200]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[kimi_cli] Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Kimi CLI — ask Moonshot AI")
    parser.add_argument("prompt",       nargs="?",  help="The message to send")
    parser.add_argument("--task",       default="default", choices=list(TASK_PROMPTS.keys()))
    parser.add_argument("--max-tokens", type=int,   default=800)
    args = parser.parse_args()

    prompt = args.prompt or (sys.stdin.read().strip() if not sys.stdin.isatty() else None)
    if not prompt:
        parser.print_help()
        sys.exit(1)

    print(ask(prompt, task=args.task, max_tokens=args.max_tokens))


if __name__ == "__main__":
    main()
