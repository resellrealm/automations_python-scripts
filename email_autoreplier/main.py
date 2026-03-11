"""
Email Auto-Replier — Main Entry Point
=====================================
Usage:
    python main.py                   # Run as daemon (polls every N minutes)
    python main.py --once            # Process inbox once then exit
    python main.py --queue           # Show pending escalation queue
    python main.py --stats           # Show processing stats

How it works:
    1. Connects to Gmail via OAuth2
    2. Fetches unread emails
    3. Sends each email to Kimi AI for analysis
    4. AI either auto-replies or escalates to human review
    5. Escalated emails are saved to escalation_queue.json
"""

import sys
import os
import time
import signal
import argparse

# Allow imports from the parent directory (shared/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from shared.logger import get_logger
import database
import email_processor
import escalation_queue
from gmail_client import GmailClient

logger = get_logger("email_autoreplier", log_dir="logs")

_running = True


def handle_signal(signum, frame):
    """Graceful shutdown on SIGINT/SIGTERM (for VPS daemon use)."""
    global _running
    logger.info(f"Received signal {signum} — shutting down gracefully...")
    _running = False


def run_once(gmail: GmailClient):
    """Process inbox one time."""
    logger.info("Starting inbox processing cycle...")
    stats = email_processor.process_inbox(gmail)
    return stats


def run_daemon(gmail: GmailClient):
    """Poll inbox every POLL_INTERVAL_MINUTES minutes."""
    interval = Config.POLL_INTERVAL_MINUTES * 60
    logger.info(
        f"Starting daemon — polling every {Config.POLL_INTERVAL_MINUTES} minute(s). "
        f"Press Ctrl+C to stop."
    )

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while _running:
        try:
            run_once(gmail)
        except Exception as e:
            logger.error(f"Unhandled error in processing cycle: {e}", exc_info=True)

        if _running:
            logger.info(f"Sleeping {Config.POLL_INTERVAL_MINUTES} min until next cycle...")
            for _ in range(interval):
                if not _running:
                    break
                time.sleep(1)

    logger.info("Daemon stopped.")


def show_stats():
    """Print processing statistics from the database."""
    stats = database.get_stats()
    total = sum(stats.values())
    print(f"\n{'='*40}")
    print(f"  Email Auto-Replier Statistics")
    print(f"{'='*40}")
    print(f"  Total processed : {total}")
    for action, count in stats.items():
        print(f"  {action:<16} : {count}")
    print(f"{'='*40}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Email Auto-Replier — AI-powered email handler"
    )
    parser.add_argument("--once", action="store_true", help="Process inbox once and exit")
    parser.add_argument("--queue", action="store_true", help="Show pending escalation queue")
    parser.add_argument("--stats", action="store_true", help="Show processing statistics")
    args = parser.parse_args()

    # Show queue without needing Gmail connection
    if args.queue:
        escalation_queue.print_pending_summary()
        return

    if args.stats:
        show_stats()
        return

    # Validate config before connecting
    try:
        Config.validate()
    except EnvironmentError as e:
        logger.error(str(e))
        sys.exit(1)

    # Init database
    database.init_db()

    # Connect to Gmail
    logger.info("Connecting to Gmail...")
    try:
        gmail = GmailClient()
    except Exception as e:
        logger.error(f"Failed to authenticate with Gmail: {e}")
        sys.exit(1)

    if args.once:
        stats = run_once(gmail)
        print(f"\nDone — replied: {stats['replied']}, escalated: {stats['escalated']}, errors: {stats['errors']}\n")
    else:
        run_daemon(gmail)


if __name__ == "__main__":
    main()
