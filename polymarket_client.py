"""Polymarket API client for fetching market data."""

import requests
import urllib3
from typing import List, Dict, Optional
import config
import demo_data

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PolymarketClient:
    def __init__(self, demo_mode: bool = False):
        self.gamma_api_url = config.GAMMA_API_URL
        self.clob_api_url = config.POLYMARKET_API_URL
        self.demo_mode = demo_mode
        self.demo_markets = demo_data.generate_demo_markets() if demo_mode else []

    def get_markets(self, limit: int = 100, active: bool = True) -> List[Dict]:
        """Fetch active markets from Polymarket."""
        if self.demo_mode:
            return self.demo_markets[:limit]

        try:
            url = f"{self.gamma_api_url}/markets"
            params = {
                "limit": limit,
                "active": "true",
                "closed": "false",  # Only get open markets
                "_c": "1"  # Cache buster
            }

            response = requests.get(url, params=params, timeout=10, verify=False)
            response.raise_for_status()

            data = response.json()
            return data if isinstance(data, list) else []

        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []

    def get_market_details(self, condition_id: str) -> Optional[Dict]:
        """Get detailed information about a specific market."""
        try:
            url = f"{self.gamma_api_url}/markets/{condition_id}"
            response = requests.get(url, timeout=10, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching market details for {condition_id}: {e}")
            return None

    def find_opportunities(self, min_price: float = 0.97, max_price: float = 0.98) -> List[Dict]:
        """Find markets with YES or NO tokens in the target price range."""
        markets = self.get_markets(limit=200)
        opportunities = []

        for market in markets:
            try:
                # Skip if market is already resolved
                if market.get("closed", False) or market.get("resolved", False):
                    continue

                # Parse outcomePrices for YES/NO prices
                prices_str = market.get("outcomePrices", "[]")
                if prices_str and prices_str != "[]":
                    import json
                    try:
                        prices = json.loads(prices_str.replace("'", '"'))
                        if len(prices) >= 2:
                            yes_price = float(prices[0])
                            no_price = float(prices[1])

                            # Check if YES price is in range
                            if min_price <= yes_price <= max_price:
                                outcome = "YES"
                                price = yes_price
                            # Check if NO price is in range
                            elif min_price <= no_price <= max_price:
                                outcome = "NO"
                                price = no_price
                            else:
                                continue

                            # Found an opportunity!
                            opportunity = {
                                "condition_id": market.get("conditionId", market.get("condition_id", "")),
                                "market_slug": market.get("slug", market.get("market_slug", "")),
                                "question": market.get("question", ""),
                                "description": market.get("description", ""),
                                "end_date": market.get("endDateIso", market.get("end_date_iso", "")),
                                "price": price,
                                "token_id": market.get("id", ""),
                                "outcome": outcome,
                                "volume": float(market.get("volumeNum", market.get("volume", 0))),
                                "liquidity": float(market.get("liquidityNum", market.get("liquidity", 0))),
                                "category": market.get("category", ""),
                                "url": f"https://polymarket.com/event/{market.get('slug', market.get('market_slug', ''))}",
                                "source": "polymarket"
                            }
                            opportunities.append(opportunity)
                    except (json.JSONDecodeError, ValueError, IndexError) as e:
                        pass

            except Exception as e:
                print(f"Error processing market: {e}")
                continue

        return opportunities

    def get_current_price(self, condition_id: str, outcome: str = "YES") -> Optional[float]:
        """Get current price for a specific market outcome."""
        if self.demo_mode:
            # Find market in demo data
            for market in self.demo_markets:
                if market['condition_id'] == condition_id:
                    for token in market.get("tokens", []):
                        if token.get("outcome", "").upper() == outcome.upper():
                            # Update price with simulated movement
                            current_price = float(token.get("price", 0))
                            new_price = demo_data.get_demo_price_update(condition_id, current_price)
                            token["price"] = new_price
                            return new_price
            return None

        try:
            market = self.get_market_details(condition_id)
            if not market:
                return None

            tokens = market.get("tokens", [])
            for token in tokens:
                if token.get("outcome", "").upper() == outcome.upper():
                    return float(token.get("price", 0))

            return None
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
