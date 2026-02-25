"""Demo market data for testing the bot when API is unavailable."""

import random
from datetime import datetime, timedelta


def generate_demo_markets():
    """Generate simulated market data for testing."""

    categories = ["Sports", "Politics", "Crypto", "Weather", "Entertainment", "Business"]

    questions = [
        ("Will Bitcoin be above $100k by March 1, 2026?", "Crypto", 0.975),
        ("Will it rain in NYC tomorrow?", "Weather", 0.978),
        ("Will the S&P 500 close above 6000 this week?", "Business", 0.972),
        ("Will Lakers win tonight's game?", "Sports", 0.976),
        ("Will Fed cut rates in March?", "Politics", 0.971),
        ("Will ETH reach $4000 by end of month?", "Crypto", 0.979),
        ("Will new iPhone be announced this month?", "Business", 0.973),
        ("Will unemployment stay below 4%?", "Politics", 0.977),
        ("Will Dow Jones hit new ATH this week?", "Business", 0.974),
        ("Will Tesla stock close above $250 today?", "Business", 0.978),
        # Some outside the range
        ("Will it snow in Miami tomorrow?", "Weather", 0.02),
        ("Will BTC reach $200k by EOY?", "Crypto", 0.45),
        ("Will market crash tomorrow?", "Business", 0.15),
        ("Coin flip - heads?", "Entertainment", 0.50),
    ]

    markets = []

    for i, (question, category, base_price) in enumerate(questions):
        # Add some random variance
        price = base_price + random.uniform(-0.01, 0.01)
        price = max(0.01, min(0.99, price))  # Clamp between 1c and 99c

        volume = random.uniform(500, 50000)
        liquidity = random.uniform(1000, 100000)

        market = {
            "condition_id": f"demo_{i}",
            "market_slug": question.lower().replace(" ", "-").replace("?", ""),
            "question": question,
            "description": f"Simulated market: {question}",
            "end_date_iso": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
            "closed": False,
            "resolved": False,
            "category": category,
            "volume": volume,
            "liquidity": liquidity,
            "tokens": [
                {
                    "outcome": "YES",
                    "price": price,
                    "token_id": f"token_yes_{i}"
                },
                {
                    "outcome": "NO",
                    "price": 1.0 - price,
                    "token_id": f"token_no_{i}"
                }
            ]
        }
        markets.append(market)

    return markets


def get_demo_price_update(condition_id: str, current_price: float) -> float:
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
