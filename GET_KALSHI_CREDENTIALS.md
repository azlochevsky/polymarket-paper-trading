# How to Get Kalshi API Credentials

## 🔑 Getting Started

Kalshi likely requires authentication for API access. Here's how to get your credentials:

## Method 1: Using Your Kalshi Account (Recommended)

### Step 1: Create a Kalshi Account
1. Go to https://kalshi.com
2. Sign up for an account
3. Complete verification

### Step 2: Get API Access
1. Log in to your Kalshi account
2. Go to **Profile → API Settings** or visit: https://kalshi.com/profile/api
3. Look for:
   - **API Key** generation option
   - **Generate Token** button
   - **Developer Settings**

### Step 3: Add Credentials

**Option A: Using Environment Variables (.env file)**

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```bash
# Method 1: Email/Password
KALSHI_EMAIL=your_email@example.com
KALSHI_PASSWORD=your_password

# OR Method 2: API Key (if available)
KALSHI_API_KEY=your_api_key_here
```

3. The bot will automatically load from `.env` file

**Option B: Using config.py (Less Secure)**

Edit `config.py`:
```python
# Kalshi Authentication
KALSHI_EMAIL = "your_email@example.com"
KALSHI_PASSWORD = "your_password"

# OR
KALSHI_API_KEY = "your_api_key_here"
```

⚠️ **Warning**: Don't commit credentials to git!

## Method 2: Check if Public API Exists

Some endpoints might be public without authentication:

```bash
# Test public access
curl "https://trading-api.kalshi.com/trade-api/v2/markets?limit=5"
```

If this returns JSON (not HTML/error), you don't need credentials!

## Testing Your Setup

### 1. Test Authentication

```bash
python3 bot.py --no-poly --scan
```

Look for:
- ✅ "Kalshi authentication successful"
- ✅ Markets found
- ❌ "Kalshi API requires authentication" → Need credentials

### 2. Test with Demo Mode (No Credentials Needed)

```bash
python3 bot.py --demo-kalshi --no-poly --scan
```

This always works for testing!

## Troubleshooting

### "Kalshi API requires authentication"

**Solution**: Add credentials using one of the methods above

### "Kalshi login failed: 401"

**Possible causes**:
- Wrong email/password
- Email not verified
- Account not activated
- API access not enabled

**Solution**:
- Verify your credentials
- Check email for verification link
- Contact Kalshi support

### "Kalshi login failed: 403"

**Possible causes**:
- API access requires approval
- Account needs to be upgraded
- Geographic restrictions

**Solution**: Contact Kalshi support

### "Error fetching Kalshi markets: 503"

**Possible causes**:
- Wrong API endpoint
- API temporarily down
- Network blocking requests

**Solution**:
- Try demo mode
- Check Kalshi status page
- Try from different network

## Alternative Endpoints to Try

If one doesn't work, try these in `config.py`:

```python
# Production API
KALSHI_API_URL = "https://trading-api.kalshi.com"

# Demo/Sandbox API (might not need auth)
KALSHI_API_URL = "https://demo-api.kalshi.co"

# Elections specific
KALSHI_API_URL = "https://api.elections.kalshi.com"
```

## Security Best Practices

1. **Use .env file** (not config.py) for credentials
2. **Never commit** .env to git (already in .gitignore)
3. **Use API keys** instead of password when possible
4. **Rotate credentials** periodically
5. **Read-only access** if available

## What the Bot Does

With credentials configured:

1. **On startup**: Authenticates with Kalshi API
2. **Gets token**: Stores authentication token
3. **Makes requests**: Uses token for all API calls
4. **Auto-renews**: Re-authenticates if token expires

## Getting Help

### Kalshi Resources
- **Website**: https://kalshi.com
- **API Docs**: https://trading-api.readme.io/
- **Support**: Check Kalshi website for support contact

### Check API Documentation
```bash
# Visit Kalshi's API documentation
open https://trading-api.readme.io/
```

Look for:
- Authentication section
- API key generation
- Rate limits
- Example requests

## Quick Reference

```bash
# 1. Create .env file
cp .env.example .env

# 2. Edit .env with your credentials
nano .env

# 3. Test connection
python3 bot.py --no-poly --scan

# 4. If working, run continuously
python3 bot.py --no-poly --run

# 5. Or use demo mode anytime
python3 bot.py --demo-kalshi --no-poly --run
```

## Expected Behavior

### Without Credentials
```
Error fetching Kalshi markets: 401 Unauthorized
⚠️ Kalshi API requires authentication. Please add credentials...
```

### With Valid Credentials
```
✅ Kalshi authentication successful
🔍 Scanning markets...
📊 Found 12 opportunities...
```

### With Demo Mode
```
MODE: DEMO (Simulated Data)
📊 Found 5 opportunities...
```

## Still Stuck?

1. **Check Kalshi Status**: Make sure API is operational
2. **Try Demo Mode**: Always works without credentials
3. **Contact Kalshi**: They can help with API access
4. **Use Test Script**: `python3 test_kalshi_api.py`
