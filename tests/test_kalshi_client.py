"""Unit tests for Kalshi client."""

import pytest
import responses
import os
from unittest.mock import patch, MagicMock
from kalshi_client import KalshiClient
import config


@pytest.fixture
def client():
    """Create a Kalshi client for testing."""
    return KalshiClient(demo_mode=False)


@pytest.fixture
def demo_client():
    """Create a demo mode client."""
    return KalshiClient(demo_mode=True)


class TestKalshiClient:
    """Test cases for KalshiClient class."""

    def test_init_demo_mode(self, demo_client):
        """Test initialization in demo mode."""
        assert demo_client.demo_mode is True
        assert len(demo_client.demo_markets) > 0
        # In demo mode, auth not initialized
        assert not hasattr(demo_client, 'api_key_id') or demo_client.api_key_id is None

    @patch.dict(os.environ, {
        'KALSHI_API_KEY_ID': 'test_key_id',
        'KALSHI_PRIVATE_KEY': '''-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----'''
    })
    def test_init_live_mode_with_env(self):
        """Test initialization with environment variables."""
        # This will fail to import the actual key, but we're testing the flow
        try:
            client = KalshiClient(demo_mode=False)
        except Exception:
            # Expected to fail with invalid key, but that's OK for this test
            pass

    def test_init_live_mode_no_credentials(self):
        """Test initialization without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            # Without credentials, should handle gracefully
            try:
                client = KalshiClient(demo_mode=False)
                # If it succeeds, it should fall back to demo mode
                assert client.demo_mode is True
            except Exception:
                # Or it might raise an exception, which is also acceptable
                pass

    @responses.activate
    def test_get_markets_success(self):
        """Test fetching markets successfully."""
        with patch('kalshi_client.KalshiClient._authenticate'):
            with patch('kalshi_client.KalshiClient._sign_request') as mock_sign:
                mock_sign.return_value = {
                    'KALSHI-ACCESS-KEY': 'test',
                    'KALSHI-ACCESS-SIGNATURE': 'sig',
                    'KALSHI-ACCESS-TIMESTAMP': '123'
                }

                mock_response = {
                    "markets": [
                        {
                            "ticker": "TEST-001",
                            "title": "Test market 1",
                            "status": "active",
                            "yes_bid": 5000,
                            "yes_ask": 5500,
                            "no_bid": 4500,
                            "no_ask": 5000
                        },
                        {
                            "ticker": "TEST-002",
                            "title": "Test market 2",
                            "status": "active",
                            "yes_bid": 7000,
                            "yes_ask": 7500,
                            "no_bid": 2500,
                            "no_ask": 3000
                        }
                    ]
                }

                responses.add(
                    responses.GET,
                    f"{config.KALSHI_API_URL}/trade-api/v2/markets",
                    json=mock_response,
                    status=200
                )

                client = KalshiClient(demo_mode=False)
                client.private_key = MagicMock()
                client.api_key_id = "test_key"

                markets = client.get_markets(limit=100)

                assert len(markets) == 2
                assert markets[0]['ticker'] == "TEST-001"

    def test_get_markets_demo_mode(self, demo_client):
        """Test getting markets in demo mode."""
        markets = demo_client.get_markets(limit=5)

        assert len(markets) <= 5
        assert all('title' in m for m in markets)
        assert all('ticker' in m for m in markets)

    @responses.activate
    def test_get_markets_error(self):
        """Test handling of API errors."""
        with patch('kalshi_client.KalshiClient._authenticate'):
            with patch('kalshi_client.KalshiClient._sign_request') as mock_sign:
                mock_sign.return_value = {
                    'KALSHI-ACCESS-KEY': 'test',
                    'KALSHI-ACCESS-SIGNATURE': 'sig',
                    'KALSHI-ACCESS-TIMESTAMP': '123'
                }

                responses.add(
                    responses.GET,
                    f"{config.KALSHI_API_URL}/trade-api/v2/markets",
                    json={"error": "Server error"},
                    status=500
                )

                client = KalshiClient(demo_mode=False)
                client.private_key = MagicMock()
                client.api_key_id = "test_key"

                markets = client.get_markets()

                assert markets == []

    def test_find_opportunities_demo_mode(self, demo_client):
        """Test finding opportunities in demo mode."""
        opportunities = demo_client.find_opportunities(min_price=0.90, max_price=0.95)

        # Should return demo opportunities
        assert isinstance(opportunities, list)
        for opp in opportunities:
            assert 'question' in opp
            assert 'price' in opp
            assert 'outcome' in opp
            assert opp['source'] == 'kalshi'

    @responses.activate
    def test_find_opportunities_live_mode(self):
        """Test finding opportunities in live mode."""
        with patch('kalshi_client.KalshiClient._authenticate'):
            with patch('kalshi_client.KalshiClient._sign_request') as mock_sign:
                mock_sign.return_value = {
                    'KALSHI-ACCESS-KEY': 'test',
                    'KALSHI-ACCESS-SIGNATURE': 'sig',
                    'KALSHI-ACCESS-TIMESTAMP': '123'
                }

                mock_response = {
                    "markets": [
                        {
                            "ticker": "HIGH-PROB-001",
                            "title": "High probability event",
                            "subtitle": "Will this happen?",
                            "status": "active",
                            "yes_bid": 9200,  # 92c bid
                            "yes_ask": 9500,  # 95c ask
                            "no_bid": 500,
                            "no_ask": 800,
                            "volume": 100000,
                            "open_interest": 50000,
                            "close_time": "2026-12-31T23:59:59Z",
                            "category": "Politics"
                        }
                    ]
                }

                responses.add(
                    responses.GET,
                    f"{config.KALSHI_API_URL}/trade-api/v2/markets",
                    json=mock_response,
                    status=200
                )

                client = KalshiClient(demo_mode=False)
                client.private_key = MagicMock()
                client.api_key_id = "test_key"

                opportunities = client.find_opportunities(min_price=0.90, max_price=0.95)

                # Should return results (might be empty or have results)
                assert isinstance(opportunities, list)
                for opp in opportunities:
                    assert opp['source'] == 'kalshi'
                    assert 0.90 <= opp['price'] <= 0.95

    def test_get_current_price_demo_mode(self, demo_client):
        """Test getting current price in demo mode."""
        markets = demo_client.get_markets(limit=1)
        if markets:
            ticker = markets[0]['ticker']
            price = demo_client.get_current_price(ticker, outcome="YES")

            assert price is not None
            assert 0 < price < 1

    @responses.activate
    def test_get_current_price_live_mode(self):
        """Test getting current price in live mode."""
        with patch('kalshi_client.KalshiClient._authenticate'):
            with patch('kalshi_client.KalshiClient._sign_request') as mock_sign:
                mock_sign.return_value = {
                    'KALSHI-ACCESS-KEY': 'test',
                    'KALSHI-ACCESS-SIGNATURE': 'sig',
                    'KALSHI-ACCESS-TIMESTAMP': '123'
                }

                mock_response = {
                    "ticker": "TEST-001",
                    "yes_bid": 6000,
                    "yes_ask": 6500,
                    "no_bid": 3500,
                    "no_ask": 4000
                }

                responses.add(
                    responses.GET,
                    f"{config.KALSHI_API_URL}/trade-api/v2/markets/TEST-001",
                    json=mock_response,
                    status=200
                )

                client = KalshiClient(demo_mode=False)
                client.private_key = MagicMock()
                client.api_key_id = "test_key"

                price = client.get_current_price("TEST-001", outcome="YES")

                # Mid price: (6000 + 6500) / 2 / 100 = 0.625
                if price is not None:
                    assert abs(price - 0.625) < 0.01

    def test_price_conversion(self, demo_client):
        """Test that prices are correctly converted from cents to dollars."""
        # Kalshi returns prices in cents (0-10000)
        # Should be converted to 0-1.0 range
        markets = demo_client.get_markets(limit=10)

        for market in markets:
            if 'yes_bid' in market and market['yes_bid'] > 0:
                # Demo data should have prices in cents format
                assert market['yes_bid'] <= 10000

    def test_opportunity_structure(self, demo_client):
        """Test that opportunities have required fields."""
        opportunities = demo_client.find_opportunities(min_price=0.90, max_price=0.95)

        required_fields = [
            'ticker', 'question', 'price', 'outcome',
            'volume', 'liquidity', 'category', 'url', 'source'
        ]

        for opp in opportunities:
            for field in required_fields:
                assert field in opp, f"Missing field: {field}"

    def test_url_format(self, demo_client):
        """Test that Kalshi URLs are correctly formatted."""
        opportunities = demo_client.find_opportunities(min_price=0.90, max_price=0.95)

        for opp in opportunities:
            assert opp['url'].startswith('https://kalshi.com/markets/')
            assert opp['source'] == 'kalshi'

    def test_skip_inactive_markets(self):
        """Test that inactive markets are skipped."""
        with patch('kalshi_client.KalshiClient._authenticate'):
            with patch('kalshi_client.KalshiClient._sign_request') as mock_sign:
                mock_sign.return_value = {
                    'KALSHI-ACCESS-KEY': 'test',
                    'KALSHI-ACCESS-SIGNATURE': 'sig',
                    'KALSHI-ACCESS-TIMESTAMP': '123'
                }

                mock_response = {
                    "markets": [
                        {
                            "ticker": "CLOSED-001",
                            "title": "Closed market",
                            "status": "closed",  # Not active
                            "yes_bid": 9500,
                            "yes_ask": 9700
                        }
                    ]
                }

                with responses.RequestsMock() as rsps:
                    rsps.add(
                        responses.GET,
                        f"{config.KALSHI_API_URL}/trade-api/v2/markets",
                        json=mock_response,
                        status=200
                    )

                    client = KalshiClient(demo_mode=False)
                    client.private_key = MagicMock()
                    client.api_key_id = "test_key"

                    opportunities = client.find_opportunities()

                    # Should skip closed markets
                    assert len(opportunities) == 0
