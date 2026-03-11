"""
Video Editor — Main Entry Point
================================
Usage:
    python main.py input.mp4
    python main.py input.mp4 --platform tiktok
    python main.py input.mp4 --platform instagram_reel --title "My Title"
    python main.py input.mp4 --no-ai          # skip AI title generation
    python main.py input.mp4 --captions-only  # only transcribe, no edit

Platforms:
    tiktok              1080x1920, up to 3 min
    instagram_reel      1080x1920, up to 90 sec
    instagram_square    1080x1080, up to 60 sec
    youtube_short       1080x1920, up to 60 sec

Output files (saved to output/ folder):
    video.mp4           — edited video, ready to post
    video.srt           — subtitle file
    video_post.txt      — ready-to-paste caption + hashtags
    video_metadata.json — full metadata (title, description, hashtags, CTA)
"""

import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from config import Config
from shared.logger import get_logger
import transcriber as transcriber_mod
import ai_enhancer
import editor as editor_mod
import caption_exporter

logger = get_logger("video_editor", log_dir="logs")


def main():
    parser = argparse.ArgumentParser(
        description="Video Editor — auto-captions, title, and platform formatting"
    )
    parser.add_argument("input", help="Path to input video file")
    parser.add_argument(
        "--platform", "-p",
        default=Config.DEFAULT_PLATFORM,
        choices=["tiktok", "instagram_reel", "instagram_square", "youtube_short"],
        help="Target platform (default: tiktok)"
    )
    parser.add_argument("--title", "-t", default=None, help="Override title (skips AI generation)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI metadata generation")
    parser.add_argument("--captions-only", action="store_true", help="Only transcribe and export SRT, no video edit")
    parser.add_argument("--output", "-o", default=None, help="Custom output path for video")
    parser.add_argument("--whisper-model", default=None, help="Override Whisper model size")
    args = parser.parse_args()

    input_path = args.input
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    if args.whisper_model:
        Config.WHISPER_MODEL = args.whisper_model

    print(f"\n{'='*55}")
    print(f"  Video Editor")
    print(f"  Input:    {input_path}")
    print(f"  Platform: {args.platform}")
    print(f"{'='*55}\n")

    # ── Step 1: Transcribe ─────────────────────────────────
    print("Step 1/3 — Transcribing audio (local Whisper, no API cost)...")
    transcript = transcriber_mod.transcribe(input_path)
    print(f"  Transcript: {transcript['text'][:100]}...")

    # ── Step 2: Generate metadata ──────────────────────────
    if args.captions_only:
        # Just save SRT and exit
        base = Path(input_path).stem
        srt_path = str(Path(Config.OUTPUT_DIR) / f"{base}.srt")
        Path(Config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        from transcriber import segments_to_srt
        srt = segments_to_srt(transcript["segments"])
        with open(srt_path, "w") as f:
            f.write(srt)
        print(f"\n  SRT saved: {srt_path}\n")
        return

    print("Step 2/3 — Generating metadata...")
    if args.no_ai or not Config.AI_API_KEY:
        metadata = ai_enhancer._placeholder(transcript["text"])
        print("  (AI skipped — using placeholder metadata)")
    else:
        metadata = ai_enhancer.generate_metadata(transcript["text"], args.platform)

    if args.title:
        metadata["title"] = args.title

    print(f"  Title:    {metadata.get('title')}")
    print(f"  Hashtags: {' '.join(('#' + t.lstrip('#')) for t in metadata.get('hashtags', [])[:5])}...")

    # ── Step 3: Edit video ─────────────────────────────────
    print("Step 3/3 — Editing video (cropping, captions, title overlay)...")
    output_path = editor_mod.edit_video(
        input_path=input_path,
        transcript=transcript,
        metadata=metadata,
        platform=args.platform,
        output_path=args.output,
    )

    # ── Export sidecar files ────────────────────────────────
    exports = caption_exporter.export_all(output_path, transcript, metadata)

    print(f"\n{'='*55}")
    print(f"  DONE!")
    print(f"  Video:       {output_path}")
    print(f"  Subtitles:   {exports['srt']}")
    print(f"  Post copy:   {exports['post']}")
    print(f"  Metadata:    {exports['metadata']}")
    print(f"{'='*55}")
    print(f"\n  Ready-to-post caption:\n")

    with open(exports["post"], "r") as f:
        print(f.read())
    print()


if __name__ == "__main__":
    main()
