"""
Kimi Loop — Automated Video Processing
=======================================
Watches a folder for new videos and auto-processes them using Kimi as brain.
Also has an --improve mode where Kimi reviews the code and Claude implements fixes.

Usage:
    python kimi_loop.py watch /path/to/folder          # auto-process new videos
    python kimi_loop.py watch /path/to/folder --once   # process existing unprocessed
    python kimi_loop.py improve                        # Kimi reviews + Claude fixes code
    python kimi_loop.py budget                         # show token budget status
"""

import sys, os, json, time, hashlib, subprocess, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from shared.logger import get_logger
from shared.kimi_client import KimiClient
from config import Config
import token_budget as budget

logger = get_logger("kimi_loop")

PROJECT     = Path(__file__).parent.parent
EDITOR_DIR  = Path(__file__).parent
PROCESSED   = EDITOR_DIR / ".processed.json"
POLL_SECS   = int(os.getenv("WATCH_POLL_SECONDS", "30"))
VIDEO_EXTS  = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


# ── Processed-file tracking ────────────────────────────────────────────────

def _load_processed() -> set:
    if PROCESSED.exists():
        try:
            return set(json.loads(PROCESSED.read_text()))
        except Exception:
            pass
    return set()


def _mark_processed(path: str):
    done = _load_processed()
    done.add(str(path))
    PROCESSED.write_text(json.dumps(sorted(done), indent=2))


# ── Kimi decision: best platform for a video file ─────────────────────────

def _kimi_decide_platform(video_path: str) -> str:
    """
    Ask Kimi to pick the best platform based on filename/path hints.
    Uses a single tiny prompt — ~100 tokens.
    Falls back to Config.DEFAULT_PLATFORM silently.
    """
    if not Config.AI_API_KEY:
        return Config.DEFAULT_PLATFORM

    name = Path(video_path).stem.lower()
    cache_key = budget.content_hash(f"platform:{name}")
    cached = budget.cache_get(cache_key)
    if cached:
        return cached.get("platform", Config.DEFAULT_PLATFORM)

    if not budget.budget_ok(150):
        return Config.DEFAULT_PLATFORM

    prompt = (
        f'Video filename: "{name}". '
        f'Pick ONE platform: tiktok, instagram_reel, instagram_square, youtube_short. '
        f'Reply with just the platform name, nothing else.'
    )
    try:
        client = KimiClient()
        result = client.chat(prompt, temperature=0.1, max_tokens=10).strip().lower()
        valid = {"tiktok", "instagram_reel", "instagram_square", "youtube_short"}
        platform = result if result in valid else Config.DEFAULT_PLATFORM
        budget.cache_set(cache_key, {"platform": platform})
        budget.record_tokens(150)
        logger.info(f"Kimi decided platform: {platform} for '{name}'")
        return platform
    except Exception as e:
        logger.warning(f"Kimi platform decision failed: {e}")
        return Config.DEFAULT_PLATFORM


# ── Process a single video ─────────────────────────────────────────────────

def process_video(video_path: str):
    """Run the full editor pipeline on one video."""
    logger.info(f"Processing: {video_path}")

    platform = _kimi_decide_platform(video_path)

    cmd = [
        sys.executable, str(EDITOR_DIR / "main.py"),
        video_path,
        "--platform", platform,
    ]

    if not Config.AI_API_KEY:
        cmd.append("--no-ai")

    try:
        result = subprocess.run(cmd, cwd=str(EDITOR_DIR), capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            logger.info(f"Done: {video_path}")
            print(result.stdout[-800:] if len(result.stdout) > 800 else result.stdout)
        else:
            logger.error(f"Failed: {video_path}\n{result.stderr[-400:]}")
    except subprocess.TimeoutExpired:
        logger.error(f"Timed out: {video_path}")
    except Exception as e:
        logger.error(f"Error processing {video_path}: {e}")


# ── Watch loop ─────────────────────────────────────────────────────────────

def watch(folder: str, run_once: bool = False):
    folder = Path(folder).expanduser().resolve()
    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    print(f"Watching: {folder}")
    print(f"Poll interval: {POLL_SECS}s | {budget.status()}\n")

    while True:
        done = _load_processed()
        videos = [p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXTS]
        new_videos = [p for p in videos if str(p) not in done]

        for vid in new_videos:
            process_video(str(vid))
            _mark_processed(str(vid))

        if run_once:
            if not new_videos:
                print("No unprocessed videos found.")
            break

        time.sleep(POLL_SECS)


# ── Improvement loop ───────────────────────────────────────────────────────

def improve():
    """
    Kimi reviews the video editor code and suggests improvements.
    Claude CLI implements the best ones.
    Token-efficient: only sends file summaries, not full code.
    """
    print("Running improvement cycle...\n")

    # Build a short summary of each file (first 40 lines only — keeps tokens low)
    summaries = []
    for f in sorted(EDITOR_DIR.glob("*.py")):
        if f.name == "kimi_loop.py":
            continue
        lines = f.read_text().splitlines()[:40]
        summaries.append(f"### {f.name}\n" + "\n".join(lines))

    code_summary = "\n\n".join(summaries)
    snippet = budget.smart_truncate(code_summary, max_tokens=1500)

    cache_key = budget.content_hash(snippet)
    cached = budget.cache_get(cache_key)
    if cached:
        suggestions = cached.get("suggestions", "")
        print(f"(Cached suggestions)\n{suggestions}")
    else:
        if not budget.budget_ok(2000):
            print(f"Budget too low for improvement cycle. {budget.status()}")
            return

        system = (
            "You are a Python expert. Review this video editor code. "
            "List max 3 specific, actionable improvements. Be concise. No code — just descriptions."
        )
        try:
            client = KimiClient()
            suggestions = client.chat(snippet, system_prompt=system, temperature=0.4, max_tokens=400)
            budget.cache_set(cache_key, {"suggestions": suggestions})
            budget.record_tokens(2000)
            print(f"Kimi suggestions:\n{suggestions}\n")
        except Exception as e:
            print(f"Kimi review failed: {e}")
            return

    # Ask Claude CLI to implement
    claude_prompt = (
        f"Improve the video editor in {EDITOR_DIR}. "
        f"Apply these specific improvements (one at a time, carefully):\n\n{suggestions}"
    )
    print("Sending to Claude CLI to implement...\n")
    try:
        result = subprocess.run(
            ["claude", "-p", claude_prompt, "--max-turns", "5"],
            cwd=str(PROJECT),
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            print("Claude implemented improvements.")
            print(result.stdout[-600:])
        else:
            print(f"Claude failed:\n{result.stderr[:300]}")
    except FileNotFoundError:
        print("claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
    except subprocess.TimeoutExpired:
        print("Claude timed out.")


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Kimi Loop — automated video processor")
    sub = parser.add_subparsers(dest="cmd")

    wp = sub.add_parser("watch", help="Watch a folder for new videos")
    wp.add_argument("folder", help="Path to watch")
    wp.add_argument("--once", action="store_true", help="Process existing unprocessed then exit")

    sub.add_parser("improve", help="Kimi reviews code, Claude implements fixes")
    sub.add_parser("budget",  help="Show today's token usage")

    args = parser.parse_args()

    if args.cmd == "watch":
        watch(args.folder, run_once=args.once)
    elif args.cmd == "improve":
        improve()
    elif args.cmd == "budget":
        print(budget.status())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
