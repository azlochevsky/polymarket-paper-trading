#!/usr/bin/env python3
"""Polymarket Paper Trading Bot - Trade 97-98c contracts."""

import time
import sys
from datetime import datetime
from typing import List, Dict
import argparse

import config
from database import Database
from polymarket_client import PolymarketClient
from kalshi_client import KalshiClient


class PaperTradingBot:
    def __init__(self, demo_mode: bool = False, polymarket_demo: bool = False, kalshi_demo: bool = False,
                 enable_poly: bool = True, enable_kalshi: bool = True):
        self.db = Database(config.DB_PATH)

        # Initialize clients based on config and command-line overrides
        self.polymarket_client = PolymarketClient(demo_mode=polymarket_demo) if enable_poly else None
        self.kalshi_client = KalshiClient(demo_mode=kalshi_demo) if enable_kalshi else None

        self.running = False
        self.demo_mode = demo_mode or polymarket_demo or kalshi_demo

    def print_banner(self):
        """Print bot banner."""
        print("\n" + "="*60)
        print("  MULTI-MARKET PAPER TRADING BOT")
        print("  Target: 97-98c contracts")

        markets = []
        if self.polymarket_client:
            markets.append("Polymarket")
        if self.kalshi_client:
            markets.append("Kalshi")

        print(f"  Markets: {', '.join(markets)}")

        if self.demo_mode:
            print("  MODE: DEMO (Simulated Data)")
        print("="*60 + "\n")

    def display_opportunities(self, opportunities: List[Dict]):
        """Display found opportunities."""
        if not opportunities:
            print("No opportunities found in price range.")
            return

        print(f"\n📊 Found {len(opportunities)} opportunities:\n")
        print(f"{'#':<4} {'Question':<45} {'Price':<8} {'Volume':<12} {'Market':<12} {'Category':<12}")
        print("-" * 100)

        for i, opp in enumerate(opportunities[:20], 1):  # Show top 20
            question = opp['question'][:42] + "..." if len(opp['question']) > 45 else opp['question']
            price = f"${opp['price']:.3f}"
            volume = f"${opp['volume']:,.0f}"
            market = opp.get('source', 'polymarket')[:12]
            category = opp.get('category', 'N/A')[:12]

            print(f"{i:<4} {question:<45} {price:<8} {volume:<12} {market:<12} {category:<12}")

    def should_enter_trade(self, opp: Dict) -> bool:
        """Determine if we should enter this trade."""
        # Check if we already have a position in this market
        open_trades = self.db.get_open_trades()
        market_id = opp.get('condition_id') or opp.get('market_id')

        for trade in open_trades:
            if trade['market_id'] == market_id:
                return False

        # Check position limits
        if len(open_trades) >= config.MAX_POSITIONS:
            return False

        # Check liquidity
        if opp['liquidity'] < config.MIN_LIQUIDITY:
            return False

        # Check volume
        if opp['volume'] < config.MIN_VOLUME_24H:
            return False

        return True

    def enter_trade(self, opp: Dict):
        """Enter a paper trade."""
        market_id = opp.get('condition_id') or opp.get('market_id')
        market_source = opp.get('source', 'polymarket')

        trade_id = self.db.add_trade(
            market_id=market_id,
            market_question=opp['question'],
            entry_price=opp['price'],
            position_size=config.POSITION_SIZE,
            market_source=market_source
        )

        print(f"\n✅ ENTERED TRADE #{trade_id} [{market_source.upper()}]")
        print(f"   Market: {opp['question']}")
        print(f"   Entry Price: ${opp['price']:.3f}")
        print(f"   Position Size: ${config.POSITION_SIZE}")
        print(f"   Shares: {config.POSITION_SIZE / opp['price']:.2f}")
        print(f"   URL: {opp['url']}\n")

    def update_open_positions(self):
        """Update prices for all open positions."""
        open_trades = self.db.get_open_trades()

        if not open_trades:
            return

        print(f"\n📈 Updating {len(open_trades)} open positions...")

        for trade in open_trades:
            # Determine which client to use based on market source
            market_source = trade.get('market_source', 'polymarket')

            if market_source == 'kalshi' and self.kalshi_client:
                current_price = self.kalshi_client.get_current_price(trade['market_id'])
            elif market_source == 'polymarket' and self.polymarket_client:
                current_price = self.polymarket_client.get_current_price(trade['market_id'])
            else:
                current_price = None

            if current_price:
                self.db.update_trade_price(trade['id'], current_price)

                # Check if price hit 1.00 (market resolved to YES)
                if current_price >= 0.99:
                    self.db.close_trade(
                        trade_id=trade['id'],
                        exit_price=1.0,
                        outcome="WON",
                        notes="Market resolved to YES"
                    )
                    print(f"   ✅ Trade #{trade['id']} WON [{market_source.upper()}] - {trade['market_question'][:50]}")

                # Check if price dropped significantly (likely resolving to NO)
                elif current_price < 0.80:
                    self.db.close_trade(
                        trade_id=trade['id'],
                        exit_price=current_price,
                        outcome="LOST",
                        notes="Price dropped below threshold"
                    )
                    print(f"   ❌ Trade #{trade['id']} LOST [{market_source.upper()}] - {trade['market_question'][:50]}")

    def display_stats(self):
        """Display performance statistics."""
        stats = self.db.get_performance_stats()

        print("\n" + "="*60)
        print("  PERFORMANCE STATISTICS")
        print("="*60)
        print(f"  Total Trades:     {stats['total_trades']}")
        print(f"  Wins:             {stats['wins']}")
        print(f"  Losses:           {stats['losses']}")
        print(f"  Win Rate:         {stats['win_rate']:.1f}%")
        print(f"  Total P&L:        ${stats['total_pnl']:.2f}")
        print(f"  Total Fees Paid:  ${stats['total_fees']:.2f} ({stats['fee_rate']:.1f}% on profits)")
        print(f"  Avg Profit/Trade: ${stats['avg_profit']:.2f}")
        print(f"  ROI:              {stats['roi']:.2f}%")
        print("="*60 + "\n")

    def display_open_positions(self):
        """Display current open positions."""
        open_trades = self.db.get_open_trades()

        if not open_trades:
            print("\n📭 No open positions.\n")
            return

        print(f"\n📊 Open Positions ({len(open_trades)}):\n")
        print(f"{'ID':<5} {'Question':<45} {'Entry':<8} {'Current':<8} {'P&L':<10}")
        print("-" * 80)

        total_pnl = 0
        for trade in open_trades:
            question = trade['market_question'][:42] + "..." if len(trade['market_question']) > 45 else trade['market_question']
            entry = f"${trade['entry_price']:.3f}"
            current = f"${trade.get('current_price', trade['entry_price']):.3f}"

            # Calculate unrealized P&L
            current_price = trade.get('current_price', trade['entry_price'])
            shares = trade['position_size'] / trade['entry_price']
            unrealized_pnl = shares * (current_price - trade['entry_price'])
            total_pnl += unrealized_pnl

            pnl_str = f"${unrealized_pnl:+.2f}"

            print(f"{trade['id']:<5} {question:<45} {entry:<8} {current:<8} {pnl_str:<10}")

        print("-" * 80)
        print(f"{'Total Unrealized P&L:':<66} ${total_pnl:+.2f}\n")

    def run_scan(self):
        """Run a single scan for opportunities."""
        print(f"\n🔍 Scanning markets... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

        opportunities = []

        # Scan Polymarket
        if self.polymarket_client:
            poly_opps = self.polymarket_client.find_opportunities(
                min_price=config.MIN_PRICE,
                max_price=config.MAX_PRICE
            )
            # Add source if not present
            for opp in poly_opps:
                if 'source' not in opp:
                    opp['source'] = 'polymarket'
                # Normalize ID field
                if 'condition_id' in opp and 'market_id' not in opp:
                    opp['market_id'] = opp['condition_id']
            opportunities.extend(poly_opps)

        # Scan Kalshi
        if self.kalshi_client:
            kalshi_opps = self.kalshi_client.find_opportunities(
                min_price=config.MIN_PRICE,
                max_price=config.MAX_PRICE
            )
            opportunities.extend(kalshi_opps)

        # Sort by price (highest first)
        opportunities.sort(key=lambda x: x['price'], reverse=True)

        self.display_opportunities(opportunities)

        # Auto-enter trades for qualifying opportunities
        entered_count = 0
        for opp in opportunities:
            if self.should_enter_trade(opp):
                self.enter_trade(opp)
                entered_count += 1

        if entered_count == 0 and opportunities:
            print("\n⚠️  No new trades entered (position limits or filters applied)")

        # Update existing positions
        self.update_open_positions()

        # Show current state
        self.display_open_positions()
        self.display_stats()

    def run_continuous(self):
        """Run continuous monitoring."""
        self.running = True
        self.print_banner()

        print(f"⚙️  Configuration:")
        print(f"   Price Range: ${config.MIN_PRICE} - ${config.MAX_PRICE}")
        print(f"   Position Size: ${config.POSITION_SIZE}")
        print(f"   Max Positions: {config.MAX_POSITIONS}")
        print(f"   Refresh Interval: {config.REFRESH_INTERVAL}s\n")
        print("Press Ctrl+C to stop...\n")

        try:
            while self.running:
                self.run_scan()
                print(f"\n⏳ Next scan in {config.REFRESH_INTERVAL} seconds...")
                time.sleep(config.REFRESH_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n👋 Stopping bot...")
            self.running = False


def main():
    parser = argparse.ArgumentParser(description="Multi-Market Paper Trading Bot")
    parser.add_argument("--scan", action="store_true", help="Run a single scan")
    parser.add_argument("--stats", action="store_true", help="Show performance statistics")
    parser.add_argument("--positions", action="store_true", help="Show open positions")
    parser.add_argument("--run", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--demo-poly", action="store_true", help="Use demo mode for Polymarket")
    parser.add_argument("--demo-kalshi", action="store_true", help="Use demo mode for Kalshi")
    parser.add_argument("--no-poly", action="store_true", help="Disable Polymarket scanning")
    parser.add_argument("--no-kalshi", action="store_true", help="Disable Kalshi scanning")

    args = parser.parse_args()

    # Determine which markets to enable (default: both enabled)
    enable_poly = not args.no_poly
    enable_kalshi = not args.no_kalshi

    # Determine demo modes
    poly_demo = args.demo_poly
    kalshi_demo = args.demo_kalshi
    any_demo = poly_demo or kalshi_demo

    bot = PaperTradingBot(
        demo_mode=any_demo,
        polymarket_demo=poly_demo,
        kalshi_demo=kalshi_demo,
        enable_poly=enable_poly,
        enable_kalshi=enable_kalshi
    )

    if args.stats:
        bot.print_banner()
        bot.display_stats()
    elif args.positions:
        bot.print_banner()
        bot.display_open_positions()
    elif args.scan:
        bot.print_banner()
        bot.run_scan()
    elif args.run:
        bot.run_continuous()
    else:
        # Default: run single scan
        bot.print_banner()
        bot.run_scan()


if __name__ == "__main__":
    main()
