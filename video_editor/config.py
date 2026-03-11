"""Config for Video Editor."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Platform presets: (width, height, max_duration_seconds, max_size_mb)
PLATFORM_PRESETS = {
    "tiktok":           (1080, 1920, 180, 287),
    "instagram_reel":   (1080, 1920, 90,  100),
    "instagram_square": (1080, 1080, 60,  100),
    "youtube_short":    (1080, 1920, 60,  256),
}

class Config:
    AI_API_URL: str  = os.getenv("AI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
    AI_API_KEY: str  = os.getenv("AI_API_KEY", "")
    AI_MODEL: str    = os.getenv("AI_MODEL", "moonshot-v1-8k")

    WHISPER_MODEL: str      = os.getenv("WHISPER_MODEL", "base")
    DEFAULT_PLATFORM: str   = os.getenv("DEFAULT_PLATFORM", "tiktok")

    CAPTION_FONT_SIZE: int         = int(os.getenv("CAPTION_FONT_SIZE", "60"))
    CAPTION_COLOR: str             = os.getenv("CAPTION_COLOR", "white")
    CAPTION_STROKE_COLOR: str      = os.getenv("CAPTION_STROKE_COLOR", "black")
    CAPTION_STROKE_WIDTH: int      = int(os.getenv("CAPTION_STROKE_WIDTH", "3"))
    CAPTION_POSITION: str          = os.getenv("CAPTION_POSITION", "bottom")

    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", str(Path(__file__).parent / "output"))

    @classmethod
    def platform(cls, name: str = None) -> dict:
        p = name or cls.DEFAULT_PLATFORM
        if p not in PLATFORM_PRESETS:
            raise ValueError(f"Unknown platform '{p}'. Choose from: {list(PLATFORM_PRESETS)}")
        w, h, max_dur, max_mb = PLATFORM_PRESETS[p]
        return {"name": p, "width": w, "height": h, "max_duration": max_dur, "max_size_mb": max_mb}
