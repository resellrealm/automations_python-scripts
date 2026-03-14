"""
Heartbeat Check — runs on Claude Code Stop hook
================================================
Checks if the heartbeat daemon is alive.
If dead, attempts to restart it and sends a Telegram alert.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).parent.parent
HEARTBEAT_SCRIPT = PROJECT / "claude_agents" / "heartbeat.py"
LOG_FILE = PROJECT / "heartbeat.log"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = os.getenv("TELEGRAM_USER_ID", "") or os.getenv("TELEGRAM_CHAT_ID", "")


def _telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass


def is_heartbeat_running() -> bool:
    """Check if heartbeat.py is running as a process."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "heartbeat.py"],
            capture_output=True, text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def restart_heartbeat():
    """Start heartbeat in background via nohup."""
    try:
        log = open(LOG_FILE, "a")
        subprocess.Popen(
            ["python", str(HEARTBEAT_SCRIPT)],
            cwd=str(PROJECT),
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        print("[heartbeat_check] Heartbeat restarted.")
        _telegram("⚠️ <b>Heartbeat</b> was dead — auto-restarted by Claude Code stop hook.")
    except Exception as e:
        print(f"[heartbeat_check] Failed to restart heartbeat: {e}")


def main():
    if not HEARTBEAT_SCRIPT.exists():
        sys.exit(0)

    if is_heartbeat_running():
        print("[heartbeat_check] Heartbeat is running. OK.")
    else:
        print("[heartbeat_check] Heartbeat NOT running — restarting...")
        restart_heartbeat()


if __name__ == "__main__":
    main()
