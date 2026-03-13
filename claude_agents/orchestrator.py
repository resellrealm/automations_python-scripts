"""
Orchestrator — Claude + Kimi Working Together
=============================================
The main brain. Claude plans and codes. Kimi researches and classifies.
Runs all money-making systems and keeps them alive 24/7.

Usage:
    python orchestrator.py                    # run all systems
    python orchestrator.py --task market      # run market bots only
    python orchestrator.py --task research    # do GitHub research
    python orchestrator.py --task apply       # run apprenticeship applier
    python orchestrator.py --loop             # infinite loop mode
"""

import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

from kimi_worker import kimi, kimi_research, kimi_json
from claude_runner import claude_run, claude_task, claude_github_research

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers= [
        logging.StreamHandler(),
        logging.FileHandler("orchestrator.log"),
    ]
)
logger = logging.getLogger("orchestrator")

PROJECT = Path(__file__).parent.parent


# ── Task runners ──────────────────────────────────────────────

def run_market_bots(dry_run: bool = False):
    """Start all money-making bots."""
    flag = "--dry-run" if dry_run else ""

    bots = [
        ("Oddpool",           PROJECT / "oddpool",           "main.py"),
        ("Polymarket Flipper",PROJECT / "polymarket_flipper","main.py"),
        ("Kalshi Flipper",    PROJECT / "kalshi_flipper",    "main.py"),
    ]

    procs = []
    for name, folder, script in bots:
        if not (folder / script).exists():
            logger.warning(f"{name}: {script} not found in {folder}")
            continue
        cmd = ["python", script] + ([flag] if flag else [])
        try:
            p = subprocess.Popen(cmd, cwd=folder)
            procs.append((name, p))
            logger.info(f"Started {name} (PID {p.pid})")
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")

    return procs


def run_apprenticeship():
    """Run apprenticeship applier — scrape + apply."""
    logger.info("Running apprenticeship applier...")
    result = subprocess.run(
        ["python", "main.py", "--apply", "--limit", "5"],
        cwd=PROJECT / "apprenticeship_applier",
        capture_output=True, text=True, timeout=600,
    )
    logger.info(f"Applier done: {result.stdout[-200:]}")
    return result.returncode == 0


def research_and_improve(topic: str):
    """
    Kimi researches a topic → Claude implements improvements.
    The core collaborative loop.
    """
    logger.info(f"Research + Improve: {topic}")

    # Step 1: Kimi researches
    logger.info("Kimi researching...")
    research = kimi_research(topic, depth="detailed")
    logger.info(f"Kimi result: {research[:200]}...")

    # Step 2: Claude decides what to implement
    logger.info("Claude planning implementation...")
    plan = claude_run(
        f"Based on this research, what Python code changes should we make to improve our "
        f"money-making bots? Be specific and actionable.\n\nResearch:\n{research}",
        max_turns=5,
    )
    logger.info(f"Claude plan: {plan[:200]}...")

    # Step 3: Claude implements if actionable
    if any(w in plan.lower() for w in ["add", "create", "update", "fix", "implement"]):
        logger.info("Claude implementing...")
        result = claude_task(
            task    = f"Implement these improvements to our trading/arbitrage bots:\n{plan}",
            context = f"Research findings:\n{research}",
            tools   = "Read,Write,Edit,Bash,Glob,Grep",
            max_turns=25,
            budget  = 1.0,
        )
        logger.info(f"Implementation done: {result[:100]}")

        # Auto-push
        push_to_github("Auto-improve: " + topic[:50])


def github_research_loop(queries: list):
    """Claude searches GitHub for each query, Kimi summarises findings."""
    logger.info(f"GitHub research: {len(queries)} queries")

    for query in queries:
        logger.info(f"Researching: {query}")

        # Claude searches GitHub
        findings = claude_github_research(query)

        # Kimi summarises into actionable points
        summary = kimi(
            f"Summarise these GitHub findings into 3 actionable things we can steal/use:\n\n{findings}",
            task="summarise",
        )
        logger.info(f"Summary for '{query}': {summary[:200]}")


