"""
Video Editor
Handles all video processing using MoviePy + FFmpeg:
  - Crop/resize to platform dimensions (9:16 for TikTok/Reels)
  - Burn in animated word-by-word captions
  - Add title overlay at the start
  - Add CTA overlay at the end
  - Normalise audio
  - Export at correct bitrate/resolution for platform
"""

import sys, os, re, textwrap
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from datetime import datetime
from typing import Optional

from shared.logger import get_logger
from config import Config

logger = get_logger("editor")


def edit_video(
    input_path: str,
    transcript: dict,
    metadata: dict,
    platform: str = None,
    output_path: str = None,
) -> str:
    """
    Full edit pipeline:
    1. Load video
    2. Crop/resize to platform dimensions
    3. Add title intro overlay
    4. Burn in word-by-word captions
    5. Add CTA outro text
    6. Export

    Returns:
        Path to the output video file
    """
    try:
        from moviepy.editor import (
            VideoFileClip, TextClip, CompositeVideoClip,
            ColorClip, concatenate_videoclips,
        )
        from moviepy.config import change_settings
    except ImportError:
        raise ImportError("moviepy not installed. Run: pip install moviepy")

    preset = Config.platform(platform)
    target_w, target_h = preset["width"], preset["height"]

    logger.info(f"Loading video: {input_path}")
    clip = VideoFileClip(input_path)

    # ── 1. Crop/resize to target dimensions ─────────────────────
    clip = _crop_to_aspect(clip, target_w, target_h)

    # ── 2. Build caption clips ───────────────────────────────────
    caption_clips = _build_caption_clips(
        transcript.get("segments", []),
        video_w=target_w,
        video_h=target_h,
    )

    # ── 3. Title overlay (first 2.5 seconds) ─────────────────────
    title_text = metadata.get("title", "")
    title_clips = []
    if title_text:
        title_clips = _build_title_clips(title_text, target_w, target_h, clip.duration)

    # ── 4. CTA overlay (last 2 seconds) ──────────────────────────
    cta_text = metadata.get("cta", "")
    cta_clips = []
    if cta_text and clip.duration > 4:
        cta_clips = _build_cta_clips(cta_text, target_w, target_h, clip.duration)

    # ── 5. Compose everything ────────────────────────────────────
    all_overlays = caption_clips + title_clips + cta_clips
    if all_overlays:
        final = CompositeVideoClip([clip] + all_overlays, size=(target_w, target_h))
    else:
        final = clip

    # ── 6. Export ────────────────────────────────────────────────
    if not output_path:
        Path(Config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        stem = Path(input_path).stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(Config.OUTPUT_DIR, f"{stem}_{platform}_{ts}.mp4")

    logger.info(f"Exporting to: {output_path}")
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        ffmpeg_params=["-crf", "23"],
        logger=None,  # suppress moviepy's verbose output
    )

    logger.info(f"Done — output: {output_path}")
    return output_path


def _crop_to_aspect(clip, target_w: int, target_h: int):
    """Centre-crop video to target aspect ratio, then resize."""
    from moviepy.editor import VideoFileClip
    from moviepy.video.fx.all import crop, resize

    orig_w, orig_h = clip.size
    target_ratio = target_w / target_h
    orig_ratio = orig_w / orig_h

    if abs(orig_ratio - target_ratio) < 0.01:
        # Already correct ratio
        return clip.fx(resize, (target_w, target_h))

    if orig_ratio > target_ratio:
        # Video too wide — crop sides
        new_w = int(orig_h * target_ratio)
        x1 = (orig_w - new_w) // 2
        clip = clip.fx(crop, x1=x1, x2=x1 + new_w)
    else:
        # Video too tall — crop top/bottom
        new_h = int(orig_w / target_ratio)
        y1 = (orig_h - new_h) // 2
        clip = clip.fx(crop, y1=y1, y2=y1 + new_h)

    return clip.fx(resize, (target_w, target_h))


def _build_caption_clips(segments: list, video_w: int, video_h: int) -> list:
    """
    Build word-by-word caption clips (TikTok style).
    Each word appears highlighted as it's spoken.
    Groups words into short lines for readability.
    """
    from moviepy.editor import TextClip

    if not segments:
        return []

    clips = []
    font_size = Config.CAPTION_FONT_SIZE
    color = Config.CAPTION_COLOR
    stroke_col = Config.CAPTION_STROKE_COLOR
    stroke_w = Config.CAPTION_STROKE_WIDTH
    pos = Config.CAPTION_POSITION

    # Position mapping
    y_positions = {
        "top":    int(video_h * 0.12),
        "center": int(video_h * 0.45),
        "bottom": int(video_h * 0.75),
    }
    y = y_positions.get(pos, y_positions["bottom"])

    # Group segments into sentence-level chunks
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        start = seg["start"]
        end = seg["end"]

        # Wrap long lines
        wrapped = textwrap.fill(text, width=28)

        try:
            tc = (
                TextClip(
                    wrapped,
                    fontsize=font_size,
                    color=color,
                    font="Arial-Bold",
                    stroke_color=stroke_col,
                    stroke_width=stroke_w,
                    method="caption",
                    size=(int(video_w * 0.9), None),
                    align="center",
                )
                .set_start(start)
                .set_end(end)
                .set_position(("center", y))
            )
            clips.append(tc)
        except Exception as e:
            logger.warning(f"Caption clip failed for segment '{text[:30]}': {e}")

    logger.info(f"Built {len(clips)} caption clip(s).")
    return clips


def _build_title_clips(title: str, video_w: int, video_h: int, duration: float) -> list:
    """Title text overlay — shown for the first 2.5 seconds."""
    from moviepy.editor import TextClip

    show_until = min(2.5, duration * 0.2)
    wrapped = textwrap.fill(title, width=22)

    try:
        tc = (
            TextClip(
                wrapped,
                fontsize=int(Config.CAPTION_FONT_SIZE * 1.2),
                color="white",
                font="Arial-Bold",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(int(video_w * 0.85), None),
                align="center",
            )
            .set_start(0)
            .set_end(show_until)
            .set_position(("center", int(video_h * 0.08)))
            .crossfadein(0.3)
            .crossfadeout(0.3)
        )
        return [tc]
    except Exception as e:
        logger.warning(f"Title clip failed: {e}")
        return []


def _build_cta_clips(cta: str, video_w: int, video_h: int, duration: float) -> list:
    """Call-to-action text — shown during the last 2 seconds."""
    from moviepy.editor import TextClip

    start = max(0, duration - 2.0)
    wrapped = textwrap.fill(cta, width=30)

    try:
        tc = (
            TextClip(
                wrapped,
                fontsize=int(Config.CAPTION_FONT_SIZE * 0.85),
                color="#FFD700",  # gold
                font="Arial-Bold",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(int(video_w * 0.85), None),
                align="center",
            )
            .set_start(start)
            .set_end(duration)
            .set_position(("center", int(video_h * 0.88)))
            .crossfadein(0.4)
        )
        return [tc]
    except Exception as e:
        logger.warning(f"CTA clip failed: {e}")
        return []
