"""
VPS Task Runner — Background Task Executor with Telegram Notifications
=======================================================================
Runs long tasks in the background. Writes status to tasks.json.
Sends Telegram push notifications when tasks START and COMPLETE.

This solves the "text me when done" problem:
  - Telegram bot only RESPONDS when you message it (polling)
  - But THIS script calls the Telegram API directly → pushes to you proactively

Usage:
  python vps_tasks/task_runner.py --name "scrape jobs" --cmd "python apprenticeship_applier/main.py --scrape-only"
  python vps_tasks/task_runner.py --status          # show all task statuses
  python vps_tasks/task_runner.py --clear-done      # remove completed tasks from list

From Claude Code skill / OpenClaw:
  The skill starts this script as a background process (nohup) and immediately
  returns. The script runs the real command, then pushes Telegram when done.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
TASKS_FILE = Path(__file__).parent / "tasks.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = os.getenv("TELEGRAM_USER_ID", "") or os.getenv("TELEGRAM_CHAT_ID", "")


# ── Telegram push (direct API call — no polling needed) ──────────────────────

def _push(message: str):
    """Push a message directly to Telegram. Works even when bot isn't polling."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print(f"[task_runner] Telegram not configured. Message: {message}")
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"[task_runner] Telegram push failed: {e}")


# ── Task state persistence ────────────────────────────────────────────────────

def _load_tasks() -> dict:
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_tasks(tasks: dict):
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def _set_status(task_id: str, **kwargs):
    tasks = _load_tasks()
    if task_id not in tasks:
        tasks[task_id] = {}
    tasks[task_id].update(kwargs)
    _save_tasks(tasks)


# ── Run a task ────────────────────────────────────────────────────────────────

def run_task(name: str, cmd: str, notify_done: bool = True):
    """
    Run a shell command. Blocks until complete, then pushes Telegram.
    This is called as a background process — the caller returns immediately.
    """
    task_id  = f"{name.replace(' ', '_')}_{int(time.time())}"
    started  = datetime.utcnow().isoformat()

    _set_status(task_id,
        name    = name,
        cmd     = cmd,
        status  = "running",
        started = started,
        pid     = os.getpid(),
    )

    _push(f"⏳ <b>Task started</b>: {name}\n<code>{cmd}</code>")
    print(f"[task_runner] Running: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, cwd=BASE_DIR,
            capture_output=True, text=True,
        )
        success  = result.returncode == 0
        finished = datetime.utcnow().isoformat()
        output   = (result.stdout or result.stderr or "").strip()[-500:]  # last 500 chars

        _set_status(task_id,
            status      = "done" if success else "failed",
            finished    = finished,
            return_code = result.returncode,
            output_tail = output,
        )

        if notify_done:
            icon = "✅" if success else "❌"
            status_word = "Complete" if success else "FAILED"
            msg = (
                f"{icon} <b>Task {status_word}</b>: {name}\n"
                f"Exit code: {result.returncode}\n"
            )
            if output:
                msg += f"\nLast output:\n<code>{output[-300:]}</code>"
            _push(msg)

        print(f"[task_runner] Done: {name} (exit {result.returncode})")

    except Exception as e:
        _set_status(task_id, status="failed", error=str(e), finished=datetime.utcnow().isoformat())
        _push(f"❌ <b>Task crashed</b>: {name}\nError: {e}")
        print(f"[task_runner] Error: {e}")


# ── Status report ─────────────────────────────────────────────────────────────

def status_report() -> str:
    tasks = _load_tasks()
    if not tasks:
        return "No tasks recorded."

    lines = []
    for tid, t in sorted(tasks.items(), key=lambda x: x[1].get("started", ""), reverse=True):
        icon = {"running": "⏳", "done": "✅", "failed": "❌"}.get(t.get("status"), "❓")
        started = t.get("started", "")[:16].replace("T", " ")
        finished = t.get("finished", "")[:16].replace("T", " ")
        lines.append(
            f"{icon} <b>{t.get('name', tid)}</b>\n"
            f"   Status: {t.get('status')} | Started: {started}"
            + (f" | Done: {finished}" if finished else "")
        )

    return "\n\n".join(lines[-10:])   # last 10 tasks


def clear_done():
    tasks = _load_tasks()
    before = len(tasks)
    tasks = {tid: t for tid, t in tasks.items() if t.get("status") not in ("done", "failed")}
    _save_tasks(tasks)
    print(f"Cleared {before - len(tasks)} completed tasks. {len(tasks)} remaining.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name",        help="Task display name")
    parser.add_argument("--cmd",         help="Shell command to run")
    parser.add_argument("--status",      action="store_true", help="Print all task statuses")
    parser.add_argument("--clear-done",  action="store_true", help="Remove completed tasks")
    parser.add_argument("--no-notify",   action="store_true", help="Don't push Telegram on done")
    args = parser.parse_args()

    if args.status:
        print(status_report())
        return

    if args.clear_done:
        clear_done()
        return

    if not args.name or not args.cmd:
        parser.print_help()
        sys.exit(1)

    run_task(args.name, args.cmd, notify_done=not args.no_notify)


if __name__ == "__main__":
    main()
