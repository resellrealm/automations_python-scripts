import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")


class Config:
    EXCHANGE: str          = os.getenv("EXCHANGE", "binance")
    API_KEY: str           = os.getenv("API_KEY", "")
    API_SECRET: str        = os.getenv("API_SECRET", "")

    TRADING_PAIRS: list    = [p.strip() for p in os.getenv("TRADING_PAIRS", "BTC/USDT").split(",")]
    TIMEFRAME: str         = os.getenv("TIMEFRAME", "1h")
    RISK_PER_TRADE_PCT: float = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))
    MAX_OPEN_TRADES: int   = int(os.getenv("MAX_OPEN_TRADES", "3"))

    STRATEGY: str          = os.getenv("STRATEGY", "rsi_ema")
    STOPLOSS_PCT: float    = float(os.getenv("STOPLOSS_PCT", "2.0"))
    TAKE_PROFIT_PCT: float = float(os.getenv("TAKE_PROFIT_PCT", "4.0"))
    TRAILING_STOP: bool    = os.getenv("TRAILING_STOP", "true").lower() == "true"

    DRY_RUN: bool          = os.getenv("DRY_RUN", "true").lower() == "true"
    DB_PATH: str           = str(Path(__file__).parent / "trades.db")
