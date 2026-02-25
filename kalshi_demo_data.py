"""Demo market data for Kalshi testing."""

import random
from datetime import datetime, timedelta


def generate_demo_markets():
    """Generate simulated Kalshi market data for testing."""

    questions = [
        ("Fed cuts rates in March 2026?", "Politics", 97.5),
        ("S&P 500 above 6000 by end of week?", "Finance", 97.8),
        ("Unemployment below 4% in February?", "Economics", 97.2),
        ("Bitcoin above $100k by March?", "Crypto", 97.6),
        ("Tesla stock above $300 by April?", "Stocks", 97.9),
        ("Gold above $2800 by end of month?", "Commodities", 97.3),
        ("Will it snow in Denver tomorrow?", "Weather", 97.7),
        ("Biden approval above 45% in March?", "Politics", 97.4),
        ("Inflation below 3% in February?", "Economics", 97.1),
        ("Oil prices above $80 by March?", "Commodities", 97.8),
        # Some outside the range
        ("Market crash tomorrow?", "Finance", 5.0),
        ("Bitcoin to $200k by EOY?", "Crypto", 35.0),
        ("Recession in 2026?", "Economics", 25.0),
    ]

    markets = []

    for i, (title, category, base_price) in enumerate(questions):
        # Add some random variance (in cents)
        price_cents = base_price + random.uniform(-1.0, 1.0)
        price_cents = max(1, min(99, price_cents))  # Clamp between 1 and 99 cents

        volume = random.uniform(10000, 500000)
        open_interest = random.uniform(5000, 100000)

        market = {
            "ticker": f"KALSHI-{i:03d}",
            "title": title,
            "subtitle": f"Simulated Kalshi market: {title}",
            "category": category,
            "status": "open",
            "close_time": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
            "yes_bid": price_cents - 1,  # Bid is slightly lower
            "yes_ask": price_cents + 1,  # Ask is slightly higher
            "no_bid": (100 - price_cents) - 1,
            "no_ask": (100 - price_cents) + 1,
            "volume": volume,
            "open_interest": open_interest,
        }
        markets.append(market)

    return markets


def get_demo_price_update(ticker: str, current_price: float) -> float:
    """Simulate price movement for demo mode."""
    # Random walk with slight upward bias (markets tend to resolve)
    change = random.uniform(-0.02, 0.03)
    new_price = current_price + change

    # Clamp between 0.01 and 1.00
    new_price = max(0.01, min(1.00, new_price))

    # If close to 1.00, sometimes jump to 1.00 (resolution)
    if new_price > 0.98 and random.random() < 0.1:
        new_price = 1.00

    # If dropping, sometimes drop to near 0 (loss)
    if new_price < 0.85 and random.random() < 0.05:
        new_price = random.uniform(0.01, 0.20)

    return new_price
