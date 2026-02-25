"""Unit tests for database module."""

import pytest
import os
import tempfile
from datetime import datetime
from database import Database
import config


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    yield db
    if os.path.exists(path):
        os.unlink(path)


class TestDatabase:
    """Test cases for Database class."""

    def test_init_creates_database(self, temp_db):
        """Test that database initialization creates the file."""
        assert os.path.exists(temp_db.db_path)

    def test_add_trade(self, temp_db):
        """Test adding a new trade."""
        trade_id = temp_db.add_trade(
            market_id="test_123",
            market_question="Will this test pass?",
            entry_price=0.97,
            position_size=100,
            market_source="polymarket"
        )

        assert trade_id > 0

        # Verify trade was added
        trades = temp_db.get_open_trades()
        assert len(trades) == 1
        assert trades[0]['market_id'] == "test_123"
        assert trades[0]['entry_price'] == 0.97
        assert trades[0]['position_size'] == 100
        assert trades[0]['market_source'] == "polymarket"

    def test_close_trade_won(self, temp_db):
        """Test closing a winning trade."""
        trade_id = temp_db.add_trade(
            market_id="win_test",
            market_question="Will this win?",
            entry_price=0.98,
            position_size=100,
            market_source="polymarket"
        )

        # Close as won
        temp_db.close_trade(trade_id, exit_price=1.0, outcome="WON", notes="Market resolved")

        # Verify closure
        open_trades = temp_db.get_open_trades()
        assert len(open_trades) == 0

        closed_trades = temp_db.get_all_closed_trades()
        assert len(closed_trades) == 1
        assert closed_trades[0]['outcome'] == "WON"
        assert closed_trades[0]['exit_price'] == 1.0

        # Calculate expected P&L
        shares = 100 / 0.98  # ~102.04 shares
        gross_profit = shares * (1.0 - 0.98)  # ~2.04
        fee = gross_profit * config.POLYMARKET_FEE
        expected_pl = gross_profit - fee

        assert abs(closed_trades[0]['profit_loss'] - expected_pl) < 0.01
        assert abs(closed_trades[0]['fee_paid'] - fee) < 0.01

    def test_close_trade_lost(self, temp_db):
        """Test closing a losing trade."""
        trade_id = temp_db.add_trade(
            market_id="loss_test",
            market_question="Will this lose?",
            entry_price=0.97,
            position_size=100,
            market_source="kalshi"
        )

        # Close as lost
        temp_db.close_trade(trade_id, exit_price=0.0, outcome="LOST", notes="Market resolved NO")

        closed_trades = temp_db.get_all_closed_trades()
        assert len(closed_trades) == 1
        assert closed_trades[0]['outcome'] == "LOST"
        assert closed_trades[0]['profit_loss'] == -100.0  # Lost full position
        assert closed_trades[0]['fee_paid'] == 0.0  # No fee on losses

    def test_get_open_trades(self, temp_db):
        """Test retrieving open trades."""
        # Add multiple trades
        temp_db.add_trade("open_1", "Open 1", 0.97, 100, "polymarket")
        trade_id_2 = temp_db.add_trade("open_2", "Open 2", 0.98, 100, "kalshi")

        # Close one
        temp_db.close_trade(trade_id_2, exit_price=1.0, outcome="WON")

        # Get open trades
        open_trades = temp_db.get_open_trades()
        assert len(open_trades) == 1
        assert open_trades[0]['market_id'] == "open_1"

    def test_get_performance_stats_no_trades(self, temp_db):
        """Test stats with no trades."""
        stats = temp_db.get_performance_stats()

        assert stats['total_trades'] == 0
        assert stats['wins'] == 0
        assert stats['losses'] == 0
        assert stats['win_rate'] == 0
        assert stats['total_pnl'] == 0
        assert stats['total_fees'] == 0

    def test_get_performance_stats_with_trades(self, temp_db):
        """Test performance statistics calculation."""
        # Create and close some trades
        for i in range(5):
            trade_id = temp_db.add_trade(
                market_id=f"trade_{i}",
                market_question=f"Question {i}",
                entry_price=0.97,
                position_size=100,
                market_source="polymarket"
            )

            # Win 4 out of 5
            if i < 4:
                temp_db.close_trade(trade_id, exit_price=1.0, outcome="WON")
            else:
                temp_db.close_trade(trade_id, exit_price=0.0, outcome="LOST")

        stats = temp_db.get_performance_stats()

        assert stats['total_trades'] == 5
        assert stats['wins'] == 4
        assert stats['losses'] == 1
        assert stats['win_rate'] == 80.0
        # With 0.97 entry price, 4 wins to 1.0 only profit ~$0.30 each = $1.20
        # 1 loss = -$100, so net is negative
        assert stats['total_pnl'] < 0  # Net is negative with this setup
        assert stats['total_fees'] > 0  # Fees from winning trades
        assert stats['fee_rate'] == config.POLYMARKET_FEE * 100

    def test_update_trade_price(self, temp_db):
        """Test updating current price of open trade."""
        trade_id = temp_db.add_trade(
            market_id="price_update",
            market_question="Update test",
            entry_price=0.97,
            position_size=100,
            market_source="polymarket"
        )

        # Update price
        temp_db.update_trade_price(trade_id, current_price=0.98)

        # Verify update
        trades = temp_db.get_open_trades()
        assert len(trades) == 1
        assert trades[0]['current_price'] == 0.98

    def test_market_source_tracking(self, temp_db):
        """Test that market source is properly tracked."""
        poly_id = temp_db.add_trade(
            market_id="poly_1",
            market_question="Polymarket trade",
            entry_price=0.97,
            position_size=100,
            market_source="polymarket"
        )

        kalshi_id = temp_db.add_trade(
            market_id="kalshi_1",
            market_question="Kalshi trade",
            entry_price=0.98,
            position_size=100,
            market_source="kalshi"
        )

        trades = temp_db.get_open_trades()

        poly_trade = [t for t in trades if t['id'] == poly_id][0]
        kalshi_trade = [t for t in trades if t['id'] == kalshi_id][0]

        assert poly_trade['market_source'] == "polymarket"
        assert kalshi_trade['market_source'] == "kalshi"

    def test_close_trade_invalid_id(self, temp_db):
        """Test closing non-existent trade doesn't crash."""
        temp_db.close_trade(999999, exit_price=1.0, outcome="WON", notes="Should not crash")

        # Should complete without error
        stats = temp_db.get_performance_stats()
        assert stats['total_trades'] == 0

    def test_fee_calculation_zero_profit(self, temp_db):
        """Test that no fee is charged on zero or negative profit."""
        trade_id = temp_db.add_trade(
            market_id="no_profit",
            market_question="No profit trade",
            entry_price=0.99,
            position_size=100,
            market_source="polymarket"
        )

        # Close at same price (no profit)
        temp_db.close_trade(trade_id, exit_price=0.99, outcome="WON")

        closed = temp_db.get_all_closed_trades()
        assert closed[0]['fee_paid'] == 0.0

    def test_multiple_trades_different_prices(self, temp_db):
        """Test handling multiple trades with different entry prices."""
        prices = [0.95, 0.96, 0.97, 0.98, 0.99]

        for i, price in enumerate(prices):
            trade_id = temp_db.add_trade(
                market_id=f"trade_{i}",
                market_question=f"Trade {i}",
                entry_price=price,
                position_size=100,
                market_source="polymarket"
            )

            # Close all as winners
            temp_db.close_trade(trade_id, exit_price=1.0, outcome="WON")

        stats = temp_db.get_performance_stats()
        assert stats['total_trades'] == 5
        assert stats['wins'] == 5
        assert stats['win_rate'] == 100.0

    def test_get_all_closed_trades_empty(self, temp_db):
        """Test getting closed trades when none exist."""
        closed = temp_db.get_all_closed_trades()
        assert closed == []

    def test_get_all_closed_trades_ordering(self, temp_db):
        """Test that closed trades are ordered by exit time (newest first)."""
        # Add and close multiple trades
        trade_ids = []
        for i in range(3):
            trade_id = temp_db.add_trade(
                market_id=f"trade_{i}",
                market_question=f"Trade {i}",
                entry_price=0.97,
                position_size=100,
                market_source="polymarket"
            )
            trade_ids.append(trade_id)

        # Close in order
        for trade_id in trade_ids:
            temp_db.close_trade(trade_id, exit_price=1.0, outcome="WON")

        closed = temp_db.get_all_closed_trades()

        # Should be ordered by exit_time DESC (newest first)
        assert len(closed) == 3
        # The last closed trade should be first in the list
        assert closed[0]['id'] == trade_ids[-1]
