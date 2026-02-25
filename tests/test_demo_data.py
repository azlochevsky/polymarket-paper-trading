"""Unit tests for demo data modules."""

import pytest
from demo_data import generate_demo_markets as generate_poly_demo, get_demo_price_update as poly_price_update
from kalshi_demo_data import generate_demo_markets as generate_kalshi_demo, get_demo_price_update as kalshi_price_update


class TestDemoData:
    """Test cases for Polymarket demo data."""

    def test_generate_demo_markets_returns_list(self):
        """Test that generate_demo_markets returns a list."""
        markets = generate_poly_demo()
        assert isinstance(markets, list)
        assert len(markets) > 0

    def test_demo_markets_have_required_fields(self):
        """Test that demo markets have required fields."""
        markets = generate_poly_demo()
        required_fields = [
            'condition_id', 'market_slug', 'question',
            'description', 'tokens'
        ]

        for market in markets:
            for field in required_fields:
                assert field in market, f"Missing field: {field}"
            # Check for either end_date or end_date_iso
            assert 'end_date' in market or 'end_date_iso' in market

    def test_demo_markets_have_tokens(self):
        """Test that demo markets have YES/NO tokens."""
        markets = generate_poly_demo()

        for market in markets:
            tokens = market['tokens']
            assert len(tokens) == 2

            outcomes = [t['outcome'] for t in tokens]
            assert 'YES' in outcomes
            assert 'NO' in outcomes

    def test_demo_market_prices_valid(self):
        """Test that demo market prices are valid."""
        markets = generate_poly_demo()

        for market in markets:
            for token in market['tokens']:
                price = float(token['price'])
                assert 0 < price < 1

    def test_demo_market_prices_sum_to_one(self):
        """Test that YES and NO prices sum to approximately 1."""
        markets = generate_poly_demo()

        for market in markets:
            yes_price = float(market['tokens'][0]['price'])
            no_price = float(market['tokens'][1]['price'])
            total = yes_price + no_price

            # Allowing small rounding errors
            assert abs(total - 1.0) < 0.01

    def test_poly_price_update_returns_float(self):
        """Test that price update returns a float."""
        condition_id = "demo_123"
        current_price = 0.5

        new_price = poly_price_update(condition_id, current_price)

        assert isinstance(new_price, float)

    def test_poly_price_update_within_bounds(self):
        """Test that updated prices stay within valid bounds."""
        condition_id = "demo_123"

        # Test multiple prices
        test_prices = [0.1, 0.5, 0.9, 0.97]

        for price in test_prices:
            new_price = poly_price_update(condition_id, price)
            assert 0 < new_price < 1

    def test_poly_price_update_simulates_movement(self):
        """Test that price can move up or down."""
        condition_id = "demo_movement"
        current_price = 0.5

        # Get multiple updates
        prices = [poly_price_update(condition_id, current_price) for _ in range(100)]

        # Should have some variation (not all the same)
        unique_prices = set(prices)
        assert len(unique_prices) > 1


class TestKalshiDemoData:
    """Test cases for Kalshi demo data."""

    def test_generate_kalshi_demo_markets_returns_list(self):
        """Test that Kalshi demo generation returns a list."""
        markets = generate_kalshi_demo()
        assert isinstance(markets, list)
        assert len(markets) > 0

    def test_kalshi_demo_markets_have_required_fields(self):
        """Test that Kalshi demo markets have required fields."""
        markets = generate_kalshi_demo()
        required_fields = [
            'ticker', 'title', 'subtitle', 'status',
            'yes_bid', 'yes_ask', 'category'
        ]

        for market in markets:
            for field in required_fields:
                assert field in market, f"Missing field: {field}"

    def test_kalshi_demo_prices_in_cents(self):
        """Test that Kalshi demo prices are in cents (0-10000)."""
        markets = generate_kalshi_demo()

        for market in markets:
            assert 0 <= market['yes_bid'] <= 10000
            assert 0 <= market['yes_ask'] <= 10000
            assert 0 <= market['no_bid'] <= 10000
            assert 0 <= market['no_ask'] <= 10000

    def test_kalshi_demo_bid_ask_spread(self):
        """Test that ask is always >= bid."""
        markets = generate_kalshi_demo()

        for market in markets:
            assert market['yes_ask'] >= market['yes_bid']
            assert market['no_ask'] >= market['no_bid']

    def test_kalshi_demo_status_active(self):
        """Test that demo markets have active status."""
        markets = generate_kalshi_demo()

        for market in markets:
            # Status can be 'active' or 'open'
            assert market['status'] in ['active', 'open']

    def test_kalshi_demo_has_volume(self):
        """Test that demo markets have volume data."""
        markets = generate_kalshi_demo()

        for market in markets:
            assert 'volume' in market
            assert market['volume'] >= 0

    def test_kalshi_demo_has_categories(self):
        """Test that demo markets have categories."""
        markets = generate_kalshi_demo()
        categories = set()

        for market in markets:
            categories.add(market['category'])

        # Should have multiple categories
        assert len(categories) > 1

    def test_kalshi_demo_ticker_format(self):
        """Test that tickers follow expected format."""
        markets = generate_kalshi_demo()

        for market in markets:
            ticker = market['ticker']
            assert isinstance(ticker, str)
            assert len(ticker) > 0
            # Kalshi tickers typically have format like "EVENT-123"
            assert '-' in ticker or ticker.isupper()
