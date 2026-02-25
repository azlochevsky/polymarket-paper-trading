"""Database handler for paper trading records."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import config


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                market_question TEXT NOT NULL,
                market_source TEXT NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                position_size REAL NOT NULL,
                current_price REAL,
                status TEXT NOT NULL,
                exit_time TIMESTAMP,
                exit_price REAL,
                profit_loss REAL,
                fee_paid REAL DEFAULT 0,
                outcome TEXT,
                outcome_bet TEXT,
                notes TEXT
            )
        """)

        # Add outcome_bet column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN outcome_bet TEXT")
            conn.commit()
        except:
            pass  # Column already exists

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                price REAL NOT NULL,
                liquidity REAL,
                volume_24h REAL
            )
        """)

        conn.commit()
        conn.close()

    def add_trade(self, market_id: str, market_question: str, entry_price: float,
                  position_size: float, market_source: str = "polymarket", outcome_bet: str = "YES") -> int:
        """Add a new paper trade."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trades (market_id, market_question, market_source, entry_time, entry_price,
                              position_size, current_price, status, outcome_bet)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (market_id, market_question, market_source, datetime.now(), entry_price,
              position_size, entry_price, outcome_bet))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trade_id

    def update_trade_price(self, trade_id: int, current_price: float):
        """Update current price of an open trade."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE trades
            SET current_price = ?
            WHERE id = ? AND status = 'OPEN'
        """, (current_price, trade_id))

        conn.commit()
        conn.close()

    def close_trade(self, trade_id: int, exit_price: float, outcome: str, notes: str = ""):
        """Close a trade and record outcome."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get trade details
        cursor.execute("""
            SELECT entry_price, position_size FROM trades WHERE id = ?
        """, (trade_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return

        entry_price, position_size = result

        # Calculate P&L
        if outcome == "WON":
            # Calculate shares bought and profit
            shares = position_size / entry_price
            gross_profit = shares * (exit_price - entry_price)
            # Apply fee on profits only (configurable fee from config.py)
            fee = max(0, gross_profit * config.POLYMARKET_FEE)
            profit_loss = gross_profit - fee
        else:
            # Lost the position
            profit_loss = -position_size
            fee = 0

        cursor.execute("""
            UPDATE trades
            SET status = 'CLOSED',
                exit_time = ?,
                exit_price = ?,
                profit_loss = ?,
                fee_paid = ?,
                outcome = ?,
                notes = ?
            WHERE id = ?
        """, (datetime.now(), exit_price, profit_loss, fee, outcome, notes, trade_id))

        conn.commit()
        conn.close()

    def get_open_trades(self) -> List[Dict]:
        """Get all open trades."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, market_id, market_question, market_source, entry_time, entry_price,
                   position_size, current_price, outcome_bet
            FROM trades
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC
        """)

        columns = [description[0] for description in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return trades

    def get_performance_stats(self) -> Dict:
        """Calculate performance statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
        total_trades = cursor.fetchone()[0]

        if total_trades == 0:
            conn.close()
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "total_fees": 0,
                "avg_profit": 0,
                "roi": 0,
                "fee_rate": config.POLYMARKET_FEE * 100
            }

        # Wins and losses
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED' AND outcome = 'WON'")
        wins = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED' AND outcome = 'LOST'")
        losses = cursor.fetchone()[0]

        # P&L
        cursor.execute("SELECT SUM(profit_loss) FROM trades WHERE status = 'CLOSED'")
        total_pnl = cursor.fetchone()[0] or 0

        # Total fees paid
        cursor.execute("SELECT SUM(fee_paid) FROM trades WHERE status = 'CLOSED'")
        total_fees = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(position_size) FROM trades WHERE status = 'CLOSED'")
        total_invested = cursor.fetchone()[0] or 1

        conn.close()

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "total_fees": total_fees,
            "avg_profit": total_pnl / total_trades if total_trades > 0 else 0,
            "roi": (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            "fee_rate": config.POLYMARKET_FEE * 100
        }

    def get_all_closed_trades(self) -> List[Dict]:
        """Get all closed trades for analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM trades
            WHERE status = 'CLOSED'
            ORDER BY exit_time DESC
        """)

        columns = [description[0] for description in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return trades
