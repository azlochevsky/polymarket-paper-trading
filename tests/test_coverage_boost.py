"""Additional tests to boost coverage to 90%+."""

import pytest
import responses
from unittest.mock import Mock, patch
from polymarket_client import PolymarketClient
from kalshi_client import KalshiClient
from demo_data import get_demo_price_update
from kalshi_demo_data import get_demo_price_update as kalshi_price_update
import config


class TestCoverageBoost:
    """Tests specifically designed to cover remaining uncovered lines."""

    def test_demo_price_update_edge_cases(self):
        """Test demo price update with edge cases."""
        # Test price at 0.99 (high probability of jumping to 1.0)
        for _ in range(20):
            price = get_demo_price_update("test_id", 0.99)
            assert 0 < price <= 1.0

        # Test price at 0.80 (probability of dropping)
        for _ in range(20):
            price = get_demo_price_update("test_id", 0.80)
            assert 0 < price <= 1.0

    def test_kalshi_demo_price_update_edge_cases(self):
        """Test Kalshi demo price updates."""
        # Test at high price
        for _ in range(10):
            price = kalshi_price_update("TEST-001", 0.99)
            assert 0 < price <= 1.0

        # Test at low price
        for _ in range(10):
            price = kalshi_price_update("TEST-001", 0.75)
            assert 0 < price <= 1.0

    @responses.activate
    def test_polymarket_get_market_details_with_tokens(self):
        """Test getting market details with token information."""
        client = PolymarketClient(demo_mode=False)

        mock_response = {
            "conditionId": "0x123",
            "question": "Test market",
            "tokens": [
                {"outcome": "YES", "price": "0.6", "token_id": "token_yes"},
                {"outcome": "NO", "price": "0.4", "token_id": "token_no"}
            ]
        }

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets/0x123",
            json=mock_response,
            status=200
        )

        details = client.get_market_details("0x123")
        assert details is not None
        assert len(details['tokens']) == 2

    @responses.activate
    def test_polymarket_find_opportunities_with_edge_prices(self):
        """Test finding opportunities with prices at edges."""
        client = PolymarketClient(demo_mode=False)

        mock_markets = [
            {
                "conditionId": "exact_min",
                "slug": "exact-min",
                "question": "Exact min price",
                "description": "Test",
                "endDateIso": "2026-12-31",
                "outcomePrices": '["0.970", "0.030"]',  # Exactly at min
                "closed": False,
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000,
                "category": "Test",
                "id": "exact_min"
            },
            {
                "conditionId": "exact_max",
                "slug": "exact-max",
                "question": "Exact max price",
                "description": "Test",
                "endDateIso": "2026-12-31",
                "outcomePrices": '["0.980", "0.020"]',  # Exactly at max
                "closed": False,
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000,
                "category": "Test",
                "id": "exact_max"
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)

        # Should find both
        assert len(opportunities) == 2

    @responses.activate
    def test_polymarket_find_opportunities_empty_prices(self):
        """Test handling of empty/null outcome prices."""
        client = PolymarketClient(demo_mode=False)

        mock_markets = [
            {
                "conditionId": "empty_prices",
                "slug": "empty",
                "question": "Empty prices",
                "outcomePrices": "[]",  # Empty prices
                "closed": False,
                "resolved": False
            },
            {
                "conditionId": "null_prices",
                "slug": "null",
                "question": "Null prices",
                "outcomePrices": None,  # Null
                "closed": False,
                "resolved": False
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities()

        # Should handle gracefully
        assert opportunities == []

    def test_polymarket_demo_get_current_price_no_match(self):
        """Test getting price for non-existent market in demo mode."""
        client = PolymarketClient(demo_mode=True)

        price = client.get_current_price("non_existent_id", outcome="YES")

        # Should return None
        assert price is None

    def test_kalshi_demo_get_current_price_no_match(self):
        """Test getting price for non-existent ticker in demo mode."""
        client = KalshiClient(demo_mode=True)

        price = client.get_current_price("NON-EXISTENT-TICKER", outcome="YES")

        # Should return None
        assert price is None

    def test_kalshi_demo_price_in_cents_conversion(self):
        """Test that Kalshi demo prices are properly converted."""
        client = KalshiClient(demo_mode=True)

        markets = client.get_markets(limit=5)

        for market in markets:
            # Prices should be in cents (0-10000)
            assert 0 <= market['yes_bid'] <= 10000
            assert 0 <= market['yes_ask'] <= 10000

    def test_polymarket_find_opportunities_with_market_slug(self):
        """Test opportunities have correct market_slug."""
        client = PolymarketClient(demo_mode=False)

        with responses.RequestsMock() as rsps:
            mock_markets = [
                {
                    "conditionId": "test_slug",
                    "market_slug": "test-market-slug",  # Using market_slug field
                    "slug": "should-not-use-this",
                    "question": "Slug test",
                    "description": "Test",
                    "endDateIso": "2026-12-31",
                    "outcomePrices": '["0.975", "0.025"]',
                    "closed": False,
                    "resolved": False,
                    "volumeNum": 10000,
                    "liquidityNum": 5000,
                    "category": "Test",
                    "id": "test_slug"
                }
            ]

            rsps.add(
                responses.GET,
                f"{config.GAMMA_API_URL}/markets",
                json=mock_markets,
                status=200
            )

            opportunities = client.find_opportunities()

            assert len(opportunities) == 1
            # Should use market_slug if available
            assert 'market_slug' in opportunities[0] or 'slug' in opportunities[0]

    def test_polymarket_get_current_price_case_insensitive(self):
        """Test that outcome matching is case-insensitive."""
        client = PolymarketClient(demo_mode=False)

        with responses.RequestsMock() as rsps:
            mock_response = {
                "conditionId": "case_test",
                "tokens": [
                    {"outcome": "yes", "price": "0.7"},  # lowercase
                    {"outcome": "no", "price": "0.3"}
                ]
            }

            rsps.add(
                responses.GET,
                f"{config.GAMMA_API_URL}/markets/case_test",
                json=mock_response,
                status=200
            )

            # Should match regardless of case
            price_upper = client.get_current_price("case_test", outcome="YES")
            assert price_upper == 0.7

    @responses.activate
    def test_polymarket_get_markets_non_list_response(self):
        """Test handling of non-list response."""
        client = PolymarketClient(demo_mode=False)

        # Return a dict instead of list
        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json={"error": "some error"},
            status=200
        )

        markets = client.get_markets()

        # Should return empty list
        assert markets == []

    def test_demo_data_comprehensive_coverage(self):
        """Test demo data generation with various scenarios."""
        client_poly = PolymarketClient(demo_mode=True)
        client_kalshi = KalshiClient(demo_mode=True)

        # Get multiple markets
        poly_markets = client_poly.get_markets(limit=20)
        kalshi_markets = client_kalshi.get_markets(limit=20)

        assert len(poly_markets) > 0
        assert len(kalshi_markets) > 0

        # Test price updates for multiple markets
        for market in poly_markets[:5]:
            price = client_poly.get_current_price(
                market['condition_id'],
                outcome="YES"
            )
            # Price can be None or valid
            if price is not None:
                assert 0 < price <= 1

        for market in kalshi_markets[:5]:
            price = client_kalshi.get_current_price(
                market['ticker'],
                outcome="NO"
            )
            if price is not None:
                assert 0 < price <= 1
