# D&D Character Scraper - Testing Commands
# Usage: make test, make test-quick, etc.

.PHONY: help test test-quick test-unit test-integration test-calculator test-spell test-edge test-coverage test-coverage-html test-setup test-list

# Default target
help:
	@echo "Available testing commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-quick        - Run quick smoke tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-calculator   - Run calculator tests only"
	@echo "  make test-spell        - Run spell-related tests"
	@echo "  make test-edge         - Run edge case tests"
	@echo "  make test-coverage     - Run tests with coverage"
	@echo "  make test-coverage-html - Generate HTML coverage report"
	@echo "  make test-setup        - Check test environment setup"
	@echo "  make test-list         - List all available test commands"

# Test commands
test:
	python test.py

test-quick:
	python test.py --quick

test-unit:
	python test.py --unit

test-integration:
	python test.py --integration

test-calculator:
	python test.py --calculator

test-spell:
	python test.py --spell

test-edge:
	python test.py --edge

test-coverage:
	python test.py --coverage

test-coverage-html:
	python test.py --coverage-html

test-setup:
	python test.py --setup-check

test-list:
	python test.py --list

# Development helpers
install-dev:
	pip install -r requirements-dev.txt

lint:
	flake8 src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/

# Clean up
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf test_results.json