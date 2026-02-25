"""Integration tests to increase coverage."""

import pytest
import tempfile
import os
import unittest.mock
from bot import PaperTradingBot
from database import Database
from polymarket_client import PolymarketClient
from kalshi_client import KalshiClient
import config


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_full_workflow_demo_mode(self, temp_db_path):
        """Test complete workflow in demo mode."""
        with unittest.mock.patch('config.DB_PATH', temp_db_path):
            # Create bot in demo mode
            bot = PaperTradingBot(
                polymarket_demo=True,
                kalshi_demo=True,
                enable_poly=True,
                enable_kalshi=True
            )

            # Run a scan
            bot.run_scan()

            # Check that we have some data
            stats = bot.db.get_performance_stats()
            assert stats is not None

    def test_polymarket_demo_client_workflow(self):
        """Test Polymarket demo client end-to-end."""
        client = PolymarketClient(demo_mode=True)

        # Get markets
        markets = client.get_markets(limit=5)
        assert len(markets) > 0

        # Find opportunities
        opportunities = client.find_opportunities(min_price=0.97, max_price=0.98)
        assert isinstance(opportunities, list)

        # Get price for a market
        if markets:
            cond_id = markets[0]['condition_id']
            price = client.get_current_price(cond_id, outcome="YES")
            assert price is None or (0 < price <= 1)

    def test_kalshi_demo_client_workflow(self):
        """Test Kalshi demo client end-to-end."""
        client = KalshiClient(demo_mode=True)

        # Get markets
        markets = client.get_markets(limit=5)
        assert len(markets) > 0

        # Find opportunities
        opportunities = client.find_opportunities(min_price=0.90, max_price=0.95)
        assert isinstance(opportunities, list)

        # Get price for a market
        if markets:
            ticker = markets[0]['ticker']
            price = client.get_current_price(ticker, outcome="YES")
            assert price is None or (0 < price <= 1)

    def test_database_full_lifecycle(self, temp_db_path):
        """Test database through full trade lifecycle."""
        db = Database(temp_db_path)

        # Add trade
        trade_id = db.add_trade(
            market_id="lifecycle_test",
            market_question="Lifecycle test",
            entry_price=0.97,
            position_size=100,
            market_source="polymarket"
        )

        # Update price
        db.update_trade_price(trade_id, 0.98)

        # Get open trades
        open_trades = db.get_open_trades()
        assert len(open_trades) == 1

        # Close trade
        db.close_trade(trade_id, exit_price=1.0, outcome="WON")

        # Verify stats
        stats = db.get_performance_stats()
        assert stats['total_trades'] == 1
        assert stats['wins'] == 1

    def test_bot_with_mixed_markets(self, temp_db_path):
        """Test bot with both Polymarket and Kalshi."""
        with unittest.mock.patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                polymarket_demo=True,
                kalshi_demo=True,
                enable_poly=True,
                enable_kalshi=True
            )

            # Mock find_opportunities to return controlled data
            from unittest.mock import Mock

            poly_opp = {
                'condition_id': 'poly_test',
                'question': 'Poly test?',
                'price': 0.975,
                'volume': 10000,
                'liquidity': 5000,
                'url': 'https://poly.com',
                'category': 'Test',
                'source': 'polymarket'
            }

            kalshi_opp = {
                'ticker': 'KALSHI-TEST',
                'market_id': 'kalshi_test',
                'question': 'Kalshi test?',
                'price': 0.92,
                'volume': 20000,
                'liquidity': 10000,
                'url': 'https://kalshi.com',
                'category': 'Test',
                'source': 'kalshi'
            }

            bot.polymarket_client.find_opportunities = Mock(return_value=[poly_opp])
            bot.kalshi_client.find_opportunities = Mock(return_value=[kalshi_opp])
            bot.polymarket_client.get_current_price = Mock(return_value=0.975)
            bot.kalshi_client.get_current_price = Mock(return_value=0.92)

            # Run scan
            bot.run_scan()

            # Should have entered trades from both markets
            open_trades = bot.db.get_open_trades()
            sources = [t['market_source'] for t in open_trades]

            # Should have at least one trade
            assert len(open_trades) > 0

    def test_bot_respects_position_limits(self, temp_db_path):
        """Test that bot respects MAX_POSITIONS limit."""
        with unittest.mock.patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(polymarket_demo=True, enable_poly=True, enable_kalshi=False)

            # Fill up to max positions
            for i in range(config.MAX_POSITIONS):
                bot.db.add_trade(
                    market_id=f'limit_test_{i}',
                    market_question=f'Limit test {i}',
                    entry_price=0.97,
                    position_size=100,
                    market_source='polymarket'
                )

            # Try to enter another via run_scan
            from unittest.mock import Mock

            opp = {
                'condition_id': 'should_not_enter',
                'question': 'Should not enter',
                'price': 0.975,
                'volume': 10000,
                'liquidity': 5000,
                'url': 'https://test.com',
                'category': 'Test',
                'source': 'polymarket'
            }

            bot.polymarket_client.find_opportunities = Mock(return_value=[opp])
            bot.polymarket_client.get_current_price = Mock(return_value=0.975)

            bot.run_scan()

            # Should still have MAX_POSITIONS trades, not more
            open_trades = bot.db.get_open_trades()
            assert len(open_trades) == config.MAX_POSITIONS

    def test_price_updates_trigger_closes(self, temp_db_path):
        """Test that price updates trigger automatic trade closes."""
        with unittest.mock.patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(polymarket_demo=True, enable_poly=True, enable_kalshi=False)

            # Add a winning trade
            bot.db.add_trade(
                market_id='auto_close_win',
                market_question='Auto close winner',
                entry_price=0.97,
                position_size=100,
                market_source='polymarket'
            )

            # Add a losing trade
            bot.db.add_trade(
                market_id='auto_close_loss',
                market_question='Auto close loser',
                entry_price=0.97,
                position_size=100,
                market_source='polymarket'
            )

            # Mock prices - one at 1.0 (won), one at 0.5 (lost)
            from unittest.mock import Mock

            def mock_price(market_id, outcome="YES"):
                if market_id == 'auto_close_win':
                    return 1.0
                elif market_id == 'auto_close_loss':
                    return 0.5
                return 0.97

            bot.polymarket_client.get_current_price = Mock(side_effect=mock_price)

            # Update positions
            bot.update_open_positions()

            # Should have no open trades (both closed)
            open_trades = bot.db.get_open_trades()
            assert len(open_trades) == 0

            # Should have 2 closed trades
            closed_trades = bot.db.get_all_closed_trades()
            assert len(closed_trades) == 2

            # Check outcomes
            outcomes = [t['outcome'] for t in closed_trades]
            assert 'WON' in outcomes
            assert 'LOST' in outcomes
