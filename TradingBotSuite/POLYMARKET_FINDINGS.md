# Polymarket Bot — Documented Findings & Real Data
## Research Date: March 2026

This document contains ONLY strategies with real, documented results.
All numbers sourced from on-chain analysis, Medium research articles, and public bot disclosures.

---

## 🏆 HEADLINE RESULTS (Documented)

| Bot / Trader | Capital | Profit | Return | Strategy |
|---|---|---|---|---|
| 0x8dxd bot | $313 | $437,600 | **139,000%** | Latency arb vs Binance spot lag |
| Igor Mikerin ensemble | Unknown | **$2.2M** | — | AI ensemble probability models |
| Arbitrage bot (8,894 trades) | — | $150,000 | $16.80/trade | YES+NO < $1.00 bundle |
| Top individual trader | — | $2.01M | — | 4,049 transactions |
| Market maker (election season) | $10,000 | $200–$800/day | 20x at peak | Liquidity rewards + spread |
| Flash crash backtest | $1,000 | $869 | **86% ROI** | Flash crash with proven params |

**Industry wide:** $40M extracted via arbitrage, $20M via market making (Apr 2024–Apr 2025)

---

## ✅ STRATEGY 1: Flash Crash / Momentum Reversal
**Status: WORKS — 86% ROI documented**

### Proven Parameters (DO NOT change — wrong params → -50% loss)
```
crash_threshold:      15% price drop in one candle   ← CRITICAL
sum_target:           0.95 (buy when YES+NO ≤ 0.95)  ← CRITICAL
observation_window:   2 minutes                       ← CRITICAL
position_size:        20 shares per trade
markets:              15-minute BTC/ETH/SOL UP/DOWN
```

### What Happens
1. Monitor 15-min BTC/ETH/SOL markets every tick
2. When YES price drops ≥15% in one candle → BUY YES
3. Simultaneously check: can buy NO such that YES_price + NO_price ≤ 0.95?
4. If YES → execute both legs (bundle guaranteed to pay $1.00 at resolution)
5. Hold until resolution

### Why it Works
- Flash crashes are often panic/noise — prices recover or resolve at $1.00
- Buying both legs below $0.95 locks in ≥$0.05 per bundle guaranteed
- 15-min markets resolve quickly — capital isn't locked long

### What FAILS (documented -50% loss)
```
crash_threshold: 1%     ← too sensitive, trades noise
sum_target: 0.60        ← too greedy, almost never fills
observation_window: 15m ← too slow, window closes
```

---

## ✅ STRATEGY 2: Spot Price Latency Arbitrage
**Status: WORKS for bots — $313 → $437,600 documented**

### How It Works
- Polymarket's 15-min crypto markets lag Binance/Coinbase spot prices by 2–12 seconds
- Monitor Binance WebSocket for confirmed BTC/ETH/SOL momentum
- When spot price has clearly moved (e.g. BTC pumped 0.8% in 30s), Polymarket UP market is still at 50/50
- BUY YES (UP) before the market reprices

### Requirements (Brutal)
- Execution latency: **<200ms ideally, <100ms for best edge**
- Sub-100ms bots capture 73% of profits
- Home internet (150ms+): edge disappears
- **VPS close to Polygon RPC + Binance is essential**

### Parameters Used by $437k Bot
- Markets: BTC/ETH/SOL 15-minute UP/DOWN contracts
- Entry: When spot confirms direction at T-45s or later
- Win rate: **98% (6,615 trades)**
- Max single win: $13,300

---

## ✅ STRATEGY 3: 5-Minute Crypto Market Technical Analysis
**Status: WORKS — 55-60% win rate, 20-50% annual ROI backtested on 1,000 candles**

### Signal Weighting System (Documented)
```python
signals = {
    "window_delta":    5-7,   # price direction in window (dominant signal)
    "micro_momentum":  2,     # sub-minute momentum
    "acceleration":    1.5,   # rate of change
    "ema_crossover":   1,     # EMA 9/21 cross
    "rsi_14":          1-2,   # RSI divergence
    "volume_surge":    1,     # volume > 1.5x avg
    "tick_trend":      2,     # real-time tick direction
}
# BUY when sum > 10, SELL when sum < -10
```

