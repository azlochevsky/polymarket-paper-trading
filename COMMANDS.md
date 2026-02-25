# Command Cheat Sheet

## 🎯 All Command Combinations

### Basic Operations
```bash
# Single scan (both markets, real data)
python3 bot.py --scan

# Continuous monitoring (both markets, real data)
python3 bot.py --run

# View statistics
python3 bot.py --stats

# View open positions
python3 bot.py --positions
```

### Demo Modes
```bash
# Both markets in demo mode
python3 bot.py --demo-poly --demo-kalshi --scan

# Only Polymarket demo (Kalshi real)
python3 bot.py --demo-poly --scan

# Only Kalshi demo (Polymarket real)
python3 bot.py --demo-kalshi --scan
```

### Market Selection
```bash
# Only scan Polymarket (Kalshi disabled)
python3 bot.py --no-kalshi --scan

# Only scan Kalshi (Polymarket disabled)
python3 bot.py --no-poly --scan
```

### Combined: Demo Mode + Market Selection
```bash
# Only Polymarket in demo (Kalshi completely disabled)
python3 bot.py --demo-poly --no-kalshi --scan

# Only Kalshi in demo (Polymarket completely disabled)
python3 bot.py --demo-kalshi --no-poly --scan
```

### Continuous Monitoring Examples
```bash
# Both markets demo, continuous
python3 bot.py --demo-poly --demo-kalshi --run

# Only Kalshi demo, continuous
python3 bot.py --demo-kalshi --no-poly --run

# Only Polymarket real data, continuous
python3 bot.py --no-kalshi --run
```

## 📋 Flag Reference

| Flag | Description |
|------|-------------|
| `--scan` | Run a single scan |
| `--run` | Run continuous monitoring (60s interval) |
| `--stats` | Show performance statistics |
| `--positions` | Show open positions |
| `--demo-poly` | Use demo mode for Polymarket |
| `--demo-kalshi` | Use demo mode for Kalshi |
| `--no-poly` | Disable Polymarket scanning |
| `--no-kalshi` | Disable Kalshi scanning |

## 🔍 Quick Decision Guide

**Want to test the bot without real APIs?**
```bash
python3 bot.py --demo-poly --demo-kalshi --scan
```

**Kalshi API is working, but Polymarket isn't?**
```bash
python3 bot.py --demo-poly --scan
```

**Only interested in Kalshi markets?**
```bash
python3 bot.py --no-poly --scan
```

**Want to compare Polymarket vs Kalshi performance?**
```bash
# First test Polymarket only
python3 bot.py --no-kalshi --demo-poly --run

# Then test Kalshi only
python3 bot.py --no-poly --demo-kalshi --run

# Compare stats
python3 bot.py --stats
```

**Ready to go live with both markets?**
```bash
python3 bot.py --run
```

## ⚙️ Common Workflows

### 1. Initial Testing
```bash
# Test with simulated data
python3 bot.py --demo-poly --demo-kalshi --scan
python3 bot.py --demo-poly --demo-kalshi --scan
python3 bot.py --demo-poly --demo-kalshi --scan

# Check results
python3 bot.py --stats
```

### 2. Test One Market at a Time
```bash
# Test only Polymarket
python3 bot.py --demo-poly --no-kalshi --run

# Stop with Ctrl+C, then test only Kalshi
python3 bot.py --demo-kalshi --no-poly --run
```

### 3. Gradual Rollout
```bash
# Start with Kalshi real data only
python3 bot.py --no-poly --scan

# If working well, add Polymarket
python3 bot.py --scan

# Go continuous
python3 bot.py --run
```

## 💡 Pro Tips

1. **Always start with demo mode** when testing changes
2. **Use `--no-*` flags** to quickly disable a problematic market
3. **Combine flags** for precise control (e.g., `--demo-poly --no-kalshi`)
4. **Check stats regularly** with `--stats` to track performance
5. **Use Ctrl+C** to stop continuous monitoring gracefully

## 🚨 Remember

- Flags override config.py settings
- `--no-poly` and `--no-kalshi` disable markets regardless of config
- Demo modes are independent per market
- Default (no flags) = both markets enabled with real data
