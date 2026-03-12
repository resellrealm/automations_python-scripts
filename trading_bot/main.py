"""
Optimised Crypto Trading Bot
=============================
Strategies: RSI+EMA, MACD+Bollinger Bands, Combined (all signals)
Risk:        1% rule, ATR-based stops, trailing stop, take-profit
Exchange:    Any CCXT-supported exchange (Binance, Kraken, Bybit, OKX...)
Backtest:    Borrowed from freqtrade-strategies community patterns

Usage:
    python main.py                    # Live/dry-run trading daemon
    python main.py --once             # Single cycle then exit
    python main.py --backtest         # Backtest on historical data
    python main.py --report           # Show trade summary
    python main.py --pair BTC/USDT    # Override pair for this run
"""

import sys, os, time, signal, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from shared.logger import get_logger
from exchange_client import ExchangeClient
from strategies import get_signal
from risk_manager import calculate_position_size, check_trailing_stop, should_exit
import database as db

logger = get_logger("trading_bot", log_dir="logs")
_running = True


def _handle_signal(s, f):
    global _running
    logger.info("Stopping bot...")
    _running = False


def run_cycle(exchange: ExchangeClient):
    """Single trading cycle across all configured pairs."""
    balance = exchange.get_balance()
    open_trades = {t["pair"]: dict(t) for t in db.get_open_trades()}

    for pair in Config.TRADING_PAIRS:
        try:
            df = exchange.get_ohlcv(pair)
            if df.empty or len(df) < 50:
                logger.warning(f"Not enough data for {pair}")
                continue

            current_price = float(df["close"].iloc[-1])
            signal = get_signal(df, Config.STRATEGY)
            atr_val = float(df["atr"].iloc[-1])

            # ── Check open trades for this pair ──────────────
            if pair in open_trades:
                trade = open_trades[pair]
                highest = trade.get("highest_price", trade["entry_price"])
                highest = max(highest, current_price)

                exit_reason = should_exit(
                    trade["entry_price"], current_price,
                    trade["stop_price"], trade["take_profit"]
                )
                trailing = check_trailing_stop(trade["entry_price"], current_price, highest)

                if exit_reason != "hold" or trailing:
                    reason = "trailing_stop" if trailing else exit_reason
                    exchange.place_order(pair, "sell", trade["size"])
                    db.close_trade(trade["id"], current_price, reason)
                    pnl_pct = ((current_price - trade["entry_price"]) / trade["entry_price"]) * 100
                    logger.info(f"CLOSED {pair} | reason={reason} | P&L={pnl_pct:.2f}%")
                else:
                    logger.info(f"{pair} | HOLD | price={current_price} signal={signal}")
                continue

            # ── Open new trade on BUY signal ─────────────────
            if signal == "BUY" and len(open_trades) < Config.MAX_OPEN_TRADES:
                sizing = calculate_position_size(balance, current_price, atr_val)
                if sizing["size"] <= 0:
                    logger.warning(f"Position size 0 for {pair} — skipping.")
                    continue

                order = exchange.place_order(pair, "buy", sizing["size"])
                trade_id = db.open_trade(
                    pair=pair, side="buy", strategy=Config.STRATEGY,
                    entry_price=current_price, size=sizing["size"],
                    stop_price=sizing["stop_price"], take_profit=sizing["take_profit"],
                    dry_run=Config.DRY_RUN,
                )
                logger.info(
                    f"OPENED {pair} | entry={current_price} stop={sizing['stop_price']} "
                    f"tp={sizing['take_profit']} size={sizing['size']} risk=${sizing['risk_amount']}"
                )
            else:
                logger.info(f"{pair} | {signal} | price={current_price:.4f} | balance=${balance:.2f}")

        except Exception as e:
            logger.error(f"Error on {pair}: {e}", exc_info=True)


def run_backtest(exchange: ExchangeClient):
    """Simple backtest on historical OHLCV data."""
    print(f"\n{'='*55}")
    print(f"  Backtest — Strategy: {Config.STRATEGY}")
    print(f"  Pairs: {Config.TRADING_PAIRS} | Timeframe: {Config.TIMEFRAME}")
    print(f"{'='*55}\n")

    for pair in Config.TRADING_PAIRS:
        df = exchange.get_ohlcv(pair, limit=500)
        if df.empty:
            print(f"  {pair}: no data")
            continue

        trades, wins, total_pnl = 0, 0, 0.0
        in_trade = False
        entry = stop = tp = 0.0

        for i in range(50, len(df)):
            chunk = df.iloc[:i]
            price = float(df["close"].iloc[i])
            atr_v = float(df["atr"].iloc[i]) if "atr" in df.columns else price * 0.01

            if not in_trade:
                sig = get_signal(chunk, Config.STRATEGY)
                if sig == "BUY":
                    sizing = calculate_position_size(1000, price, atr_v)
                    entry, stop, tp = price, sizing["stop_price"], sizing["take_profit"]
                    in_trade = True
            else:
                if price <= stop:
                    pnl = ((price - entry) / entry) * 100
                    total_pnl += pnl
                    trades += 1
                    in_trade = False
                elif price >= tp:
                    pnl = ((price - entry) / entry) * 100
                    total_pnl += pnl
                    wins += 1
                    trades += 1
                    in_trade = False

        win_rate = (wins / trades * 100) if trades else 0
        print(f"  {pair}: {trades} trades | Win rate: {win_rate:.1f}% | Total P&L: {total_pnl:.2f}%")

    print()


def main():
    parser = argparse.ArgumentParser(description="Optimised Crypto Trading Bot")
    parser.add_argument("--once",      action="store_true")
    parser.add_argument("--backtest",  action="store_true")
    parser.add_argument("--report",    action="store_true")
    parser.add_argument("--pair",      default=None)
    args = parser.parse_args()

    if args.pair:
        Config.TRADING_PAIRS = [args.pair]

    db.init_db()
    exchange = ExchangeClient()

    if args.report:
        s = db.get_summary()
        print(f"\n{'='*45}")
        print(f"  Trading Bot — Results")
        print(f"{'='*45}")
        print(f"  Total trades : {s.get('total', 0)}")
        print(f"  Wins / Losses: {s.get('wins', 0)} / {s.get('losses', 0)}")
        print(f"  Total P&L    : ${s.get('total_pnl', 0)}")
        print(f"  Avg P&L %    : {s.get('avg_pnl_pct', 0)}%")
        print(f"  Open trades  : {s.get('open', 0)}")
        print(f"{'='*45}\n")
        return

    if args.backtest:
        run_backtest(exchange)
        return

    mode = "[DRY RUN]" if Config.DRY_RUN else "[LIVE]"
    logger.info(f"Bot started {mode} | strategy={Config.STRATEGY} | pairs={Config.TRADING_PAIRS}")

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if args.once:
        run_cycle(exchange)
        return

    # Map timeframe to seconds for sleep
    tf_seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}
    sleep = tf_seconds.get(Config.TIMEFRAME, 3600)

    while _running:
        run_cycle(exchange)
        if _running:
            logger.info(f"Sleeping {Config.TIMEFRAME} ({sleep}s)...")
            for _ in range(sleep):
                if not _running:
                    break
                time.sleep(1)


if __name__ == "__main__":
    main()
