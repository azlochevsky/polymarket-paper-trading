"""Final tests to push coverage to 90%."""

import pytest
import responses
import sys
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import config


class TestFinalPush:
    """Tests to reach 90% coverage."""

    def test_main_function_help(self):
        """Test main function with --help argument."""
        from bot import main

        # Mock sys.argv
        with patch.object(sys, 'argv', ['bot.py', '--help']):
            # Should exit with code 0
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_function_stats_mode(self):
        """Test main function in stats mode."""
        from bot import main

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            with patch('config.DB_PATH', path):
                with patch.object(sys, 'argv', ['bot.py', '--stats']):
                    # Should run without error
                    main()
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_main_function_scan_mode(self):
        """Test main function in scan mode."""
        from bot import main

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            with patch('config.DB_PATH', path):
                with patch.object(sys, 'argv', ['bot.py', '--demo-poly', '--demo-kalshi', '--scan']):
                    # Should run scan once
                    main()
        finally:
            if os.path.exists(path):
                os.unlink(path)


    def test_main_with_market_flags(self):
        """Test main with various market enable/disable flags."""
        from bot import main

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            # Test --no-poly
            with patch('config.DB_PATH', path):
                with patch.object(sys, 'argv', ['bot.py', '--no-poly', '--demo-kalshi', '--scan']):
                    main()

            # Test --no-kalshi
            with patch('config.DB_PATH', path):
                with patch.object(sys, 'argv', ['bot.py', '--demo-poly', '--no-kalshi', '--scan']):
                    main()
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @responses.activate
    def test_kalshi_client_live_api_paths(self):
        """Test Kalshi client live API code paths."""
        from kalshi_client import KalshiClient

        # Mock successful authentication
        with patch('kalshi_client.KalshiClient._authenticate'):
            with patch('kalshi_client.KalshiClient._sign_request') as mock_sign:
                mock_sign.return_value = {
                    'KALSHI-ACCESS-KEY': 'test_key',
                    'KALSHI-ACCESS-SIGNATURE': 'test_sig',
                    'KALSHI-ACCESS-TIMESTAMP': '12345'
                }

                # Mock market response
                mock_markets_response = {
                    "markets": [
                        {
                            "ticker": "TEST-001",
                            "title": "Test market",
                            "subtitle": "Subtitle",
                            "status": "active",
                            "yes_bid": 9100,
                            "yes_ask": 9300,
                            "no_bid": 700,
                            "no_ask": 900,
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
                    json=mock_markets_response,
                    status=200
                )

                # Mock single market response
                mock_market_response = {
                    "ticker": "TEST-001",
                    "yes_bid": 9100,
                    "yes_ask": 9300,
                    "no_bid": 700,
                    "no_ask": 900
                }

                responses.add(
                    responses.GET,
                    f"{config.KALSHI_API_URL}/trade-api/v2/markets/TEST-001",
                    json=mock_market_response,
                    status=200
                )

                client = KalshiClient(demo_mode=False)
                client.private_key = MagicMock()
                client.api_key_id = "test_key"

                # Test get_markets
                markets = client.get_markets(limit=100)
                assert isinstance(markets, list)

                # Test find_opportunities
                opps = client.find_opportunities(min_price=0.90, max_price=0.95)
                assert isinstance(opps, list)

                # Test get_current_price
                price = client.get_current_price("TEST-001", outcome="YES")
                if price is not None:
                    assert 0 < price < 1

    def test_polymarket_client_error_handling_paths(self):
        """Test Polymarket client error handling."""
        from polymarket_client import PolymarketClient

        client = PolymarketClient(demo_mode=False)

        with responses.RequestsMock() as rsps:
            # Test timeout
            rsps.add(
                responses.GET,
                f"{config.GAMMA_API_URL}/markets",
                body="Timeout",
                status=504
            )

            markets = client.get_markets()
            assert markets == []

        with responses.RequestsMock() as rsps:
            # Test connection error for market details
            rsps.add(
                responses.GET,
                f"{config.GAMMA_API_URL}/markets/error_test",
                body="Error",
                status=500
            )

            details = client.get_market_details("error_test")
            assert details is None


    def test_comprehensive_demo_mode_coverage(self):
        """Comprehensive test of demo mode."""
        from bot import PaperTradingBot

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            with patch('config.DB_PATH', path):
                # Test with both demo modes
                bot = PaperTradingBot(
                    polymarket_demo=True,
                    kalshi_demo=True,
                    enable_poly=True,
                    enable_kalshi=True
                )

                # Run multiple operations
                bot.print_banner()
                bot.run_scan()
                bot.display_stats()
                bot.display_open_positions()

                # Update positions
                bot.update_open_positions()

                # Check stats
                stats = bot.db.get_performance_stats()
                assert isinstance(stats, dict)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_kalshi_demo_price_updates_coverage(self):
        """Test Kalshi demo price update edge cases."""
        from kalshi_demo_data import get_demo_price_update

        # Test multiple price levels
        test_prices = [0.1, 0.5, 0.8, 0.95, 0.99]

        for price in test_prices:
            for _ in range(5):
                new_price = get_demo_price_update("TEST-001", price)
                assert 0 < new_price <= 1

    def test_polymarket_demo_multiple_outcomes(self):
        """Test Polymarket demo with multiple outcome queries."""
        from polymarket_client import PolymarketClient

        client = PolymarketClient(demo_mode=True)

        markets = client.get_markets(limit=3)

        if markets:
            for market in markets:
                cond_id = market['condition_id']

                # Test both YES and NO outcomes
                yes_price = client.get_current_price(cond_id, outcome="YES")
                no_price = client.get_current_price(cond_id, outcome="NO")

                # At least one should return a price
                assert yes_price is not None or no_price is not None

    def test_config_values_comprehensive(self):
        """Comprehensive test of all config values."""
        # Test all config parameters are accessible
        assert hasattr(config, 'MIN_PRICE')
        assert hasattr(config, 'MAX_PRICE')
        assert hasattr(config, 'POLYMARKET_FEE')
        assert hasattr(config, 'POSITION_SIZE')
        assert hasattr(config, 'MAX_POSITIONS')
        assert hasattr(config, 'MIN_LIQUIDITY')
        assert hasattr(config, 'MIN_VOLUME_24H')
        assert hasattr(config, 'POLYMARKET_API_URL')
        assert hasattr(config, 'GAMMA_API_URL')
        assert hasattr(config, 'KALSHI_API_URL')
        assert hasattr(config, 'ENABLE_POLYMARKET')
        assert hasattr(config, 'ENABLE_KALSHI')
        assert hasattr(config, 'DB_PATH')
        assert hasattr(config, 'REFRESH_INTERVAL')

        # Test values are reasonable
        assert 0 < config.MIN_PRICE < config.MAX_PRICE < 1
        assert config.POLYMARKET_FEE >= 0
        assert config.POSITION_SIZE > 0
        assert config.MAX_POSITIONS > 0
        assert config.REFRESH_INTERVAL > 0
