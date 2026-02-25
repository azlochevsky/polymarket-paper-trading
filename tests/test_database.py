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
    db.conn.close()
    os.unlink(path)


class TestDatabase:
    """Test cases for Database class."""

    def test_init_creates_tables(self, temp_db):
        """Test that database initialization creates required tables."""
        cursor = temp_db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trades'"
        )
        assert cursor.fetchone() is not None

    def test_record_trade(self, temp_db):
        """Test recording a new trade."""
        trade_id = temp_db.record_trade(
            condition_id="test_123",
            market_slug="test-market",
            question="Will this test pass?",
            outcome="YES",
            entry_price=0.97,
            position_size=100,
            url="https://test.com",
            market_source="polymarket"
        )

        assert trade_id > 0

        # Verify trade was recorded
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()

        assert trade is not None
        assert trade[1] == "test_123"  # condition_id
        assert trade[2] == "test-market"  # market_slug
        assert trade[4] == "YES"  # outcome
        assert trade[5] == 0.97  # entry_price
        assert trade[6] == 100  # position_size
        assert trade[11] == "polymarket"  # market_source

    def test_close_trade_won(self, temp_db):
        """Test closing a winning trade."""
        # Create a trade
        trade_id = temp_db.record_trade(
            condition_id="test_win",
            market_slug="test-market",
            question="Will this win?",
            outcome="YES",
            entry_price=0.98,
            position_size=100,
            url="https://test.com",
            market_source="polymarket"
        )

        # Close as won
        temp_db.close_trade(trade_id, exit_price=1.0, outcome="WON", notes="Market resolved YES")

        # Verify closure
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()

        assert trade[8] == "WON"  # outcome
        assert trade[7] == 1.0  # exit_price

        # Calculate expected P&L
        shares = 100 / 0.98  # 102.04 shares
        gross_profit = shares * (1.0 - 0.98)  # ~2.04
        fee = gross_profit * config.POLYMARKET_FEE
        expected_pl = gross_profit - fee

        assert abs(float(trade[9]) - expected_pl) < 0.01  # profit_loss
        assert float(trade[10]) == fee  # fee_paid

    def test_close_trade_lost(self, temp_db):
        """Test closing a losing trade."""
        trade_id = temp_db.record_trade(
            condition_id="test_loss",
            market_slug="test-market",
            question="Will this lose?",
            outcome="YES",
            entry_price=0.97,
            position_size=100,
            url="https://test.com",
            market_source="kalshi"
        )

        # Close as lost
        temp_db.close_trade(trade_id, exit_price=0.0, outcome="LOST", notes="Market resolved NO")

        # Verify closure
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()

        assert trade[8] == "LOST"
        assert float(trade[9]) == -100.0  # Lost full position
        assert float(trade[10]) == 0.0  # No fee on losses

    def test_get_open_trades(self, temp_db):
        """Test retrieving open trades."""
        # Create some trades
        temp_db.record_trade(
            condition_id="open_1",
            market_slug="market-1",
            question="Open 1",
            outcome="YES",
            entry_price=0.97,
            position_size=100,
            url="https://test.com",
            market_source="polymarket"
        )

        trade_id_2 = temp_db.record_trade(
            condition_id="open_2",
            market_slug="market-2",
            question="Open 2",
            outcome="NO",
            entry_price=0.98,
            position_size=100,
            url="https://test.com",
            market_source="kalshi"
        )

        # Close one trade
        temp_db.close_trade(trade_id_2, exit_price=1.0, outcome="WON")

        # Get open trades
        open_trades = temp_db.get_open_trades()

        assert len(open_trades) == 1
        assert open_trades[0]['condition_id'] == "open_1"

    def test_get_trade_stats(self, temp_db):
        """Test retrieving trade statistics."""
        # Create and close some trades
        for i in range(5):
            trade_id = temp_db.record_trade(
                condition_id=f"trade_{i}",
                market_slug=f"market-{i}",
                question=f"Question {i}",
                outcome="YES",
                entry_price=0.97,
                position_size=100,
                url="https://test.com",
                market_source="polymarket"
            )

            # Win 4 out of 5
            if i < 4:
                temp_db.close_trade(trade_id, exit_price=1.0, outcome="WON")
            else:
                temp_db.close_trade(trade_id, exit_price=0.0, outcome="LOST")

        stats = temp_db.get_trade_stats()

        assert stats['total_trades'] == 5
        assert stats['wins'] == 4
        assert stats['losses'] == 1
        assert stats['win_rate'] == 80.0
        assert stats['total_pnl'] > 0  # Should be positive overall
        assert stats['total_fees'] > 0  # Fees from winning trades

    def test_get_trade_stats_no_trades(self, temp_db):
        """Test stats with no trades."""
        stats = temp_db.get_trade_stats()

        assert stats['total_trades'] == 0
        assert stats['wins'] == 0
        assert stats['losses'] == 0
        assert stats['win_rate'] == 0.0
        assert stats['total_pnl'] == 0.0
        assert stats['total_fees'] == 0.0

    def test_update_position(self, temp_db):
        """Test updating position price."""
        trade_id = temp_db.record_trade(
            condition_id="update_test",
            market_slug="test-market",
            question="Update test",
            outcome="YES",
            entry_price=0.97,
            position_size=100,
            url="https://test.com",
            market_source="polymarket"
        )

        # Update position
        temp_db.update_position(trade_id, current_price=0.98)

        # Verify update (check the database directly)
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()

        # The current price affects unrealized P&L calculation
        # Verify trade is still open
        assert trade[8] == "OPEN"

    def test_market_source_tracking(self, temp_db):
        """Test that market source is properly tracked."""
        # Create trades from different sources
        poly_id = temp_db.record_trade(
            condition_id="poly_1",
            market_slug="poly-market",
            question="Polymarket trade",
            outcome="YES",
            entry_price=0.97,
            position_size=100,
            url="https://polymarket.com",
            market_source="polymarket"
        )

        kalshi_id = temp_db.record_trade(
            condition_id="kalshi_1",
            market_slug="kalshi-market",
            question="Kalshi trade",
            outcome="NO",
            entry_price=0.98,
            position_size=100,
            url="https://kalshi.com",
            market_source="kalshi"
        )

        # Verify sources
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT market_source FROM trades WHERE id = ?", (poly_id,))
        assert cursor.fetchone()[0] == "polymarket"

        cursor.execute("SELECT market_source FROM trades WHERE id = ?", (kalshi_id,))
        assert cursor.fetchone()[0] == "kalshi"

    def test_fee_calculation_zero_profit(self, temp_db):
        """Test that no fee is charged on zero or negative profit."""
        trade_id = temp_db.record_trade(
            condition_id="no_profit",
            market_slug="test-market",
            question="No profit trade",
            outcome="YES",
            entry_price=0.99,
            position_size=100,
            url="https://test.com",
            market_source="polymarket"
        )

        # Close at same price (no profit)
        temp_db.close_trade(trade_id, exit_price=0.99, outcome="WON")

        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT fee_paid FROM trades WHERE id = ?", (trade_id,))
        fee = cursor.fetchone()[0]

        assert float(fee) == 0.0
