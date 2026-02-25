"""Unit tests for bot module."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from bot import PaperTradingBot
import config


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


class TestPaperTradingBot:
    """Test cases for PaperTradingBot class."""

    def test_init_both_markets_enabled(self, temp_db_path):
        """Test initialization with both markets enabled."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                polymarket_demo=True,
                kalshi_demo=True,
                enable_poly=True,
                enable_kalshi=True
            )

            assert bot.polymarket_client is not None
            assert bot.kalshi_client is not None
            assert bot.demo_mode is True

    def test_init_only_polymarket(self, temp_db_path):
        """Test initialization with only Polymarket."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                polymarket_demo=True,
                enable_poly=True,
                enable_kalshi=False
            )

            assert bot.polymarket_client is not None
            assert bot.kalshi_client is None

    def test_init_only_kalshi(self, temp_db_path):
        """Test initialization with only Kalshi."""
        with patch('config.DB_PATH', temp_db_path):
            bot = PaperTradingBot(
                kalshi_demo=True,
                enable_poly=False,
                enable_kalshi=True
            )

            assert bot.polymarket_client is None
            assert bot.kalshi_client is not None

    def test_should_enter_trade_basic(self, bot):
        """Test should_enter_trade with valid opportunity."""
        opportunity = {
            'condition_id': 'new_opp',
            'question': 'New opportunity?',
            'price': 0.975,
            'volume': 10000,
            'liquidity': 5000,
            'source': 'polymarket'
        }

        assert bot.should_enter_trade(opportunity) is True

    def test_should_enter_trade_duplicate(self, bot):
        """Test that duplicate positions are rejected."""
        # Enter first trade
        bot.db.add_trade(
            market_id='existing_123',
            market_question='Existing trade',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Try to enter same market
        opportunity = {
            'condition_id': 'existing_123',
            'question': 'Existing trade',
            'price': 0.975,
            'volume': 10000,
            'liquidity': 5000,
            'source': 'polymarket'
        }

        assert bot.should_enter_trade(opportunity) is False

    def test_should_enter_trade_position_limit(self, bot):
        """Test that position limits are enforced."""
        # Fill up to max positions
        for i in range(config.MAX_POSITIONS):
            bot.db.add_trade(
                market_id=f'trade_{i}',
                market_question=f'Trade {i}',
                entry_price=0.97,
                position_size=100,
                market_source='polymarket'
            )

        # Try to enter another
        opportunity = {
            'condition_id': 'new_trade',
            'question': 'New trade',
            'price': 0.975,
            'volume': 10000,
            'liquidity': 5000,
            'source': 'polymarket'
        }

        assert bot.should_enter_trade(opportunity) is False

    def test_should_enter_trade_low_liquidity(self, bot):
        """Test that low liquidity trades are rejected."""
        opportunity = {
            'condition_id': 'low_liq',
            'question': 'Low liquidity',
            'price': 0.975,
            'volume': 10000,
            'liquidity': 100,  # Below MIN_LIQUIDITY
            'source': 'polymarket'
        }

        assert bot.should_enter_trade(opportunity) is False

    def test_should_enter_trade_low_volume(self, bot):
        """Test that low volume trades are rejected."""
        opportunity = {
            'condition_id': 'low_vol',
            'question': 'Low volume',
            'price': 0.975,
            'volume': 100,  # Below MIN_VOLUME_24H
            'liquidity': 5000,
            'source': 'polymarket'
        }

        assert bot.should_enter_trade(opportunity) is False

    def test_enter_trade(self, bot):
        """Test entering a trade."""
        opportunity = {
            'condition_id': 'test_123',
            'question': 'Test question?',
            'price': 0.975,
            'url': 'https://test.com',
            'source': 'polymarket'
        }

        bot.enter_trade(opportunity)

        # Verify trade was added
        trades = bot.db.get_open_trades()
        assert len(trades) == 1
        assert trades[0]['market_id'] == 'test_123'
        assert trades[0]['entry_price'] == 0.975
        assert trades[0]['position_size'] == config.POSITION_SIZE

    def test_update_open_positions_polymarket(self, bot):
        """Test updating Polymarket positions."""
        # Add a trade
        bot.db.add_trade(
            market_id='poly_123',
            market_question='Polymarket trade',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Mock the price update
        bot.polymarket_client.get_current_price = Mock(return_value=0.98)

        bot.update_open_positions()

        # Verify price was updated
        trades = bot.db.get_open_trades()
        assert trades[0]['current_price'] == 0.98

    def test_update_open_positions_closes_winner(self, bot):
        """Test that positions are closed when price hits 1.0."""
        trade_id = bot.db.add_trade(
            market_id='winner_123',
            market_question='Winner trade',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Mock price at 1.0 (resolved)
        bot.polymarket_client.get_current_price = Mock(return_value=1.0)

        bot.update_open_positions()

        # Verify trade was closed
        open_trades = bot.db.get_open_trades()
        assert len(open_trades) == 0

        closed_trades = bot.db.get_all_closed_trades()
        assert len(closed_trades) == 1
        assert closed_trades[0]['outcome'] == 'WON'

    def test_update_open_positions_closes_loser(self, bot):
        """Test that positions are closed when price drops below threshold."""
        trade_id = bot.db.add_trade(
            market_id='loser_123',
            market_question='Loser trade',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Mock price dropping below 0.80
        bot.polymarket_client.get_current_price = Mock(return_value=0.75)

        bot.update_open_positions()

        # Verify trade was closed
        closed_trades = bot.db.get_all_closed_trades()
        assert len(closed_trades) == 1
        assert closed_trades[0]['outcome'] == 'LOST'

    def test_update_open_positions_kalshi(self, bot):
        """Test updating Kalshi positions."""
        bot.db.add_trade(
            market_id='KALSHI-001',
            market_question='Kalshi trade',
            entry_price=0.92,
            position_size=100,
            market_source='kalshi'
        )

        bot.kalshi_client.get_current_price = Mock(return_value=0.95)

        bot.update_open_positions()

        trades = bot.db.get_open_trades()
        assert trades[0]['current_price'] == 0.95

    def test_update_open_positions_no_trades(self, bot):
        """Test updating when there are no open positions."""
        # Should not crash
        bot.update_open_positions()

    def test_display_stats(self, bot, capsys):
        """Test displaying statistics."""
        # Add and close some trades
        for i in range(3):
            trade_id = bot.db.add_trade(
                market_id=f'trade_{i}',
                market_question=f'Trade {i}',
                entry_price=0.97,
                position_size=100,
                market_source='polymarket'
            )
            bot.db.close_trade(trade_id, exit_price=1.0, outcome='WON')

        bot.display_stats()

        captured = capsys.readouterr()
        assert "PERFORMANCE STATISTICS" in captured.out
        assert "Total Trades:" in captured.out
        assert "Win Rate:" in captured.out

    def test_display_open_positions_with_trades(self, bot, capsys):
        """Test displaying open positions."""
        bot.db.add_trade(
            market_id='test_1',
            market_question='Test question 1',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        bot.display_open_positions()

        captured = capsys.readouterr()
        assert "Open Positions" in captured.out
        assert "Test question 1" in captured.out

    def test_display_open_positions_empty(self, bot, capsys):
        """Test displaying when no positions."""
        bot.display_open_positions()

        captured = capsys.readouterr()
        assert "No open positions" in captured.out

    def test_run_scan_finds_opportunities(self, bot, capsys):
        """Test run_scan finds and displays opportunities."""
        # Mock opportunities
        mock_poly_opps = [
            {
                'condition_id': 'poly_1',
                'question': 'Poly market 1',
                'price': 0.975,
                'volume': 10000,
                'liquidity': 5000,
                'url': 'https://poly.com',
                'category': 'Politics'
            }
        ]

        bot.polymarket_client.find_opportunities = Mock(return_value=mock_poly_opps)
        bot.kalshi_client.find_opportunities = Mock(return_value=[])

        bot.run_scan()

        captured = capsys.readouterr()
        assert "Scanning markets" in captured.out
        assert "Found 1 opportunities" in captured.out

    def test_run_scan_enters_trades(self, bot):
        """Test that run_scan enters qualifying trades."""
        mock_opps = [
            {
                'condition_id': 'auto_enter',
                'question': 'Auto enter trade',
                'price': 0.975,
                'volume': 10000,
                'liquidity': 5000,
                'url': 'https://test.com',
                'category': 'Test',
                'source': 'polymarket'
            }
        ]

        bot.polymarket_client.find_opportunities = Mock(return_value=mock_opps)
        bot.kalshi_client.find_opportunities = Mock(return_value=[])
        bot.polymarket_client.get_current_price = Mock(return_value=0.975)

        bot.run_scan()

        # Verify trade was entered
        trades = bot.db.get_open_trades()
        assert len(trades) == 1
        assert trades[0]['market_id'] == 'auto_enter'

    def test_display_opportunities_empty(self, bot, capsys):
        """Test displaying when no opportunities found."""
        bot.display_opportunities([])

        captured = capsys.readouterr()
        assert "No opportunities found" in captured.out

    def test_display_opportunities_multiple(self, bot, capsys):
        """Test displaying multiple opportunities."""
        opps = [
            {
                'question': f'Opportunity {i}',
                'price': 0.97 + (i * 0.001),
                'volume': 10000,
                'category': 'Test',
                'source': 'polymarket'
            }
            for i in range(5)
        ]

        bot.display_opportunities(opps)

        captured = capsys.readouterr()
        assert "Found 5 opportunities" in captured.out
        assert "Opportunity 0" in captured.out

    def test_print_banner(self, bot, capsys):
        """Test printing bot banner."""
        bot.print_banner()

        captured = capsys.readouterr()
        assert "PAPER TRADING BOT" in captured.out
        assert "Polymarket" in captured.out
        assert "Kalshi" in captured.out
        assert "DEMO" in captured.out

    def test_market_source_routing(self, bot):
        """Test that updates are routed to correct client."""
        # Add Polymarket trade
        bot.db.add_trade(
            market_id='poly_test',
            market_question='Poly',
            entry_price=0.97,
            position_size=100,
            market_source='polymarket'
        )

        # Add Kalshi trade
        bot.db.add_trade(
            market_id='kalshi_test',
            market_question='Kalshi',
            entry_price=0.92,
            position_size=100,
            market_source='kalshi'
        )

        bot.polymarket_client.get_current_price = Mock(return_value=0.98)
        bot.kalshi_client.get_current_price = Mock(return_value=0.93)

        bot.update_open_positions()

        # Verify correct clients were called
        bot.polymarket_client.get_current_price.assert_called_once_with('poly_test')
        bot.kalshi_client.get_current_price.assert_called_once_with('kalshi_test')
