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
    with patch('bot.Database') as mock_db:
        mock_db.return_value = MagicMock()
        bot = PaperTradingBot(
            demo_mode=True,
            polymarket_demo=True,
            kalshi_demo=True,
            enable_poly=True,
            enable_kalshi=True
        )
        bot.db = mock_db.return_value
        return bot


class TestPaperTradingBot:
    """Test cases for PaperTradingBot class."""

    def test_init_both_markets_enabled(self, temp_db_path):
        """Test initialization with both markets enabled."""
        with patch('bot.Database'):
            bot = PaperTradingBot(
                polymarket_demo=True,
                kalshi_demo=True,
                enable_poly=True,
                enable_kalshi=True
            )

            assert bot.polymarket_client is not None
            assert bot.kalshi_client is not None

    def test_init_only_polymarket(self, temp_db_path):
        """Test initialization with only Polymarket."""
        with patch('bot.Database'):
            bot = PaperTradingBot(
                polymarket_demo=True,
                enable_poly=True,
                enable_kalshi=False
            )

            assert bot.polymarket_client is not None
            assert bot.kalshi_client is None

    def test_init_only_kalshi(self, temp_db_path):
        """Test initialization with only Kalshi."""
        with patch('bot.Database'):
            bot = PaperTradingBot(
                kalshi_demo=True,
                enable_poly=False,
                enable_kalshi=True
            )

            assert bot.polymarket_client is None
            assert bot.kalshi_client is not None

    def test_find_opportunities_both_markets(self, bot):
        """Test finding opportunities from both markets."""
        # Mock opportunities from both markets
        poly_opps = [
            {
                'condition_id': 'poly_1',
                'question': 'Poly market 1',
                'price': 0.975,
                'source': 'polymarket',
                'volume': 10000,
                'liquidity': 5000
            }
        ]

        kalshi_opps = [
            {
                'ticker': 'KALSHI-001',
                'question': 'Kalshi market 1',
                'price': 0.92,
                'source': 'kalshi',
                'volume': 20000,
                'liquidity': 10000
            }
        ]

        bot.polymarket_client.find_opportunities = Mock(return_value=poly_opps)
        bot.kalshi_client.find_opportunities = Mock(return_value=kalshi_opps)

        opportunities = bot.find_opportunities()

        assert len(opportunities) == 2
        assert any(o['source'] == 'polymarket' for o in opportunities)
        assert any(o['source'] == 'kalshi' for o in opportunities)

    def test_find_opportunities_filters_low_liquidity(self, bot):
        """Test that opportunities below minimum liquidity are filtered."""
        opportunities = [
            {
                'condition_id': 'high_liq',
                'question': 'High liquidity',
                'price': 0.975,
                'source': 'polymarket',
                'volume': 10000,
                'liquidity': 5000  # Above MIN_LIQUIDITY
            },
            {
                'condition_id': 'low_liq',
                'question': 'Low liquidity',
                'price': 0.975,
                'source': 'polymarket',
                'volume': 10000,
                'liquidity': 500  # Below MIN_LIQUIDITY
            }
        ]

        bot.polymarket_client.find_opportunities = Mock(return_value=opportunities)
        bot.kalshi_client = None

        filtered = bot.find_opportunities()

        # Should only include high liquidity market
        assert len(filtered) == 1
        assert filtered[0]['condition_id'] == 'high_liq'

    def test_find_opportunities_filters_low_volume(self, bot):
        """Test that opportunities below minimum volume are filtered."""
        opportunities = [
            {
                'condition_id': 'high_vol',
                'question': 'High volume',
                'price': 0.975,
                'source': 'polymarket',
                'volume': 10000,  # Above MIN_VOLUME_24H
                'liquidity': 5000
            },
            {
                'condition_id': 'low_vol',
                'question': 'Low volume',
                'price': 0.975,
                'source': 'polymarket',
                'volume': 100,  # Below MIN_VOLUME_24H
                'liquidity': 5000
            }
        ]

        bot.polymarket_client.find_opportunities = Mock(return_value=opportunities)
        bot.kalshi_client = None

        filtered = bot.find_opportunities()

        assert len(filtered) == 1
        assert filtered[0]['condition_id'] == 'high_vol'

    def test_enter_trade_success(self, bot):
        """Test successfully entering a trade."""
        opportunity = {
            'condition_id': 'test_123',
            'market_slug': 'test-market',
            'ticker': 'TEST-001',
            'question': 'Test question?',
            'price': 0.975,
            'outcome': 'YES',
            'url': 'https://test.com',
            'source': 'polymarket'
        }

        bot.db.record_trade = Mock(return_value=1)

        trade_id = bot.enter_trade(opportunity)

        assert trade_id == 1
        bot.db.record_trade.assert_called_once()

    def test_enter_trade_respects_max_positions(self, bot):
        """Test that bot doesn't exceed maximum positions."""
        # Mock MAX_POSITIONS open trades
        mock_open_trades = [{'id': i} for i in range(config.MAX_POSITIONS)]
        bot.db.get_open_trades = Mock(return_value=mock_open_trades)

        opportunity = {
            'condition_id': 'test_123',
            'market_slug': 'test-market',
            'question': 'Test?',
            'price': 0.975,
            'outcome': 'YES',
            'url': 'https://test.com',
            'source': 'polymarket'
        }

        trade_id = bot.enter_trade(opportunity)

        # Should not enter trade
        assert trade_id is None
        bot.db.record_trade.assert_not_called()

    def test_enter_trade_skips_duplicates(self, bot):
        """Test that duplicate positions are skipped."""
        # Mock existing trade with same condition_id
        mock_open_trades = [
            {
                'id': 1,
                'condition_id': 'existing_123',
                'market_slug': 'existing-market'
            }
        ]
        bot.db.get_open_trades = Mock(return_value=mock_open_trades)

        opportunity = {
            'condition_id': 'existing_123',  # Same as existing
            'market_slug': 'existing-market',
            'question': 'Test?',
            'price': 0.975,
            'outcome': 'YES',
            'url': 'https://test.com',
            'source': 'polymarket'
        }

        trade_id = bot.enter_trade(opportunity)

        assert trade_id is None
        bot.db.record_trade.assert_not_called()

    def test_update_positions_polymarket(self, bot):
        """Test updating Polymarket positions."""
        mock_open_trades = [
            {
                'id': 1,
                'condition_id': 'poly_123',
                'market_slug': 'poly-market',
                'outcome': 'YES',
                'entry_price': 0.975,
                'market_source': 'polymarket'
            }
        ]

        bot.db.get_open_trades = Mock(return_value=mock_open_trades)
        bot.polymarket_client.get_current_price = Mock(return_value=0.98)
        bot.db.update_position = Mock()
        bot.db.close_trade = Mock()

        bot.update_positions()

        # Should update position
        bot.polymarket_client.get_current_price.assert_called_once_with(
            'poly_123', outcome='YES'
        )
        bot.db.update_position.assert_called()

    def test_update_positions_kalshi(self, bot):
        """Test updating Kalshi positions."""
        mock_open_trades = [
            {
                'id': 1,
                'condition_id': 'KALSHI-001',
                'market_slug': 'kalshi-market',
                'outcome': 'YES',
                'entry_price': 0.92,
                'market_source': 'kalshi'
            }
        ]

        bot.db.get_open_trades = Mock(return_value=mock_open_trades)
        bot.kalshi_client.get_current_price = Mock(return_value=0.95)
        bot.db.update_position = Mock()
        bot.db.close_trade = Mock()

        bot.update_positions()

        bot.kalshi_client.get_current_price.assert_called_once()
        bot.db.update_position.assert_called()

    def test_update_positions_closes_winning_trade(self, bot):
        """Test that winning trades are automatically closed."""
        mock_open_trades = [
            {
                'id': 1,
                'condition_id': 'winner_123',
                'market_slug': 'winner',
                'outcome': 'YES',
                'entry_price': 0.975,
                'market_source': 'polymarket'
            }
        ]

        bot.db.get_open_trades = Mock(return_value=mock_open_trades)
        bot.polymarket_client.get_current_price = Mock(return_value=1.0)  # Resolved to YES
        bot.db.close_trade = Mock()

        bot.update_positions()

        # Should close as won
        bot.db.close_trade.assert_called_once()
        call_args = bot.db.close_trade.call_args[0]
        assert call_args[0] == 1  # trade_id
        assert call_args[1] == 1.0  # exit_price
        assert call_args[2] == "WON"  # outcome

    def test_update_positions_closes_losing_trade(self, bot):
        """Test that losing trades are automatically closed."""
        mock_open_trades = [
            {
                'id': 1,
                'condition_id': 'loser_123',
                'market_slug': 'loser',
                'outcome': 'YES',
                'entry_price': 0.975,
                'market_source': 'polymarket'
            }
        ]

        bot.db.get_open_trades = Mock(return_value=mock_open_trades)
        bot.polymarket_client.get_current_price = Mock(return_value=0.0)  # Resolved to NO
        bot.db.close_trade = Mock()

        bot.update_positions()

        # Should close as lost
        bot.db.close_trade.assert_called_once()
        call_args = bot.db.close_trade.call_args[0]
        assert call_args[0] == 1
        assert call_args[1] == 0.0
        assert call_args[2] == "LOST"

    def test_scan_markets_enters_new_trades(self, bot):
        """Test that scan_markets enters new trades."""
        opportunities = [
            {
                'condition_id': 'new_opp',
                'market_slug': 'new-market',
                'ticker': 'NEW-001',
                'question': 'New opportunity?',
                'price': 0.975,
                'outcome': 'YES',
                'url': 'https://test.com',
                'source': 'polymarket',
                'volume': 10000,
                'liquidity': 5000
            }
        ]

        bot.find_opportunities = Mock(return_value=opportunities)
        bot.db.get_open_trades = Mock(return_value=[])
        bot.db.record_trade = Mock(return_value=1)
        bot.update_positions = Mock()

        bot.scan_markets()

        bot.db.record_trade.assert_called_once()
        bot.update_positions.assert_called_once()

    def test_display_stats(self, bot, capsys):
        """Test displaying statistics."""
        mock_stats = {
            'total_trades': 10,
            'wins': 8,
            'losses': 2,
            'win_rate': 80.0,
            'total_pnl': 15.50,
            'total_fees': 0.31,
            'avg_profit': 1.55
        }

        bot.db.get_trade_stats = Mock(return_value=mock_stats)

        bot.display_stats()

        captured = capsys.readouterr()
        assert "PERFORMANCE STATISTICS" in captured.out
        assert "80.0%" in captured.out
        assert "$15.50" in captured.out

    def test_display_open_positions(self, bot, capsys):
        """Test displaying open positions."""
        mock_positions = [
            {
                'id': 1,
                'question': 'Test question 1?',
                'entry_price': 0.975,
                'current_price': 0.98,
                'unrealized_pnl': 0.50
            },
            {
                'id': 2,
                'question': 'Test question 2?',
                'entry_price': 0.97,
                'current_price': 0.96,
                'unrealized_pnl': -1.00
            }
        ]

        bot.db.get_open_trades = Mock(return_value=mock_positions)

        bot.display_open_positions(mock_positions)

        captured = capsys.readouterr()
        assert "Open Positions" in captured.out
        assert "Test question 1" in captured.out

    def test_polymarket_only_mode(self, temp_db_path):
        """Test bot with only Polymarket enabled."""
        with patch('bot.Database'):
            bot = PaperTradingBot(
                enable_poly=True,
                enable_kalshi=False,
                polymarket_demo=True
            )

            assert bot.polymarket_client is not None
            assert bot.kalshi_client is None

    def test_kalshi_only_mode(self, temp_db_path):
        """Test bot with only Kalshi enabled."""
        with patch('bot.Database'):
            bot = PaperTradingBot(
                enable_poly=False,
                enable_kalshi=True,
                kalshi_demo=True
            )

            assert bot.polymarket_client is None
            assert bot.kalshi_client is not None

    def test_no_markets_enabled_raises_error(self, temp_db_path):
        """Test that disabling both markets raises an error."""
        with patch('bot.Database'):
            with pytest.raises(ValueError):
                PaperTradingBot(
                    enable_poly=False,
                    enable_kalshi=False
                )
