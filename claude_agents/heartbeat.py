"""
Heartbeat — Keeps all bots alive 24/7
======================================
Monitors bot processes, sends Telegram alerts on crashes,
auto-restarts, and runs Claude+Kimi improvement cycles.

Run on VPS:
    nohup python claude_agents/heartbeat.py >> heartbeat.log 2>&1 &
"""

import os
import sys
import time
import signal
import logging
import subprocess
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [HEARTBEAT] %(message)s",
    handlers= [logging.StreamHandler(), logging.FileHandler("heartbeat.log")],
)
logger = logging.getLogger("heartbeat")

PROJECT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT))
from telegram_push import notify, notify_bot_crash, notify_bot_restarted

CHECK_INTERVAL = 60      # seconds between checks
IMPROVE_EVERY  = 3600    # run improvement cycle every 1 hour
PUSH_EVERY     = 1800    # push to GitHub every 30 mins

# ── Bots to monitor ───────────────────────────────────────────
BOTS = [
    {"name": "Oddpool",            "dir": "oddpool",            "cmd": ["python", "main.py"]},
    {"name": "Polymarket Flipper", "dir": "polymarket_flipper", "cmd": ["python", "main.py"]},
    {"name": "Kalshi Flipper",     "dir": "kalshi_flipper",     "cmd": ["python", "main.py"]},
]

_processes = {}
_running   = True
_last_improve = 0
_last_push    = 0


def _telegram(msg: str):
    notify(msg)


def start_bot(bot: dict) -> subprocess.Popen:
    """Start a bot process."""
    bot_dir = PROJECT / bot["dir"]
    if not bot_dir.exists():
        logger.warning(f"{bot['name']}: directory not found")
        return None
    try:
        p = subprocess.Popen(
            bot["cmd"], cwd=bot_dir,
            stdout=open(bot_dir / "bot.log", "a"),
            stderr=subprocess.STDOUT,
        )
        logger.info(f"Started {bot['name']} (PID {p.pid})")
        return p
    except Exception as e:
        logger.error(f"Failed to start {bot['name']}: {e}")
        return None


def check_bots():
    """Check all bots, restart any that crashed."""
    for bot in BOTS:
        name = bot["name"]
        proc = _processes.get(name)

        if proc is None or proc.poll() is not None:
            exit_code = proc.poll() if proc else "never started"
            if proc is not None:
                logger.warning(f"{name} crashed (exit {exit_code}) — restarting...")
                notify_bot_crash(name, log_tail=f"Exit code: {exit_code}")
            else:
                logger.info(f"Starting {name}...")

            new_proc = start_bot(bot)
            if new_proc:
                _processes[name] = new_proc
                notify_bot_restarted(name, pid=new_proc.pid)
        else:
            logger.debug(f"{name} running (PID {proc.pid})")


def run_improvement_cycle():
    """Ask Claude + Kimi to find and implement improvements."""
    logger.info("Running improvement cycle...")
    try:
        result = subprocess.run(
            ["python", "claude_agents/orchestrator.py", "--task", "improve"],
            cwd=PROJECT, capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            logger.info("Improvement cycle complete.")
        else:
            logger.warning(f"Improvement cycle failed: {result.stderr[:200]}")
    except Exception as e:
        logger.error(f"Improvement cycle error: {e}")


def push_to_github():
    """Auto-push any changes."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=PROJECT, check=True, capture_output=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT)
        if diff.returncode != 0:
            msg = f"Heartbeat auto-push {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=PROJECT, check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "push", "xvin1ty", "main"],
                cwd=PROJECT, check=True, capture_output=True,
            )
            logger.info("Auto-pushed to GitHub.")
    except Exception as e:
        logger.debug(f"Git push: {e}")


def report_status():
    """Send daily status to Telegram."""
    alive = [name for name, p in _processes.items() if p and p.poll() is None]
    _telegram(
        f"💓 <b>Heartbeat Status</b>\n"
        f"Time: {datetime.now().strftime('%H:%M')}\n"
        f"Running: {', '.join(alive) or 'none'}\n"
        f"Total bots: {len(alive)}/{len(BOTS)}"
    )


def _handle_stop(sig, frame):
    global _running
    logger.info("Heartbeat stopping...")
    _telegram("🛑 Heartbeat stopped (manual)")
    for name, p in _processes.items():
        if p and p.poll() is None:
            p.terminate()
    _running = False


signal.signal(signal.SIGINT, _handle_stop)
signal.signal(signal.SIGTERM, _handle_stop)


def main():
    global _last_improve, _last_push

    logger.info("=" * 50)
    logger.info("  HEARTBEAT STARTED")
    logger.info("=" * 50)
    _telegram("💓 <b>Heartbeat started</b> — monitoring all bots")

    # Initial start
    check_bots()

    while _running:
        now = time.time()

        check_bots()

        if now - _last_improve >= IMPROVE_EVERY:
            run_improvement_cycle()
            _last_improve = now

        if now - _last_push >= PUSH_EVERY:
            push_to_github()
            _last_push = now

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
