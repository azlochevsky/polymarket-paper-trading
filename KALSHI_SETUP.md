# Kalshi API Setup Guide

## 🔍 Research Findings

**Kalshi API likely requires authentication!** The bot now includes:
- ✅ Email/password authentication
- ✅ API key support (if Kalshi provides it)
- ✅ Automatic login on startup
- ✅ Token management
- ✅ Session handling

## Current Status

⚠️ The Kalshi API cannot be tested in the current network environment due to firewall/proxy restrictions. However, **the authentication-enabled code is ready** to work when you run it in your own environment.

## 📖 See Detailed Credentials Guide

For step-by-step instructions on getting Kalshi API credentials, see:
**→ `GET_KALSHI_CREDENTIALS.md`**

## Quick Test

Run this to test Kalshi API connectivity:

```bash
python3 test_kalshi_api.py
```

This will:
- Test multiple Kalshi API endpoints
- Show which endpoint works
- Display sample market data
- Provide the correct API URL for config.py

## Manual Testing

### 1. Test API Connectivity

```bash
# Test if you can reach Kalshi API
curl "https://trading-api.kalshi.com/trade-api/v2/exchange/status"

# Or try the demo API
curl "https://demo-api.kalshi.co/trade-api/v2/exchange/status"
```

### 2. Test Market Data

```bash
# Get markets
curl "https://trading-api.kalshi.com/trade-api/v2/markets?limit=5&status=open"
```

### 3. Check Response

If you get JSON back (not HTML), the API is working! Look for:
- `markets` array
- Market objects with `ticker`, `title`, `yes_bid`, `yes_ask`

## Configuration

### Option 1: Production API (Requires Account)

```python
# config.py
KALSHI_API_URL = "https://trading-api.kalshi.com"
```

You may need API credentials:
```python
# Add to config.py if needed
KALSHI_API_KEY = "your_api_key"
KALSHI_API_SECRET = "your_api_secret"
```

### Option 2: Demo API (No Account Needed)

```python
# config.py
KALSHI_API_URL = "https://demo-api.kalshi.co"
```

### Option 3: Elections API

```python
# config.py
KALSHI_API_URL = "https://api.elections.kalshi.com"
```

## API Documentation

- **Main Docs**: https://trading-api.readme.io/
- **API Reference**: https://trading-api.readme.io/reference/
- **Getting Started**: https://kalshi.com/api

## Common Issues

### 503 Service Unavailable

**Possible causes:**
1. API endpoint is wrong
2. API requires authentication
3. Network/firewall blocking requests
4. Kalshi API is down (check status page)

**Solutions:**
- Try different endpoints (production/demo/elections)
- Add authentication headers if you have API credentials
- Test from different network
- Use demo mode: `python3 bot.py --demo-kalshi --scan`

### SSL Certificate Errors

The bot already handles SSL errors with `verify=False`. If you still get errors:
```python
# Already in kalshi_client.py
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### Authentication Required

If Kalshi requires authentication, update `kalshi_client.py`:

```python
def get_markets(self, limit: int = 100, status: str = "open"):
    if self.demo_mode:
        return self.demo_markets[:limit]

    try:
        url = f"{self.api_url}/trade-api/v2/markets"
        params = {"limit": limit, "status": status}

        # Add authentication headers
        headers = {}
        if hasattr(config, 'KALSHI_API_KEY'):
            headers['Authorization'] = f'Bearer {config.KALSHI_API_KEY}'

        response = requests.get(url, params=params, headers=headers,
                              timeout=10, verify=False)
        response.raise_for_status()
        # ...
```

## Testing the Bot

### With Demo Mode (Works Anywhere)

```bash
# Test Kalshi demo mode only
python3 bot.py --demo-kalshi --no-poly --scan

# Continuous monitoring in demo
python3 bot.py --demo-kalshi --no-poly --run
```

### With Real API (Once Working)

```bash
# Test real Kalshi API
python3 bot.py --no-poly --scan

# If working, run continuous
python3 bot.py --no-poly --run

# Or both markets
python3 bot.py --run
```

## Verifying It Works

When Kalshi API is working, you should see:

```
============================================================
  MULTI-MARKET PAPER TRADING BOT
  Target: 97-98c contracts
  Markets: Kalshi
============================================================

🔍 Scanning markets... [2026-02-25 14:20:00]

📊 Found 8 opportunities:

#    Question                              Price    Volume       Market    Category
1    Will unemployment be below 4%?        $0.978   $125,000     kalshi    Economics
2    Fed cuts rates in March?              $0.975   $250,000     kalshi    Politics
...
```

**NOT** error messages like:
- ❌ "Error fetching Kalshi markets: 503"
- ❌ "Error fetching Kalshi markets: SSL"
- ❌ "URL Content Blocked"

## Next Steps

1. **Run test script**: `python3 test_kalshi_api.py`
2. **Update config.py** with working endpoint
3. **Test bot**: `python3 bot.py --no-poly --scan`
4. **If still blocked**: Use demo mode or try from different network
5. **Report issues**: Check if Kalshi API docs have changed

## Alternative: Use Demo Mode

If you can't access real Kalshi API:
- Demo mode provides realistic testing
- Simulates market movements and resolutions
- Perfect for strategy development
- Use: `--demo-kalshi` flag

```bash
python3 bot.py --demo-kalshi --no-poly --run
```

## Getting Help

If stuck:
1. Check Kalshi status page
2. Review Kalshi API documentation
3. Contact Kalshi support for API access
4. Use demo mode for testing in the meantime
