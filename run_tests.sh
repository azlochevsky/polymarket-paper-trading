#!/bin/bash
# Script to run tests with coverage reporting

set -e

echo "=========================================="
echo "  Running Unit Tests with Coverage"
echo "=========================================="
echo ""

# Install test dependencies if not already installed
echo "Installing test dependencies..."
pip install -q -r requirements-dev.txt

echo ""
echo "Running pytest with coverage..."
echo ""

# Run pytest with coverage
pytest tests/ \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=json \
    -v

echo ""
echo "=========================================="
echo "  Coverage Report Generated"
echo "=========================================="
echo ""
echo "HTML report: htmlcov/index.html"
echo "JSON report: coverage.json"
echo ""

# Check coverage threshold
coverage_percent=$(python3 -c "import json; data=json.load(open('coverage.json')); print(data['totals']['percent_covered'])")

echo "Total coverage: ${coverage_percent}%"
echo ""

# Set threshold to 90%
threshold=90

if (( $(echo "$coverage_percent >= $threshold" | bc -l) )); then
    echo "✅ Coverage threshold met! (>= ${threshold}%)"
    exit 0
else
    echo "❌ Coverage below threshold! (< ${threshold}%)"
    echo "   Current: ${coverage_percent}%"
    echo "   Required: ${threshold}%"
    exit 1
fi
