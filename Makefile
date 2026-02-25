.PHONY: test coverage install-dev clean run help

help:
	@echo "Available commands:"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make coverage     - Run tests with coverage report"
	@echo "  make clean        - Remove test artifacts and cache"
	@echo "  make run          - Run the bot in demo mode"

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

coverage:
	./run_tests.sh

clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -f .coverage
	rm -f coverage.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run:
	python3 bot.py --demo-poly --demo-kalshi --scan
