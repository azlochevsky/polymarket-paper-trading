#!/usr/bin/env python3
"""Test script to verify Kalshi API connectivity."""

import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_kalshi_api():
    """Test different Kalshi API endpoints."""

    endpoints = [
        "https://api.elections.kalshi.com/trade-api/v2/exchange/status",
        "https://trading-api.kalshi.com/trade-api/v2/exchange/status",
        "https://demo-api.kalshi.co/trade-api/v2/exchange/status",
        "https://api.elections.kalshi.com/trade-api/v2/markets?limit=5",
        "https://trading-api.kalshi.com/trade-api/v2/markets?limit=5",
    ]

    print("Testing Kalshi API endpoints...\n")

    for url in endpoints:
        print(f"Testing: {url}")
        try:
            response = requests.get(url, timeout=10, verify=False)
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")

                # If this is the markets endpoint, show a sample
                if 'markets' in data:
                    markets = data['markets']
                    print(f"  Found {len(markets)} markets")
                    if markets:
                        print(f"  Sample market: {markets[0].get('ticker', 'N/A')}")
                        print(f"  Title: {markets[0].get('title', 'N/A')}")
                print()
                return url  # Return the working endpoint
            else:
                print(f"  ❌ Failed: {response.status_code}")
                print(f"  Response: {response.text[:200]}")

        except requests.exceptions.SSLError as e:
            print(f"  ❌ SSL Error: {str(e)[:100]}")
        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ Connection Error: {str(e)[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}: {str(e)[:100]}")

        print()

    print("❌ No working endpoints found")
    print("\nTroubleshooting:")
    print("1. Check if you have internet connectivity")
    print("2. Check if Kalshi API requires authentication")
    print("3. Try from a different network")
    print("4. Check Kalshi API documentation: https://trading-api.readme.io/")
    return None


if __name__ == "__main__":
    working_endpoint = test_kalshi_api()

    if working_endpoint:
        print(f"\n✅ Working endpoint found: {working_endpoint}")
        print(f"\nUpdate config.py with:")

        # Extract base URL
        if "demo-api.kalshi.co" in working_endpoint:
            base = "https://demo-api.kalshi.co"
        elif "api.elections.kalshi.com" in working_endpoint:
            base = "https://api.elections.kalshi.com"
        else:
            base = "https://trading-api.kalshi.com"

        print(f'KALSHI_API_URL = "{base}"')
