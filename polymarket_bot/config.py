import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")


class Config:
    PRIVATE_KEY: str       = os.getenv("POLYGON_PRIVATE_KEY", "")
    RPC_URL: str           = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    CLOB_HOST: str         = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
    GAMMA_HOST: str        = os.getenv("GAMMA_HOST", "https://gamma-api.polymarket.com")

    AI_API_URL: str        = os.getenv("AI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
    AI_API_KEY: str        = os.getenv("AI_API_KEY", "")
    AI_MODEL: str          = os.getenv("AI_MODEL", "moonshot-v1-8k")

    STRATEGY: str          = os.getenv("STRATEGY", "flash_crash")
    MAX_POSITION_USDC: float = float(os.getenv("MAX_POSITION_USDC", "50.0"))
    MIN_EDGE_PCT: float    = float(os.getenv("MIN_EDGE_PCT", "3.0"))
    MAX_OPEN_POSITIONS: int = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
    DRY_RUN: bool          = os.getenv("DRY_RUN", "true").lower() == "true"

    FLASH_CRASH_DROP_PCT: float   = float(os.getenv("FLASH_CRASH_DROP_PCT", "15.0"))
    FLASH_CRASH_TARGET_PCT: float = float(os.getenv("FLASH_CRASH_TARGET_PCT", "8.0"))

    MM_SPREAD_PCT: float      = float(os.getenv("MM_SPREAD_PCT", "3.0"))
    MM_INVENTORY_LIMIT: float = float(os.getenv("MM_INVENTORY_LIMIT", "100.0"))

    DB_PATH: str           = str(Path(__file__).parent / "positions.db")
