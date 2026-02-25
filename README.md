# Multi-Market Paper Trading Bot

A paper trading bot for testing strategies across **Polymarket** and **Kalshi** prediction markets. Focuses on identifying contracts priced at 97-98 cents with high probability of resolving to YES.

## ⚠️ Disclaimer

This is for **PAPER TRADING ONLY** - no real money is traded. Use this to test strategies before risking capital.

## 🎯 Features

- ✅ **Multi-Market Support**: Scan both Polymarket AND Kalshi simultaneously
- ✅ **Configurable Fees**: Adjust fee rates to match different platforms
- ✅ **Demo Mode**: Test with simulated data (per-market or combined)
- ✅ **Performance Tracking**: Detailed statistics with fee breakdown
- ✅ **Auto-Execution**: Automatically enters and exits paper trades
- ✅ **Market Source Tracking**: Know which platform each trade came from

## Strategy

The bot looks for:
- YES tokens priced between 97-98 cents (configurable)
- Sufficient liquidity (>$1000)
- Minimum 24h volume (>$500)
- Automatically enters paper trades
- Tracks performance with realistic fee simulation (configurable, default 2%)

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Test Kalshi API connectivity (optional)
python3 test_kalshi_api.py
```

## ⚠️ API Access Note

- **Polymarket API**: Currently returns 503 errors (may be temporary)
- **Kalshi API**: Ready to use - test with `python3 test_kalshi_api.py`
- **Demo Mode**: Works perfectly for both markets without API access

See `KALSHI_SETUP.md` for detailed API setup instructions.

## Usage

### Demo Mode (Recommended for Testing)

**Both markets in demo mode:**
```bash
python3 bot.py --demo-poly --demo-kalshi --scan
python3 bot.py --demo-poly --demo-kalshi --run
```

**Polymarket demo only (Real Kalshi):**
```bash
python3 bot.py --demo-poly --scan
```

**Kalshi demo only (Real Polymarket):**
```bash
python3 bot.py --demo-kalshi --scan
```

### Selecting Markets

**Scan only Polymarket (disable Kalshi):**
```bash
python3 bot.py --no-kalshi --scan
```

**Scan only Kalshi (disable Polymarket):**
```bash
python3 bot.py --no-poly --scan
```

**Combine with demo modes:**
```bash
# Only Kalshi in demo mode
python3 bot.py --demo-kalshi --no-poly --scan

# Only Polymarket in demo mode
python3 bot.py --demo-poly --no-kalshi --scan
```

### Live Mode (Real Market Data)

**Single scan:**
```bash
python3 bot.py --scan
```

**Continuous monitoring:**
```bash
python3 bot.py --run
```

**View statistics:**
```bash
python3 bot.py --stats
```

**View open positions:**
```bash
python3 bot.py --positions
```

## Configuration

Edit `config.py` to adjust:

### Trading Parameters
- `MIN_PRICE` / `MAX_PRICE`: Price range (default 0.97-0.98)
- `POLYMARKET_FEE`: Fee rate (default 0.02 = 2%)
- `POSITION_SIZE`: Size of each paper trade (default $100)
- `MAX_POSITIONS`: Maximum concurrent positions (default 10)

### Market Selection
- `ENABLE_POLYMARKET`: Enable/disable Polymarket (default True)
- `ENABLE_KALSHI`: Enable/disable Kalshi (default True)

### Filters
- `MIN_LIQUIDITY`: Minimum market liquidity (default $1000)
- `MIN_VOLUME_24H`: Minimum 24h volume (default $500)
- `REFRESH_INTERVAL`: Scan frequency (default 60 seconds)

## How It Works

1. **Scans Multiple Markets** - Polymarket and Kalshi simultaneously
2. **Identifies Opportunities** - YES tokens in 97-98c range from both platforms
3. **Filters** by liquidity and volume
4. **Enters Paper Trades** automatically with market source tracking
5. **Monitors Positions** - updates prices and closes winning/losing trades
6. **Tracks Performance** - calculates P&L, fees, win rate, ROI by market source

## Performance Tracking

All trades stored in `paper_trades.db` (SQLite):
- Entry/exit prices and timestamps
- Market source (Polymarket or Kalshi)
- Win/loss outcomes
- Profit/loss with fee breakdown
- Win rate and ROI

## Exit Conditions

Trades automatically close when:
- **WIN**: Price reaches ≥99c (market resolving to YES)
- **LOSS**: Price drops <80c (likely resolving to NO)

## Example Output

```
============================================================
  MULTI-MARKET PAPER TRADING BOT
  Target: 97-98c contracts
  Markets: Polymarket, Kalshi
  MODE: DEMO (Simulated Data)
============================================================

📊 Found 12 opportunities:

#    Question                                      Price    Volume       Market       Category
----------------------------------------------------------------------------------------------------
1    S&P 500 above 6000 by end of week?            $0.979   $291,503     kalshi       Finance
2    Will Lakers win tonight's game?               $0.978   $44,481      polymarket   Sports
3    Fed cuts rates in March 2026?                 $0.975   $311,433     kalshi       Politics

✅ ENTERED TRADE #1 [KALSHI]
   Market: S&P 500 above 6000 by end of week?
   Entry Price: $0.979
   Position Size: $100
   Shares: 102.11

   ✅ Trade #5 WON [POLYMARKET] - Will Lakers win tonight's game?

PERFORMANCE STATISTICS
  Total Trades:     2
  Wins:             2
  Losses:           0
  Win Rate:         100.0%
  Total P&L:        $5.15
  Total Fees Paid:  $0.11 (2.0% on profits)
  Avg Profit/Trade: $2.58
  ROI:              2.58%
```

## Fee Configuration

The bot uses a configurable fee system:

```python
# In config.py
POLYMARKET_FEE = 0.02  # 2% on profits
```

Fees are:
- Applied only to winning trades
- Calculated on profit portion only
- Fully tracked in statistics

Test different fee structures:
- `0.01` = 1% fees (optimistic)
- `0.02` = 2% fees (realistic for Polymarket)
- `0.03` = 3% fees (conservative)

## Comparing Markets

The bot tracks which market each trade comes from, allowing you to:
- Compare win rates between Polymarket and Kalshi
- Identify which platform has better opportunities
- Optimize which markets to focus on

## Next Steps

After paper trading:
1. Run in demo mode for several days to collect data
2. Analyze which platform performs better
3. Test different price ranges and fee assumptions
4. Identify best-performing categories
5. Consider real trading only if strategy proves profitable

## Notes

- Markets can still reverse even at 98c
- Transaction fees significantly impact thin margins
- Liquidity at high prices may be limited
- Different platforms have different fee structures
- Past performance doesn't guarantee future results
- Always verify fee rates before real trading
