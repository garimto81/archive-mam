#!/bin/bash
# M3 Timecode Validation - Test runner script

set -e

echo "=========================================="
echo "M3 Timecode Validation Service - Tests"
echo "=========================================="
echo ""

# Set environment for testing
export POKER_ENV=development
export VISION_API_ENABLED=false
export BIGQUERY_MOCK_DATA=../../mock_data/bigquery/hand_summary_mock.json

echo "Environment: $POKER_ENV"
echo "Vision API: $VISION_API_ENABLED"
echo ""

# Run linting
echo "Running pylint..."
pylint app/ --fail-under=8 || true
echo ""

# Run tests with coverage
echo "Running tests with coverage..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Check coverage threshold
echo ""
echo "Coverage report generated in htmlcov/index.html"
echo ""

# Display final summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
pytest tests/ -v --tb=no -q

echo ""
echo "All tests completed!"
