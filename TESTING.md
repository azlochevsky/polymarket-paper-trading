# Testing Documentation

## Current Status

- **Total Tests**: 70 tests created
- **Passing Tests**: 58
- **Current Coverage**: 52%
- **Target Coverage**: 90%+

## Test Suite Structure

### Completed Tests

1. **test_config.py** ✅
   - All configuration validation tests passing
   - 100% coverage of config module

2. **test_polymarket_client.py** ✅
   - Tests for market fetching, price updates, opportunity finding
   - Mocked API responses using `responses` library
   - 91% coverage of polymarket_client.py

3. **test_demo_data.py** ✅
   - Tests for both Polymarket and Kalshi demo data
   - 96% coverage of demo_data.py
   - 91% coverage of kalshi_demo_data.py

### Tests Needing Fixes

4. **test_database.py** ⚠️
   - Test structure created but needs adjustment for actual Database class API
   - Issue: Database class uses different method names than expected
   - Need to check actual database.py implementation

5. **test_kalshi_client.py** ⚠️
   - Most tests passing, some failures with authentication mocking
   - 63% coverage of kalshi_client.py
   - Minor fixes needed for attribute names

6. **test_bot.py** ⚠️
   - Test structure created but method names don't match
   - Bot has: `run_scan()`, `update_open_positions()`, `display_opportunities()`
   - Tests expected: `scan_markets()`, `update_positions()`, `find_opportunities()`
   - Needs refactoring to match actual bot implementation

## Next Steps to Reach 90% Coverage

1. Fix test_database.py to match actual Database class methods
2. Fix test_bot.py to test actual bot methods (run_scan, update_open_positions, etc.)
3. Fix minor issues in test_kalshi_client.py
4. Add integration tests for end-to-end workflows
5. Add tests for edge cases and error handling

## Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make coverage

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage threshold check
./run_tests.sh
```

## Test Dependencies

Install with:
```bash
pip3 install -r requirements-dev.txt
```

Dependencies:
- pytest>=8.0.0
- pytest-cov>=4.1.0
- pytest-mock>=3.12.0
- responses>=0.24.0 (for mocking HTTP requests)
- freezegun>=1.4.0 (for time-based tests)
