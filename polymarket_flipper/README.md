# Polymarket Flipper — £5/trade, £5/day

Standalone bot targeting ~8 profitable flips/day on Polymarket using 3 proven strategies.

## Risk Profile
| Setting | Value |
|---|---|
| Risk per trade | £5 (~$6.35 USDC) |
| Daily loss limit | £5 hard stop |
| Target trades/day | ~8 |

## Strategies

### 1. Flash Crash (86% ROI documented)
Fires when YES price drops ≥15% in one tick AND YES + NO bundle ≤ $0.95.
Buying both legs guarantees $1.00 at resolution — locked profit of 5¢+.

**Proven params:** 15% drop threshold, sum ≤ 0.95, 2-min confirmation.
**Wrong params (1% drop, 0.60 sum) = -50% loss — don't change.**

### 2. Orderbook Imbalance
When bid volume is 2.5× ask volume near window close (T-10s to T-300s),
price tends to drift toward the heavy side. Only enters if net edge > 3¢ after the 3.15% taker fee.

### 3. NO Bias
~70% of Polymarket markets resolve NO (on-chain data, 95M+ transactions).
Buys NO at 55–85¢ on non-crypto, non-election markets with >$5k volume.
Avoids markets within 24h of resolution.

## Setup

```bash
cd polymarket_flipper
pip install -r requirements.txt
cp .env.example .env
# Fill in your Polymarket API credentials in .env
```

### Getting API credentials
1. Go to polymarket.com → Settings → API Keys
2. Create new API key — copy key, secret, passphrase
3. Your private key is your EVM wallet key (used to sign orders)

## Usage

```bash
# Dry run — simulate without real orders
python main.py --dry-run

# Live trading
python main.py

# One cycle and exit (good for testing)
python main.py --once --dry-run

# 30-day P&L report
python main.py --report
```

## VPS Deployment

```bash
# Run as background daemon
nohup python main.py >> flipper.log 2>&1 &

# Or with systemd (recommended)
# Create /etc/systemd/system/polymarket-flipper.service
```

## Fee Awareness
- Taker fee: **3.15%** at 50/50 markets
- Flash crash strategy is fee-immune (guaranteed $1.00 payout)
- OB Mismatch only enters when net edge > 3.15% fee
- NO bias entries at 55–85¢ — fee is ~3¢ on a 55¢ buy, manageable

## Infrastructure Note
For latency arb (not included here), you need VPS < 200ms from Polygon RPC.
These 3 strategies work fine on home internet / standard VPS.
