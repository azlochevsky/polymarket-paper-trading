"""Unit tests for config module."""

import pytest
import config


class TestConfig:
    """Test cases for configuration values."""

    def test_price_range_valid(self):
        """Test that price range is valid."""
        assert 0 < config.MIN_PRICE < 1
        assert 0 < config.MAX_PRICE <= 1
        assert config.MIN_PRICE < config.MAX_PRICE

    def test_fee_valid(self):
        """Test that fee is valid."""
        assert 0 <= config.POLYMARKET_FEE <= 1
        assert isinstance(config.POLYMARKET_FEE, float)

    def test_position_size_positive(self):
        """Test that position size is positive."""
        assert config.POSITION_SIZE > 0

    def test_max_positions_positive(self):
        """Test that max positions is positive."""
        assert config.MAX_POSITIONS > 0

    def test_liquidity_filters_positive(self):
        """Test that liquidity filters are positive."""
        assert config.MIN_LIQUIDITY >= 0
        assert config.MIN_VOLUME_24H >= 0

    def test_api_urls_valid(self):
        """Test that API URLs are valid."""
        assert config.POLYMARKET_API_URL.startswith('https://')
        assert config.GAMMA_API_URL.startswith('https://')
        assert config.KALSHI_API_URL.startswith('https://')

    def test_market_flags(self):
        """Test market enable flags are boolean."""
        assert isinstance(config.ENABLE_POLYMARKET, bool)
        assert isinstance(config.ENABLE_KALSHI, bool)

    def test_refresh_interval_positive(self):
        """Test that refresh interval is positive."""
        assert config.REFRESH_INTERVAL > 0

    def test_db_path_exists(self):
        """Test that database path is defined."""
        assert config.DB_PATH is not None
        assert isinstance(config.DB_PATH, str)
        assert len(config.DB_PATH) > 0
