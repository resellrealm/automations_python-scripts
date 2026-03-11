"""
Email Auto-Replier (Zoho Mail) — Entry Point
=============================================
Usage:
    python main.py              # Daemon — polls every N minutes forever
    python main.py --once       # Process inbox once then exit
    python main.py --queue      # Show emails waiting for your reply
    python main.py --stats      # Show processing stats
    python main.py --test       # Test Zoho connection only

Setup:
    1. Edit .env with your Zoho credentials
    2. Run: python main.py --test
    3. Run: python main.py --once  (first live run)
    4. Run: python main.py         (daemon on VPS)
"""

import sys, os, time, signal, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from shared.logger import get_logger
import database
import email_processor
import escalation_queue
from zoho_client import ZohoClient

logger = get_logger("email_autoreplier", log_dir="logs")
_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info(f"Signal {signum} received — shutting down...")
    _running = False


def run_once(zoho: ZohoClient):
    return email_processor.process_inbox(zoho)


def run_daemon(zoho: ZohoClient):
    interval = Config.POLL_INTERVAL_MINUTES * 60
    logger.info(f"Daemon started — checking every {Config.POLL_INTERVAL_MINUTES} min. Ctrl+C to stop.")
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while _running:
        try:
            run_once(zoho)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
        if _running:
            logger.info(f"Sleeping {Config.POLL_INTERVAL_MINUTES} min...")
            for _ in range(interval):
                if not _running:
                    break
                time.sleep(1)

    logger.info("Daemon stopped.")


def main():
    parser = argparse.ArgumentParser(description="Zoho Mail Auto-Replier")
    parser.add_argument("--once",  action="store_true", help="Process inbox once and exit")
    parser.add_argument("--queue", action="store_true", help="Show escalation queue")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--test",  action="store_true", help="Test Zoho connection")
    args = parser.parse_args()

    if args.queue:
        escalation_queue.print_pending_summary()
        return

    if args.stats:
        stats = database.get_stats()
        print(f"\n{'='*40}")
        print(f"  Email Auto-Replier Stats")
        print(f"{'='*40}")
        for action, count in stats.items():
            print(f"  {action:<16} : {count}")
        print(f"{'='*40}\n")
        return

    try:
        Config.validate()
    except EnvironmentError as e:
        logger.error(str(e))
        sys.exit(1)

    database.init_db()

    logger.info("Connecting to Zoho Mail...")
    try:
        zoho = ZohoClient()
    except ConnectionError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.test:
        print("\n  Zoho Mail connection: OK\n")
        return

    if args.once:
        stats = run_once(zoho)
        print(f"\nDone — replied:{stats['replied']} escalated:{stats['escalated']} errors:{stats['errors']}\n")
    else:
        run_daemon(zoho)


if __name__ == "__main__":
    main()
