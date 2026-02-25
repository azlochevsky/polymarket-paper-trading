"""Kalshi API client for fetching market data."""

import requests
import urllib3
from typing import List, Dict, Optional
import os
import time
import base64
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import config
import kalshi_demo_data

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class KalshiClient:
    def __init__(self, demo_mode: bool = False):
        self.api_url = config.KALSHI_API_URL
        self.demo_mode = demo_mode
        self.demo_markets = kalshi_demo_data.generate_demo_markets() if demo_mode else []
        self.auth_token = None
        self.session = requests.Session()

        # Try to authenticate if credentials are provided
        if not demo_mode:
            self._authenticate()

    def _authenticate(self):
        """Authenticate with Kalshi API using credentials."""
        # Check for credentials from environment variables first
        api_key_id = os.getenv('KALSHI_API_KEY_ID') or getattr(config, 'KALSHI_API_KEY_ID', None)
        private_key_str = os.getenv('KALSHI_PRIVATE_KEY') or getattr(config, 'KALSHI_PRIVATE_KEY', None)

        # Method 1: RSA Key-based authentication (Kalshi's method)
        if api_key_id and private_key_str:
            try:
                # Load the RSA private key
                self.private_key = RSA.import_key(private_key_str)
                self.api_key_id = api_key_id
                print(f"✅ Kalshi API key loaded: {api_key_id[:8]}...")
                return
            except Exception as e:
                print(f"⚠️ Error loading Kalshi private key: {e}")

        # Method 2: Legacy email/password (if RSA not available)
        email = os.getenv('KALSHI_EMAIL') or getattr(config, 'KALSHI_EMAIL', None)
        password = os.getenv('KALSHI_PASSWORD') or getattr(config, 'KALSHI_PASSWORD', None)

        if email and password:
            try:
                login_url = f"{self.api_url}/trade-api/v2/login"
                response = self.session.post(
                    login_url,
                    json={"email": email, "password": password},
                    timeout=10,
                    verify=False
                )

                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get('token')
                    if self.auth_token:
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                        print("✅ Kalshi authentication successful")
                    return
                else:
                    print(f"⚠️ Kalshi login failed: {response.status_code}")

            except Exception as e:
                print(f"⚠️ Kalshi authentication error: {e}")

    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Sign request with RSA private key for Kalshi API."""
        if not hasattr(self, 'private_key') or not hasattr(self, 'api_key_id'):
            return {}

        try:
            # Create timestamp (milliseconds)
            timestamp = str(int(time.time() * 1000))

            # Create signature message: timestamp + method + path + body
            message = timestamp + method + path + body

            # Sign the message
            h = SHA256.new(message.encode('utf-8'))
            signature = pkcs1_15.new(self.private_key).sign(h)

            # Base64 encode the signature
            signature_b64 = base64.b64encode(signature).decode('utf-8')

            return {
                'KALSHI-ACCESS-KEY': self.api_key_id,
                'KALSHI-ACCESS-SIGNATURE': signature_b64,
                'KALSHI-ACCESS-TIMESTAMP': timestamp
            }

        except Exception as e:
            print(f"⚠️ Error signing request: {e}")
            return {}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make authenticated request to Kalshi API."""
        url = f"{self.api_url}{endpoint}"

        # Sign the request with RSA key if available
        body = kwargs.get('json', '')
        if body:
            import json
            body = json.dumps(body)

        auth_headers = self._sign_request(method.upper(), endpoint, body)

        # Merge authentication headers with any existing headers
        headers = kwargs.get('headers', {})
        headers.update(auth_headers)
        kwargs['headers'] = headers

        # Set default timeout
        kwargs.setdefault('timeout', 10)
        kwargs.setdefault('verify', False)

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            # If 401 Unauthorized, credentials might be needed
            if e.response.status_code == 401:
                print("⚠️ Kalshi API requires authentication. Please add credentials to .env")
                print("   Visit: https://kalshi.com/profile/api")
            raise
        except Exception:
            raise

    def get_markets(self, limit: int = 100, status: str = "open") -> List[Dict]:
        """Fetch active markets from Kalshi."""
        if self.demo_mode:
            return self.demo_markets[:limit]

        try:
            response = self._make_request(
                'GET',
                '/trade-api/v2/markets',
                params={"limit": limit, "status": status}
            )

            if response:
                data = response.json()
                return data.get("markets", [])

            return []

        except Exception as e:
            print(f"Error fetching Kalshi markets: {e}")
            return []

    def get_market_details(self, ticker: str) -> Optional[Dict]:
        """Get detailed information about a specific market."""
        if self.demo_mode:
            for market in self.demo_markets:
                if market['ticker'] == ticker:
                    return market
            return None

        try:
            response = self._make_request('GET', f'/trade-api/v2/markets/{ticker}')
            if response:
                return response.json().get("market")
            return None

        except Exception as e:
            print(f"Error fetching Kalshi market details for {ticker}: {e}")
            return None

    def find_opportunities(self, min_price: float = 0.97, max_price: float = 0.98) -> List[Dict]:
        """Find markets with YES tokens in the target price range."""
        markets = self.get_markets(limit=200)
        opportunities = []

        # Convert to 0-1 range from Kalshi's cents (0-100)
        min_price_cents = min_price * 100
        max_price_cents = max_price * 100

        for market in markets:
            try:
                # Skip if market is closed or inactive
                if market.get("status") != "open" and not self.demo_mode:
                    continue

                # Kalshi uses yes_bid, yes_ask, no_bid, no_ask (in cents)
                yes_bid = market.get("yes_bid", 0) / 100.0  # Convert cents to dollars
                yes_ask = market.get("yes_ask", 0) / 100.0

                # Use mid price
                yes_price = (yes_bid + yes_ask) / 2 if yes_ask > 0 else yes_bid

                if min_price <= yes_price <= max_price:
                    opportunity = {
                        "market_id": market.get("ticker"),
                        "market_slug": market.get("ticker"),
                        "question": market.get("title"),
                        "description": market.get("subtitle", ""),
                        "end_date": market.get("close_time"),
                        "price": yes_price,
                        "outcome": "YES",
                        "volume": float(market.get("volume", 0)),
                        "liquidity": float(market.get("open_interest", 0)),
                        "category": market.get("category", ""),
                        "url": f"https://kalshi.com/markets/{market.get('ticker', '')}",
                        "source": "kalshi"
                    }
                    opportunities.append(opportunity)

            except Exception as e:
                print(f"Error processing Kalshi market: {e}")
                continue

        return opportunities

    def get_current_price(self, ticker: str, outcome: str = "YES") -> Optional[float]:
        """Get current price for a specific market outcome."""
        # Handle None outcome (backward compatibility with NULL database values)
        if outcome is None:
            outcome = "YES"

        if self.demo_mode:
            # Find market in demo data
            for market in self.demo_markets:
                if market['ticker'] == ticker:
                    yes_bid = market.get("yes_bid", 0) / 100.0
                    yes_ask = market.get("yes_ask", 0) / 100.0
                    current_price = (yes_bid + yes_ask) / 2 if yes_ask > 0 else yes_bid

                    # Update price with simulated movement
                    new_price = kalshi_demo_data.get_demo_price_update(ticker, current_price)

                    # Update the market data
                    new_price_cents = new_price * 100
                    market["yes_bid"] = new_price_cents - 1
                    market["yes_ask"] = new_price_cents + 1

                    return new_price
            return None

        try:
            market = self.get_market_details(ticker)
            if not market:
                return None

            yes_bid = market.get("yes_bid", 0) / 100.0
            yes_ask = market.get("yes_ask", 0) / 100.0

            return (yes_bid + yes_ask) / 2 if yes_ask > 0 else yes_bid

        except Exception as e:
            print(f"Error getting current Kalshi price: {e}")
            return None
