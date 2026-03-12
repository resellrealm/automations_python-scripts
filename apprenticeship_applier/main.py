"""
Apprenticeship Applier — Main Entry Point
==========================================
Usage:
    python main.py --scrape-only            # Find new listings, don't apply
    python main.py --apply                  # Scrape then apply to found jobs
    python main.py --apply --limit 5        # Apply to max 5 jobs this run
    python main.py --dry-run                # Scrape + generate cover letters, don't submit
    python main.py --report                 # Show stats on jobs found/applied

How it works:
    1. Scrapes findapprenticeship.service.gov.uk for matching apprenticeships
    2. Skips jobs already seen in the database
    3. For each new job: generates a tailored AI cover letter
    4. Logs in to gov.uk and submits the application (unless --dry-run)
    5. Saves screenshots and logs everything
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from shared.logger import get_logger
import database
import scraper as scraper_module
import ai_cover_letter
import profile_manager
import database
from applier import ApprenticeshipApplier
from notifier import get_notifier

logger = get_logger("apprenticeship_applier", log_dir="logs")


def show_report():
    stats = database.get_stats()
    total = sum(stats.values())
    print(f"\n{'='*50}")
    print(f"  Apprenticeship Applier — Report")
    print(f"{'='*50}")
    print(f"  Total listings tracked : {total}")
    for status, count in sorted(stats.items()):
        bar = "█" * min(count, 40)
        print(f"  {status:<20} {count:>4}  {bar}")
    print(f"{'='*50}\n")


def run_scrape() -> list:
    """Scrape all keywords and return new jobs found."""
    logger.info(
        f"Searching for: {Config.SEARCH_KEYWORDS} "
        f"near {Config.SEARCH_LOCATION} ({Config.SEARCH_DISTANCE_MILES} miles)"
    )
    new_jobs = scraper_module.scrape_all_keywords()
    logger.info(f"Found {len(new_jobs)} new listing(s).")
    if new_jobs:
        try:
            get_notifier().send(
                f"🔍 <b>Scrape complete</b>\n"
                f"Found {len(new_jobs)} new apprenticeship listing(s).\n"
                f"Keywords: {', '.join(Config.SEARCH_KEYWORDS)}\n"
                f"Location: {Config.SEARCH_LOCATION}"
            )
        except Exception:
            pass
    return new_jobs


def run_apply(profile, limit: int = None, dry_run: bool = False):
    """Generate cover letters and submit applications."""
    pending = database.get_pending_jobs(limit=limit or Config.MAX_APPLICATIONS_PER_RUN)

    if not pending:
        logger.info("No pending jobs to apply to.")
        return

    logger.info(
        f"{'[DRY RUN] ' if dry_run else ''}Applying to {len(pending)} job(s)..."
    )

    profile_summary = profile.to_summary_text()
    applied = 0
    skipped = 0
    failed = 0

    # Set up browser session (skipped in dry-run)
    applier_context = ApprenticeshipApplier() if not dry_run else None

    def process_jobs(applier=None):
        nonlocal applied, skipped, failed

        if applier and not applier.login():
            logger.error("Could not log in to gov.uk — aborting applications.")
            return

        for job in pending:
            job = dict(job)  # Convert sqlite3.Row to plain dict
            logger.info(f"\n{'─'*50}")
            logger.info(f"  Job:     {job['title']}")
            logger.info(f"  Company: {job['company']}")
            logger.info(f"  URL:     {job['url']}")

            # Generate cover letter
            letter_text = ai_cover_letter.generate_cover_letter(
                job, profile_summary, profile.full_name
            )
            letter_path = ai_cover_letter.save_cover_letter(job, letter_text)

            if dry_run:
                logger.info(f"  [DRY RUN] Cover letter saved: {letter_path}")
                database.update_status(job["url"], "found", cover_letter_path=letter_path,
                                       notes="dry_run — letter generated but not submitted")
                applied += 1
                continue

            # Submit application
            status = applier.apply_to_job(job, letter_text, profile)
            database.update_status(
                job["url"],
                status,
                cover_letter_path=letter_path,
                notes=f"Run at {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )

            if status == "applied":
                applied += 1
                logger.info(f"  APPLIED successfully!")
            elif status == "skipped":
                skipped += 1
                logger.info(f"  Skipped (no apply button or already applied).")
            else:
                failed += 1
                logger.warning(f"  FAILED with status: {status}")

    if dry_run:
        process_jobs()
    else:
        with ApprenticeshipApplier() as applier:
            process_jobs(applier)

    print(f"\n{'='*50}")
    print(f"  Run complete")
    print(f"  Applied  : {applied}")
    print(f"  Skipped  : {skipped}")
    print(f"  Failed   : {failed}")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Apprenticeship Applier — auto-apply to UK apprenticeships"
    )
    parser.add_argument("--scrape-only", action="store_true", help="Only scrape listings, don't apply")
    parser.add_argument("--apply", action="store_true", help="Scrape then apply to new jobs")
    parser.add_argument("--dry-run", action="store_true", help="Generate cover letters but don't submit")
    parser.add_argument("--report", action="store_true", help="Show stats and exit")
    parser.add_argument("--limit", type=int, default=None, help="Max applications this run")
    args = parser.parse_args()

    if args.report:
        show_report()
        return

    # Validate config
    try:
        Config.validate()
    except EnvironmentError as e:
        logger.error(str(e))
        sys.exit(1)

    # Init database
    database.init_db()

    # Load user profile
    try:
        profile = profile_manager.load_profile()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.scrape_only:
        run_scrape()
        show_report()
        return

    if args.apply or args.dry_run:
        # Always scrape first for fresh listings
        run_scrape()
        dry = args.dry_run or Config.DRY_RUN
        run_apply(profile, limit=args.limit, dry_run=dry)
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
