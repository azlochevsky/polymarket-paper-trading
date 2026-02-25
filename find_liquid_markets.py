#!/usr/bin/env python3
"""Find Kalshi markets with actual liquidity."""

from kalshi_client import KalshiClient

client = KalshiClient(demo_mode=False)

print('Fetching 200 markets...')
markets = client.get_markets(limit=200)
print(f'Total markets: {len(markets)}\n')

# Analyze markets
high_price_markets = []
liquid_markets = []

for m in markets:
    yes_bid = m.get('yes_bid', 0) / 100
    yes_ask = m.get('yes_ask', 0) / 100
    mid = (yes_bid + yes_ask) / 2

    # Find markets with actual bids (not $0)
    if yes_bid > 0:
        liquid_markets.append((m, mid, yes_bid, yes_ask))

    # Find high-priced markets
    if mid >= 0.90:
        high_price_markets.append((m, mid, yes_bid, yes_ask))

print(f'Markets with actual liquidity: {len(liquid_markets)}')
print(f'Markets priced >= 90c: {len(high_price_markets)}\n')

if liquid_markets:
    print('Top 10 markets with liquidity:')
    for i, (m, mid, bid, ask) in enumerate(liquid_markets[:10], 1):
        print(f'{i}. {m.get("title")[:60]}')
        print(f'   Ticker: {m.get("ticker")}')
        print(f'   Price: ${mid:.3f} (bid: ${bid:.3f}, ask: ${ask:.3f})')
        print()

if high_price_markets:
    print('\nHigh-priced markets (>= 90c):')
    for i, (m, mid, bid, ask) in enumerate(high_price_markets[:10], 1):
        print(f'{i}. {m.get("title")[:60]}')
        print(f'   Price: ${mid:.3f} (bid: ${bid:.3f}, ask: ${ask:.3f})')
        print()

# Summary
print('\n=== SUMMARY ===')
print(f'Total markets fetched: {len(markets)}')
print(f'Markets with bids > 0: {len(liquid_markets)}')
print(f'Markets >= 90c: {len(high_price_markets)}')
print(f'Markets in 97-98c range: ', end='')

in_range = [m for m, mid, bid, ask in liquid_markets if 0.97 <= mid <= 0.98]
print(len(in_range))

if in_range:
    print('\nOPPORTUNITIES FOUND:')
    for m, mid, bid, ask in in_range:
        print(f'  - {m.get("title")}: ${mid:.3f}')
