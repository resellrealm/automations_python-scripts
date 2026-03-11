"""
Transcriber
Runs OpenAI Whisper locally to transcribe speech from video.
100% local — zero API tokens used.

Returns word-level timestamps for rendering animated captions.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logger import get_logger
from config import Config

logger = get_logger("transcriber")


def transcribe(video_path: str) -> dict:
    """
    Transcribe audio from a video file using Whisper.

    Returns:
        {
            "text": "full transcript",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "Hello world", "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.6},
                    {"word": "world", "start": 0.7, "end": 1.5},
                ]}
            ]
        }
    """
    try:
        import whisper
    except ImportError:
        raise ImportError("openai-whisper not installed. Run: pip install openai-whisper")

    logger.info(f"Loading Whisper model '{Config.WHISPER_MODEL}'...")
    model = whisper.load_model(Config.WHISPER_MODEL)

    logger.info(f"Transcribing: {video_path}")
    result = model.transcribe(
        video_path,
        word_timestamps=True,   # needed for word-level caption animation
        verbose=False,
    )

    segments = []
    for seg in result.get("segments", []):
        words = []
        for w in seg.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": round(w["start"], 3),
                "end": round(w["end"], 3),
            })
        segments.append({
            "start": round(seg["start"], 3),
            "end": round(seg["end"], 3),
            "text": seg["text"].strip(),
            "words": words,
        })

    full_text = result.get("text", "").strip()
    language = result.get("language", "en")
    logger.info(f"Transcription done — {len(segments)} segment(s), language: {language}")
    logger.debug(f"Full text: {full_text[:200]}")

    return {"text": full_text, "language": language, "segments": segments}


def segments_to_srt(segments: list) -> str:
    """Convert Whisper segments to SRT subtitle format."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_time(seg["start"])
        end = _format_time(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    return "\n".join(lines)


def _format_time(seconds: float) -> str:
    """Convert seconds to SRT time format: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
