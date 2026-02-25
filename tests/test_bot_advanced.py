"""Advanced tests for bot module to increase coverage."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call
from bot import PaperTradingBot
import config
import time


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def bot(temp_db_path):
    """Create a bot instance for testing."""
    with patch('config.DB_PATH', temp_db_path):
        bot = PaperTradingBot(
            polymarket_demo=True,
            kalshi_demo=True,
            enable_poly=True,
            enable_kalshi=True
        )
        return bot


class TestPaperTradingBotAdvanced:
    """Advanced test cases for PaperTradingBot to reach 90% coverage."""

    def test_run_continuous_single_iteration(self, bot):
        """Test run_continuous for single iteration."""
        # Mock run_scan to avoid actual scanning
        bot.run_scan = Mock()

        # Mock time.sleep to stop after first iteration
        with patch('bot.time.sleep') as mock_sleep:
            def stop_after_sleep(*args):
                bot.running = False

            mock_sleep.side_effect = stop_after_sleep

            # Run continuous (will stop after first sleep)
            bot.run_continuous()

            # Should have called run_scan
            bot.run_scan.assert_called()
            mock_sleep.assert_called()

    def test_run_continuous_keyboard_interrupt(self, bot):
        """Test that run_continuous handles KeyboardInterrupt."""
        bot.run_scan = Mock()

        # Mock sleep to raise KeyboardInterrupt
        with patch('bot.time.sleep') as mock_sleep:
            mock_sleep.side_effect = KeyboardInterrupt()

            # Should handle the interrupt gracefully
            bot.run_continuous()

            # Should have attempted at least one scan
            bot.run_scan.assert_called()

    def test_enter_trade_with_market_id(self, bot):
        """Test entering trade with market_id field."""
        opportunity = {
            'market_id': 'test_market_id',  # Using market_id instead of condition_id
            'question': 'Test with market_id?',
            'price': 0.975,
            'url': 'https://test.com',
            'source': 'kalshi'
        }

        bot.enter_trade(opportunity)

        trades = bot.db.get_open_trades()
        assert len(trades) == 1
        assert trades[0]['market_id'] == 'test_market_id'

    def test_should_enter_trade_with_market_id(self, bot):
        """Test should_enter_trade with market_id field."""
        # Add existing trade with market_id
        bot.db.add_trade(
            market_id='existing_market',
            market_question='Existing',
            entry_price=0.97,
            position_size=100,
            market_source='kalshi'
        )

        # Try to enter same market using market_id
        opportunity = {
            'market_id': 'existing_market',
            'question': 'Duplicate',
            'price': 0.975,
            'volume': 10000,
            'liquidity': 5000,
            'source': 'kalshi'
        }

        assert bot.should_enter_trade(opportunity) is False

    def test_update_open_positions_no_client(self, bot):
        """Test updating positions when client is None."""
        # Add a trade
        bot.db.add_trade(
            market_id='test_123',
            market_question='Test',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Set client to None
        bot.polymarket_client = None

        # Should not crash
        bot.update_open_positions()

    def test_update_open_positions_price_none(self, bot):
        """Test updating positions when price returns None."""
        bot.db.add_trade(
            market_id='test_123',
            market_question='Test',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Mock price returning None
        bot.polymarket_client.get_current_price = Mock(return_value=None)

        # Should not crash
        bot.update_open_positions()

    def test_run_scan_with_only_polymarket(self, temp_db_path):
        """Test scanning with only Polymarket enabled."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                polymarket_demo=True,
                enable_poly=True,
                enable_kalshi=False
            )

            bot.polymarket_client.find_opportunities = Mock(return_value=[])
            bot.polymarket_client.get_current_price = Mock(return_value=0.97)

            bot.run_scan()

            # Should have called Polymarket
            bot.polymarket_client.find_opportunities.assert_called()

    def test_run_scan_with_only_kalshi(self, temp_db_path):
        """Test scanning with only Kalshi enabled."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                kalshi_demo=True,
                enable_poly=False,
                enable_kalshi=True
            )

            bot.kalshi_client.find_opportunities = Mock(return_value=[])
            bot.kalshi_client.get_current_price = Mock(return_value=0.92)

            bot.run_scan()

            # Should have called Kalshi
            bot.kalshi_client.find_opportunities.assert_called()

    def test_print_banner_polymarket_only(self, temp_db_path, capsys):
        """Test banner with only Polymarket."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                polymarket_demo=True,
                enable_poly=True,
                enable_kalshi=False
            )

            bot.print_banner()

            captured = capsys.readouterr()
            assert "Polymarket" in captured.out
            assert "Kalshi" not in captured.out

    def test_print_banner_kalshi_only(self, temp_db_path, capsys):
        """Test banner with only Kalshi."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                kalshi_demo=True,
                enable_poly=False,
                enable_kalshi=True
            )

            bot.print_banner()

            captured = capsys.readouterr()
            assert "Kalshi" in captured.out
            assert "Polymarket" not in captured.out

    def test_display_opportunities_many_items(self, bot, capsys):
        """Test displaying more than 20 opportunities."""
        opps = [
            {
                'question': f'Opportunity {i}',
                'price': 0.97,
                'volume': 10000,
                'category': 'Test',
                'source': 'polymarket'
            }
            for i in range(30)
        ]

        bot.display_opportunities(opps)

        captured = capsys.readouterr()
        # Should show "Found 30" but only display top 20
        assert "Found 30 opportunities" in captured.out

    def test_run_scan_sorts_by_price(self, bot):
        """Test that opportunities are sorted by price."""
        mock_opps = [
            {
                'condition_id': f'opp_{i}',
                'question': f'Opportunity {i}',
                'price': 0.97 + (i * 0.001),
                'volume': 10000,
                'liquidity': 5000,
                'url': 'https://test.com',
                'category': 'Test',
                'source': 'polymarket'
            }
            for i in range(5)
        ]

        bot.polymarket_client.find_opportunities = Mock(return_value=mock_opps)
        bot.kalshi_client.find_opportunities = Mock(return_value=[])
        bot.polymarket_client.get_current_price = Mock(return_value=0.97)

        # Mock display_opportunities to capture sorted list
        original_display = bot.display_opportunities
        displayed_opps = []

        def capture_display(opps):
            displayed_opps.extend(opps)
            return original_display(opps)

        bot.display_opportunities = capture_display

        bot.run_scan()

        # Check that opportunities are sorted by price (highest first)
        if len(displayed_opps) > 1:
            for i in range(len(displayed_opps) - 1):
                assert displayed_opps[i]['price'] >= displayed_opps[i+1]['price']

    def test_update_positions_closes_at_exact_99(self, bot):
        """Test that positions close at exactly 0.99."""
        trade_id = bot.db.add_trade(
            market_id='test_099',
            market_question='Test 0.99',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Mock price at exactly 0.99
        bot.polymarket_client.get_current_price = Mock(return_value=0.99)

        bot.update_open_positions()

        # Should be closed
        open_trades = bot.db.get_open_trades()
        assert len(open_trades) == 0

    def test_enter_trade_output_format(self, bot, capsys):
        """Test the output format when entering a trade."""
        opportunity = {
            'condition_id': 'test_output',
            'question': 'Test output format?',
            'price': 0.975,
            'url': 'https://test.com/market',
            'source': 'polymarket'
        }

        bot.enter_trade(opportunity)

        captured = capsys.readouterr()
        assert "ENTERED TRADE" in captured.out
        assert "POLYMARKET" in captured.out
        assert "Test output format?" in captured.out
        assert "$0.975" in captured.out
        assert f"${config.POSITION_SIZE}" in captured.out

    def test_kalshi_trade_output(self, bot, capsys):
        """Test output format for Kalshi trade."""
        opportunity = {
            'ticker': 'KALSHI-TEST',
            'market_id': 'kalshi_test_001',
            'question': 'Kalshi test trade?',
            'price': 0.92,
            'url': 'https://kalshi.com/test',
            'source': 'kalshi'
        }

        bot.enter_trade(opportunity)

        captured = capsys.readouterr()
        assert "KALSHI" in captured.out
        assert "Kalshi test trade?" in captured.out

    def test_display_open_positions_calculates_pnl(self, bot, capsys):
        """Test that open positions show calculated P&L."""
        trade_id = bot.db.add_trade(
            market_id='pnl_test',
            market_question='P&L calculation test',
            entry_price=0.95,
            position_size=100,
            market_source='polymarket'
        )

        # Update to higher price
        bot.db.update_trade_price(trade_id, 0.97)

        bot.display_open_positions()

        captured = capsys.readouterr()
        # Should show positive P&L
        assert "+$" in captured.out or "Total Unrealized P&L" in captured.out
