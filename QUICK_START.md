# Quick Start Guide

## 🚀 Command Reference

### Demo Mode (Simulated Data)

```bash
# Both markets in demo mode (recommended for testing)
python3 bot.py --demo-poly --demo-kalshi --scan

# Only Polymarket demo (Kalshi will try real API)
python3 bot.py --demo-poly --scan

# Only Kalshi demo (Polymarket will try real API)
python3 bot.py --demo-kalshi --scan
```

### Market Selection

```bash
# Scan only Polymarket (disable Kalshi)
python3 bot.py --no-kalshi --scan

# Scan only Kalshi (disable Polymarket)
python3 bot.py --no-poly --scan

# Combine: Only Polymarket in demo mode (Kalshi disabled)
python3 bot.py --demo-poly --no-kalshi --scan

# Combine: Only Kalshi in demo mode (Polymarket disabled)
python3 bot.py --demo-kalshi --no-poly --scan
```

### Live Mode (Real Market Data)

```bash
# Both markets with real API data
python3 bot.py --scan

# Continuous monitoring (updates every 60 seconds)
python3 bot.py --run
```

### View Results

```bash
# Show performance statistics
python3 bot.py --stats

# Show open positions
python3 bot.py --positions
```

## 🎯 Typical Workflow

### 1. Initial Testing (Both Markets Demo)
```bash
# Run a few scans to see how it works
python3 bot.py --demo-poly --demo-kalshi --scan
python3 bot.py --demo-poly --demo-kalshi --scan
python3 bot.py --demo-poly --demo-kalshi --scan

# Check results
python3 bot.py --stats
python3 bot.py --positions
```

### 2. Test Real Kalshi API
```bash
# Polymarket in demo, Kalshi with real data
python3 bot.py --demo-poly --scan

# If that works, try continuous mode
python3 bot.py --demo-poly --run
```

### 3. Go Fully Live (When Ready)
```bash
# Both markets with real data
python3 bot.py --scan

# If satisfied, run continuous
python3 bot.py --run
```

## ⚙️ Quick Configuration Changes

### Change Price Range
```bash
# Edit config.py
MIN_PRICE = 0.95  # Lower threshold to 95c
MAX_PRICE = 0.97  # Upper threshold to 97c
```

### Adjust Fee Rate
```bash
# Edit config.py
POLYMARKET_FEE = 0.01  # Test with 1% fees
POLYMARKET_FEE = 0.03  # Test with 3% fees
```

### Enable/Disable Markets (Command Line - Recommended)
```bash
# Disable Kalshi (scan only Polymarket)
python3 bot.py --no-kalshi --scan

# Disable Polymarket (scan only Kalshi)
python3 bot.py --no-poly --scan
```

### Enable/Disable Markets (Config File - Persistent)
```bash
# Edit config.py for permanent changes
ENABLE_POLYMARKET = False  # Only scan Kalshi
ENABLE_KALSHI = False      # Only scan Polymarket
```

### Change Position Size
```bash
# Edit config.py
POSITION_SIZE = 50   # $50 per trade
POSITION_SIZE = 200  # $200 per trade
```

## 📊 Understanding Output

### Opportunity List
```
#    Question                    Price    Volume    Market       Category
1    Will BTC hit $100k?         $0.978   $45,000   kalshi       Crypto
2    Lakers win tonight?         $0.974   $12,000   polymarket   Sports
```
- **Price**: Current YES price (97-98c is target)
- **Volume**: 24h trading volume
- **Market**: Which platform (polymarket or kalshi)
- **Category**: Market category

### Trade Entry
```
✅ ENTERED TRADE #1 [KALSHI]
   Market: Will BTC hit $100k?
   Entry Price: $0.978
   Position Size: $100
   Shares: 102.25
```
- **Market source** shown in brackets
- **Shares** = Position Size / Entry Price

### Performance Stats
```
Total Trades:     5
Wins:             4
Losses:           1
Win Rate:         80.0%
Total P&L:        $7.50
Total Fees Paid:  $0.15 (2.0% on profits)
ROI:              1.50%
```
- **P&L** is net after fees
- **Fees** only on winning trades
- **ROI** = P&L / Total Invested

## 🔍 Troubleshooting

### "Error fetching markets: 503"
- API is down/unavailable
- Use demo mode: `--demo-poly` or `--demo-kalshi`

### "No opportunities found"
- Price range might be too narrow
- Try lowering MIN_PRICE or raising MAX_PRICE
- Lower MIN_LIQUIDITY or MIN_VOLUME_24H filters

### No trades entering despite opportunities
- Check MAX_POSITIONS limit (default 10)
- Check MIN_LIQUIDITY and MIN_VOLUME_24H filters
- Position might already exist in that market

## 💡 Tips

1. **Start with demo mode** to understand the bot
2. **Run multiple scans** to see price movement and trade resolution
3. **Compare markets** - check which platform has better opportunities
4. **Test fee assumptions** - try 1%, 2%, 3% to see impact
5. **Adjust filters** based on what you find
6. **Monitor continuously** with `--run` flag for real-time updates

## ⚠️ Important

- This is **paper trading** - no real money involved
- Always verify fee structures before real trading
- Markets can reverse even at 98c
- Transaction costs significantly impact thin margins
- Test thoroughly before considering real trading