### Entry Timing (Critical)
- **Optimal entry: T-10 seconds** before window closes
- Hard deadline: T-5 seconds
- Rationale: Direction is locked in — insufficient time for reversal

### Risk Modes
```
SAFE:       25% bankroll per trade, 30% confidence minimum
AGGRESSIVE: All profits above principal, 20% threshold
```

---

## ✅ STRATEGY 4: Systematic NO Betting
**Status: WORKS — ~70% of Polymarket markets historically resolve NO**

### Why It Works
- Markets are created for events that might happen — most don't
- Long-shot bias: people overbet YES on unlikely events
- Creates consistent edge on NO side in non-election, non-crypto markets

### Parameters
```
market_filter:    avoid binary crypto/sports (too efficient)
best_markets:     political outcomes, regulatory events, company milestones
min_no_price:     0.55 (at least 55¢ for NO = ~45% implied probability)
max_no_price:     0.85 (avoid events that are near-certain to not happen)
position_size:    2% of portfolio per trade
```

### Avoid
- Markets where YES is almost certain (NO too expensive, no edge)
- Crypto price direction markets (efficient, real-time arbitrage)
- Markets within 24h of resolution (binary outcome, no time for mispricing)

---

## ✅ STRATEGY 5: AI Ensemble Probability Mispricing
**Status: WORKS — $2.2M in 2 months documented**

### Core Logic
- Market shows 50/50 but real probability is ~85%
- Feed news + social data into LLM/ensemble model
- When model confidence high AND market underprices → BUY

### Data Sources That Matter
1. Breaking news feeds (Reuters, AP)
2. Twitter/X sentiment on the specific topic
3. Historical base rates for similar events
4. Polling data (politics)
5. Regulatory filing trackers (company events)

### Implementation with Kimi AI (Token-Efficient)
```
System: "You are a prediction market analyst. Based on the news provided,
         estimate the probability of: {market_question}.
         JSON only: {"probability": 0-1, "confidence": 0-1, "reasoning": "<20 words"}"

Input:  Latest 3 news headlines about the topic + current market price
Tokens: ~200 input, ~60 output per call
```

---

## ❌ WHAT'S BEEN ARBED AWAY (Don't Waste Time On These)

| Strategy | Why Dead |
|---|---|
| Simple YES+NO bundle arb | 3.15% taker fee at 50/50 odds kills it. Median spread now only 0.3% |
| Slow latency arb | Windows shrunk 12.3s → 2.7s. 73% captured by sub-100ms bots |
| Blind copy trading | "Destroys 99% of traders." Slippage + win rate decay |
| Market making (post-2024) | "Not profitable, will lose money." Rewards cut after election season |
| Liquidity rewards alone | Reward formula reduced post-election, now competitive race to bottom |

---

## 💰 RISK MANAGEMENT (Proven to Preserve Capital)

```
daily_loss_limit:    5% of total capital
monthly_loss_limit:  15% of total capital
max_drawdown:        25%
position_size:       1-2% per trade (conservative) / 20-25% (flash crash only)
inventory_skew_max:  30% (market making)
stop_loss:           10-15%
```

---

## 🖥️ INFRASTRUCTURE REQUIREMENTS

| Requirement | Why |
|---|---|
| VPS near Polygon RPC | Reduces latency to <50ms |
| WebSocket connections | Polling too slow (>5s lag vs WS) |
| Dedicated RPC node | Shared nodes add 50-200ms of variance |
| Binance WebSocket | Real-time spot feed for latency arb |

**Recommended VPS location:** AWS/GCP/Hetzner in US-East or Frankfurt (closest to Polygon validators)

---

*Sources: Finbold, Yahoo Finance, CoinDesk, Medium/Illumination, HTX Insights, QuantVPS, QuickNode*
