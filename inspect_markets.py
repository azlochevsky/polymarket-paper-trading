#!/usr/bin/env python3
"""Inspect actual Kalshi market data structure."""

from kalshi_client import KalshiClient
import json

client = KalshiClient(demo_mode=False)

print('Fetching first 5 markets...\n')
markets = client.get_markets(limit=5)

print(f'Got {len(markets)} markets\n')

if markets:
    # Show first market in detail
    print('=== FIRST MARKET (full JSON) ===')
    print(json.dumps(markets[0], indent=2))
    print('\n' + '='*60 + '\n')

    # Show summary of all markets
    print('=== ALL 5 MARKETS SUMMARY ===')
    for i, m in enumerate(markets, 1):
        print(f"\n{i}. {m.get('title', 'N/A')[:80]}")
        print(f"   Ticker: {m.get('ticker', 'N/A')}")
        print(f"   Status: {m.get('status', 'N/A')}")

        # Check all possible price fields
        print(f"   Fields available: {list(m.keys())}")

        # Check for price-related fields
        for key in m.keys():
            if any(word in key.lower() for word in ['price', 'bid', 'ask', 'last', 'yes', 'no']):
                print(f"   {key}: {m[key]}")
