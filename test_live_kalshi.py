#!/usr/bin/env python3
"""Quick test of live Kalshi API."""

from kalshi_client import KalshiClient

print("Testing Kalshi API...")
client = KalshiClient(demo_mode=False)

print("\n1. Fetching markets...")
markets = client.get_markets(limit=10)

print(f"Found {len(markets)} markets\n")

if markets:
    print("Sample markets:")
    for i, market in enumerate(markets[:5], 1):
        ticker = market.get('ticker', 'N/A')
        title = market.get('title', 'N/A')
        status = market.get('status', 'N/A')

        # Get prices
        yes_bid = market.get('yes_bid', 0) / 100
        yes_ask = market.get('yes_ask', 0) / 100
        mid_price = (yes_bid + yes_ask) / 2

        print(f"{i}. {ticker}")
        print(f"   Title: {title}")
        print(f"   Status: {status}")
        print(f"   Price: ${mid_price:.3f} (bid: ${yes_bid:.3f}, ask: ${yes_ask:.3f})")
        print()

    # Check for opportunities
    print("\n2. Checking for 97-98c opportunities...")
    opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)
    print(f"Found {len(opportunities)} opportunities in 97-98c range")

    if opportunities:
        for opp in opportunities[:3]:
            print(f"  - {opp['question']}: ${opp['price']:.3f}")

    # Try wider range
    print("\n3. Checking for 95-99c opportunities...")
    opportunities = client.find_opportunities(min_price=0.95, max_price=0.99)
    print(f"Found {len(opportunities)} opportunities in 95-99c range")

    if opportunities:
        for opp in opportunities[:5]:
            print(f"  - {opp['question']}: ${opp['price']:.3f}")
else:
    print("❌ No markets returned - API might need different parameters")
