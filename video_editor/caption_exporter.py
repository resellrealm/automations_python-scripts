"""
Caption Exporter
Exports captions in multiple formats alongside the video:
  - .srt  — standard subtitle file (works everywhere)
  - .txt  — plain transcript
  - metadata.json — title, description, hashtags, CTA for copy-paste

These files are saved next to the output video for easy uploading.
"""

import json, os
from pathlib import Path
from transcriber import segments_to_srt
from shared.logger import get_logger

logger = get_logger("caption_exporter")


def export_all(output_video_path: str, transcript: dict, metadata: dict):
    """
    Export all sidecar files next to the output video.

    Creates:
        video.srt           — subtitles
        video_transcript.txt — plain text
        video_metadata.json  — social post data
        video_post.txt       — ready-to-paste social post
    """
    base = Path(output_video_path).with_suffix("")

    # ── SRT ──────────────────────────────────────────────
    srt_path = str(base) + ".srt"
    srt_content = segments_to_srt(transcript.get("segments", []))
    _write(srt_path, srt_content)

    # ── Transcript ───────────────────────────────────────
    txt_path = str(base) + "_transcript.txt"
    _write(txt_path, transcript.get("text", ""))

    # ── Metadata JSON ────────────────────────────────────
    meta_path = str(base) + "_metadata.json"
    _write(meta_path, json.dumps(metadata, indent=2, ensure_ascii=False))

    # ── Ready-to-paste post ───────────────────────────────
    post = _build_post_text(metadata)
    post_path = str(base) + "_post.txt"
    _write(post_path, post)

    logger.info(f"Exports saved: .srt, _transcript.txt, _metadata.json, _post.txt")
    return {
        "srt": srt_path,
        "transcript": txt_path,
        "metadata": meta_path,
        "post": post_path,
    }


def _build_post_text(metadata: dict) -> str:
    title = metadata.get("title", "")
    desc = metadata.get("description", "")
    cta = metadata.get("cta", "")
    hashtags = " ".join(f"#{t.lstrip('#')}" for t in metadata.get("hashtags", []))

    parts = [p for p in [title, "", desc, "", cta, "", hashtags] if p is not None]
    return "\n".join(parts).strip()


def _write(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
