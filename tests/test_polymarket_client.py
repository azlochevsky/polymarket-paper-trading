"""Unit tests for Polymarket client."""

import pytest
import responses
import json
from polymarket_client import PolymarketClient
import config


@pytest.fixture
def client():
    """Create a Polymarket client for testing."""
    return PolymarketClient(demo_mode=False)


@pytest.fixture
def demo_client():
    """Create a demo mode client."""
    return PolymarketClient(demo_mode=True)


class TestPolymarketClient:
    """Test cases for PolymarketClient class."""

    def test_init_demo_mode(self, demo_client):
        """Test initialization in demo mode."""
        assert demo_client.demo_mode is True
        assert len(demo_client.demo_markets) > 0

    def test_init_live_mode(self, client):
        """Test initialization in live mode."""
        assert client.demo_mode is False
        assert client.demo_markets == []

    @responses.activate
    def test_get_markets_success(self, client):
        """Test fetching markets successfully."""
        mock_response = [
            {
                "conditionId": "0x123",
                "question": "Test market 1",
                "slug": "test-market-1",
                "outcomePrices": '["0.5", "0.5"]',
                "closed": False,
                "resolved": False
            },
            {
                "conditionId": "0x456",
                "question": "Test market 2",
                "slug": "test-market-2",
                "outcomePrices": '["0.7", "0.3"]',
                "closed": False,
                "resolved": False
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_response,
            status=200
        )

        markets = client.get_markets(limit=100)

        assert len(markets) == 2
        assert markets[0]['conditionId'] == "0x123"
        assert markets[1]['question'] == "Test market 2"

    @responses.activate
    def test_get_markets_error(self, client):
        """Test handling of API errors."""
        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json={"error": "Server error"},
            status=500
        )

        markets = client.get_markets()

        assert markets == []

    def test_get_markets_demo_mode(self, demo_client):
        """Test getting markets in demo mode."""
        markets = demo_client.get_markets(limit=5)

        assert len(markets) <= 5
        assert all('question' in m for m in markets)

    @responses.activate
    def test_get_market_details_success(self, client):
        """Test fetching market details."""
        mock_response = {
            "conditionId": "0x123",
            "question": "Test market",
            "tokens": [
                {"outcome": "YES", "price": "0.6"},
                {"outcome": "NO", "price": "0.4"}
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
        assert details['conditionId'] == "0x123"
        assert len(details['tokens']) == 2

    @responses.activate
    def test_get_market_details_error(self, client):
        """Test handling of market details errors."""
        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets/0x999",
            json={"error": "Not found"},
            status=404
        )

        details = client.get_market_details("0x999")

        assert details is None

    @responses.activate
    def test_find_opportunities_yes_outcome(self, client):
        """Test finding opportunities with YES outcome in range."""
        mock_markets = [
            {
                "conditionId": "0x123",
                "slug": "high-prob-yes",
                "question": "Will YES win?",
                "description": "Test market",
                "endDateIso": "2026-12-31",
                "outcomePrices": '["0.975", "0.025"]',
                "closed": False,
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000,
                "category": "Politics",
                "id": "market_123"
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)

        assert len(opportunities) == 1
        assert opportunities[0]['outcome'] == "YES"
        assert opportunities[0]['price'] == 0.975
        assert opportunities[0]['question'] == "Will YES win?"

    @responses.activate
    def test_find_opportunities_no_outcome(self, client):
        """Test finding opportunities with NO outcome in range."""
        mock_markets = [
            {
                "conditionId": "0x456",
                "slug": "high-prob-no",
                "question": "Will NO win?",
                "description": "Test market",
                "endDateIso": "2026-12-31",
                "outcomePrices": '["0.025", "0.975"]',
                "closed": False,
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000,
                "category": "Sports",
                "id": "market_456"
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)

        assert len(opportunities) == 1
        assert opportunities[0]['outcome'] == "NO"
        assert opportunities[0]['price'] == 0.975

    @responses.activate
    def test_find_opportunities_both_outcomes(self, client):
        """Test that only one outcome is selected per market."""
        mock_markets = [
            {
                "conditionId": "0x789",
                "slug": "both-high",
                "question": "Both outcomes high?",
                "description": "Test",
                "endDateIso": "2026-12-31",
                "outcomePrices": '["0.975", "0.976"]',  # Both in range
                "closed": False,
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000,
                "category": "Test",
                "id": "market_789"
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)

        # Should only get one opportunity (YES is checked first)
        assert len(opportunities) == 1
        assert opportunities[0]['outcome'] == "YES"

    @responses.activate
    def test_find_opportunities_skip_closed(self, client):
        """Test that closed markets are skipped."""
        mock_markets = [
            {
                "conditionId": "0x111",
                "slug": "closed-market",
                "question": "Closed market",
                "outcomePrices": '["0.975", "0.025"]',
                "closed": True,  # Closed market
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000
            },
            {
                "conditionId": "0x222",
                "slug": "resolved-market",
                "question": "Resolved market",
                "outcomePrices": '["0.975", "0.025"]',
                "closed": False,
                "resolved": True,  # Resolved market
                "volumeNum": 10000,
                "liquidityNum": 5000
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities()

        assert len(opportunities) == 0

    @responses.activate
    def test_find_opportunities_price_out_of_range(self, client):
        """Test that markets outside price range are skipped."""
        mock_markets = [
            {
                "conditionId": "0x333",
                "slug": "low-price",
                "question": "Low price market",
                "outcomePrices": '["0.5", "0.5"]',  # Out of range
                "closed": False,
                "resolved": False,
                "volumeNum": 10000,
                "liquidityNum": 5000
            }
        ]

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets",
            json=mock_markets,
            status=200
        )

        opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)

        assert len(opportunities) == 0

    @responses.activate
    def test_find_opportunities_invalid_json(self, client):
        """Test handling of invalid price JSON."""
        mock_markets = [
            {
                "conditionId": "0x444",
                "slug": "bad-json",
                "question": "Bad JSON market",
                "outcomePrices": "invalid json",  # Invalid JSON
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

        assert len(opportunities) == 0

    @responses.activate
    def test_get_current_price_yes(self, client):
        """Test getting current price for YES outcome."""
        mock_response = {
            "conditionId": "0x123",
            "tokens": [
                {"outcome": "YES", "price": "0.75"},
                {"outcome": "NO", "price": "0.25"}
            ]
        }

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets/0x123",
            json=mock_response,
            status=200
        )

        price = client.get_current_price("0x123", outcome="YES")

        assert price == 0.75

    @responses.activate
    def test_get_current_price_no(self, client):
        """Test getting current price for NO outcome."""
        mock_response = {
            "conditionId": "0x123",
            "tokens": [
                {"outcome": "YES", "price": "0.75"},
                {"outcome": "NO", "price": "0.25"}
            ]
        }

        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets/0x123",
            json=mock_response,
            status=200
        )

        price = client.get_current_price("0x123", outcome="NO")

        assert price == 0.25

    @responses.activate
    def test_get_current_price_not_found(self, client):
        """Test getting price when market not found."""
        responses.add(
            responses.GET,
            f"{config.GAMMA_API_URL}/markets/0x999",
            json={"error": "Not found"},
            status=404
        )

        price = client.get_current_price("0x999", outcome="YES")

        assert price is None

    def test_get_current_price_demo_mode(self, demo_client):
        """Test getting price in demo mode."""
        # Get a demo market
        markets = demo_client.get_markets(limit=1)
        if markets:
            condition_id = markets[0]['condition_id']
            price = demo_client.get_current_price(condition_id, outcome="YES")

            # Price should be updated (simulated movement)
            assert price is not None
            assert 0 < price <= 1  # Can be 1.0 if market resolved

    def test_opportunity_url_format(self, client):
        """Test that opportunity URLs are correctly formatted."""
        # We'll need to mock a market and verify the URL
        with responses.RequestsMock() as rsps:
            mock_markets = [
                {
                    "conditionId": "0x123",
                    "slug": "test-slug",
                    "question": "Test",
                    "description": "Test",
                    "endDateIso": "2026-12-31",
                    "outcomePrices": '["0.975", "0.025"]',
                    "closed": False,
                    "resolved": False,
                    "volumeNum": 10000,
                    "liquidityNum": 5000,
                    "category": "Test",
                    "id": "test_id"
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
            assert opportunities[0]['url'] == "https://polymarket.com/event/test-slug"
            assert opportunities[0]['source'] == "polymarket"
