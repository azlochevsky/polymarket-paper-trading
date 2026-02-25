"""Configuration for Polymarket paper trading bot."""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Trading parameters
MIN_PRICE = 0.97  # Minimum price to consider (97 cents) - for Polymarket
MAX_PRICE = 0.98  # Maximum price to consider (98 cents) - for Polymarket

# Fee configuration
POLYMARKET_FEE = 0.02  # Fee on profits (0.02 = 2%, 0.01 = 1%, etc.)
                        # This fee is only applied to winning trades on the profit portion
                        # Set to 0 for no fees (unrealistic but useful for testing)

# Position sizing
POSITION_SIZE = 100  # Default position size in USD
MAX_POSITIONS = 10  # Maximum concurrent positions

# Market filters
MIN_LIQUIDITY = 1000  # Minimum liquidity in USD
MIN_VOLUME_24H = 500  # Minimum 24h volume

# API configuration
POLYMARKET_API_URL = "https://clob.polymarket.com"
GAMMA_API_URL = "https://gamma-api.polymarket.com"
# KALSHI_API_URL = "https://demo-api.kalshi.co"  # Demo API
KALSHI_API_URL = "https://api.elections.kalshi.com"  # Production API (new endpoint!)

# Kalshi Authentication (Use .env file for security!)
# Get credentials from: https://kalshi.com/profile/api
KALSHI_API_KEY_ID = None  # Your API Key ID
KALSHI_PRIVATE_KEY = None  # Your RSA Private Key (multi-line string)

# Legacy authentication (if RSA not available)
KALSHI_EMAIL = None  # Your Kalshi account email
KALSHI_PASSWORD = None  # Your Kalshi account password

# Market selection
ENABLE_POLYMARKET = True  # Enable Polymarket scanning
ENABLE_KALSHI = True      # Enable Kalshi scanning

# Database
DB_PATH = "paper_trades.db"

# Refresh interval
REFRESH_INTERVAL = 60  # Check markets every 60 seconds