def push_to_github(message: str = "Auto-update from orchestrator"):
    """Commit and push all changes."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=PROJECT, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=PROJECT
        )
        if result.returncode == 0:
            logger.debug("Nothing to commit.")
            return

        subprocess.run(
            ["git", "commit", "-m", f"{message}\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"],
            cwd=PROJECT, check=True,
        )
        subprocess.run(["git", "push", "xvin1ty", "main"], cwd=PROJECT, check=True)
        logger.info("Pushed to GitHub.")
    except Exception as e:
        logger.error(f"Git push failed: {e}")


def monitor_bots(procs: list) -> list:
    """Check if bots are still running, restart if crashed."""
    alive = []
    for name, proc in procs:
        ret = proc.poll()
        if ret is None:
            alive.append((name, proc))
        else:
            logger.warning(f"{name} crashed (exit {ret}) — asking Claude to diagnose...")
            diagnosis = claude_run(
                f"{name} bot crashed with exit code {ret}. "
                f"Read its log file and diagnose the error. Suggest a fix.",
                max_turns=5,
            )
            kimi_summary = kimi(f"Summarise this crash diagnosis in 1 line: {diagnosis}", task="summarise")
            logger.warning(f"Crash diagnosis: {kimi_summary}")
    return alive


def money_loop(dry_run: bool = False):
    """
    Main autonomous loop. Runs forever.
    - Starts all bots
    - Monitors them, restarts if crashed
    - Periodically researches improvements
    - Auto-pushes changes to GitHub
    """
    logger.info("=" * 60)
    logger.info("  AUTONOMOUS MONEY-MAKING LOOP STARTED")
    logger.info(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info("=" * 60)

    # Initial GitHub research
    github_research_loop([
        "polymarket flash crash arbitrage bot python 2025",
        "kalshi prediction market arbitrage open source",
        "cross platform prediction market arbitrage",
    ])

    # Start bots
    procs = run_market_bots(dry_run=dry_run)

    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n── Heartbeat cycle {cycle} @ {datetime.now().strftime('%H:%M:%S')} ──")

        # Monitor and restart crashed bots
        procs = monitor_bots(procs)
        if len(procs) < 3:
            logger.warning(f"Only {len(procs)} bots running — restarting missing ones")
            procs = run_market_bots(dry_run=dry_run)

        # Every 10 cycles: research improvements
        if cycle % 10 == 0:
            topic = "new prediction market arbitrage strategies 2025 2026"
            research_and_improve(topic)

        # Every 5 cycles: run apprenticeship applier
        if cycle % 5 == 0:
            run_apprenticeship()

        # Every 20 cycles: push to GitHub
        if cycle % 20 == 0:
            push_to_github(f"Heartbeat auto-push cycle {cycle}")

        time.sleep(300)  # 5-minute heartbeat


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude+Kimi Orchestrator")
    parser.add_argument("--task",    choices=["market","research","apply","improve","all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--loop",    action="store_true", help="Run forever")
    parser.add_argument("--push",    action="store_true", help="Push to GitHub and exit")
    args = parser.parse_args()

    if args.push:
        push_to_github("Manual push from orchestrator")
        return

    if args.loop or args.task == "all":
        money_loop(dry_run=args.dry_run)
        return

    if args.task == "market":
        procs = run_market_bots(dry_run=args.dry_run)
        logger.info(f"Started {len(procs)} bots. Press Ctrl+C to stop.")
        try:
            while True:
                procs = monitor_bots(procs)
                time.sleep(60)
        except KeyboardInterrupt:
            for name, p in procs:
                p.terminate()

    elif args.task == "research":
        github_research_loop([
            "polymarket arbitrage bot python",
            "kalshi trading bot open source",
            "cross platform prediction market scanner",
        ])

    elif args.task == "apply":
        run_apprenticeship()

    elif args.task == "improve":
        research_and_improve("prediction market arbitrage strategies and improvements")


if __name__ == "__main__":
    main()
