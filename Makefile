# Makefile for zarrcompatibility v3.0 testing
# 
# This Makefile provides convenient commands for running different test suites.
# 
# Usage:
#   make test          # Run all tests
#   make test-quick    # Run only fast tests
#   make test-iso      # Run only isolation tests
#   make test-func     # Run only functionality tests
#   make test-int      # Run only integration tests
#   make test-ci       # Run tests in CI mode
#   make clean         # Clean test artifacts

.PHONY: help test test-quick test-isolation test-functionality test-integration test-ci clean setup check-env

# Default target
help:
	@echo "zarrcompatibility v3.0 - Test Commands"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@echo "  test            Run all tests"
	@echo "  test-quick      Run only fast tests (no integration)"
	@echo "  test-isolation  Run only isolation tests"
	@echo "  test-func       Run only functionality tests"
	@echo "  test-int        Run only integration tests"
	@echo "  test-ci         Run tests in CI mode (minimal output)"
	@echo "  clean           Clean test artifacts"
	@echo "  setup           Install test dependencies"
	@echo "  check-env       Check test environment"
	@echo ""
	@echo "Examples:"
	@echo "  make test                    # Run all tests"
	@echo "  make test-quick              # Skip slow integration tests"
	@echo "  make test ARGS='-v -s'       # Run with extra pytest args"
	@echo "  make test-ci                 # CI mode with JUnit output"

# Check environment
check-env:
	@echo "Checking test environment..."
	@python -c "import sys; print('Python:', sys.version.split()[0])"
	@python -c "import pathlib; print('Working dir:', pathlib.Path.cwd())"
	@python -c "import sys; sys.path.insert(0, 'src'); exec('try:\n import zarrcompatibility as zc\n print(\"OK zarrcompatibility v\" + zc.__version__)\nexcept Exception as e:\n print(\"ERROR zarrcompatibility:\", e)')"
	@python -c "exec('try:\n import zarr\n print(\"OK Zarr v\" + zarr.__version__)\nexcept Exception as e:\n print(\"ERROR Zarr:\", e)')"
	@python -c "exec('try:\n import numpy as np\n print(\"OK NumPy v\" + np.__version__)\nexcept Exception as e:\n print(\"ERROR NumPy:\", e)')"
	@python -c "exec('try:\n import pytest\n print(\"OK pytest v\" + pytest.__version__)\nexcept Exception as e:\n print(\"ERROR pytest:\", e)')"

# Setup test dependencies
setup:
	@echo "📦 Installing test dependencies..."
	@pip install pytest>=6.0
	@pip install numpy
	@pip install zarr>=3.0.0
	@echo "✅ Test dependencies installed"

# Run all tests
test: check-env
	@echo "🧪 Running all zarrcompatibility tests..."
	@pytest $(ARGS)

# Run only fast tests (exclude slow integration tests)
test-quick: check-env
	@echo "⚡ Running quick tests (excluding slow integration tests)..."
	@pytest -m "not slow" $(ARGS)

# Run only isolation tests
test-isolation: check-env
	@echo "🔒 Running isolation tests..."
	@pytest -m "isolation" $(ARGS)

# Run only functionality tests
test-functionality: check-env
	@echo "⚙️ Running functionality tests..."
	@pytest -m "functionality" $(ARGS)

# Run only integration tests
test-integration: check-env
	@echo "🔗 Running integration tests..."
	@pytest -m "integration" $(ARGS)

# Run tests in CI mode
test-ci: check-env
	@echo "🤖 Running tests in CI mode..."
	@pytest \
		--tb=short \
		--quiet \
		--disable-warnings \
		--junit-xml=tests/testresults/junit.xml \
		--junit-prefix=zarrcompatibility_v3 \
		$(ARGS)

# Clean test artifacts
clean:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf tests/testresults/*
	@rm -rf tests/__pycache__
	@rm -rf tests/.pytest_cache
	@rm -rf .pytest_cache
	@rm -rf __pycache__
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name "*~" -delete
	@echo "✅ Test artifacts cleaned"

# Development shortcuts
dev-test: test-quick
dev-full: clean test
dev-iso: test-isolation

# CI shortcuts  
ci: test-ci
ci-quick: test-ci ARGS="-m 'not slow'"

# Performance testing (if needed)
test-perf: check-env
	@echo "📈 Running performance tests..."
	@pytest -m "performance" --durations=0 $(ARGS)

# Coverage testing (if pytest-cov is available)
test-cov: check-env
	@echo "📊 Running tests with coverage..."
	@pytest --cov=zarrcompatibility --cov-report=html --cov-report=term-missing $(ARGS)

# Debug mode (verbose output, no capture)
test-debug: check-env
	@echo "🐛 Running tests in debug mode..."
	@pytest -v -s --tb=long $(ARGS)

# Test specific file
test-file: check-env
	@echo "📄 Running specific test file: $(FILE)"
	@pytest $(FILE) $(ARGS)

# Examples of usage
examples:
	@echo "📚 Test command examples:"
	@echo ""
	@echo "# Run all tests:"
	@echo "make test"
	@echo ""
	@echo "# Run only fast tests:"
	@echo "make test-quick"
	@echo ""
	@echo "# Run specific test category:"
	@echo "make test-isolation"
	@echo "make test-functionality"
	@echo "make test-integration"
	@echo ""
	@echo "# Run with custom pytest args:"
	@echo "make test ARGS='-v -s'"
	@echo "make test-quick ARGS='--tb=line'"
	@echo ""
	@echo "# CI mode:"
	@echo "make test-ci"
	@echo ""
	@echo "# Debug mode:"
	@echo "make test-debug"
	@echo ""
	@echo "# Test specific file:"
	@echo "make test-file FILE=tests/test_functionality.py"
	@echo ""
	@echo "# Coverage:"
	@echo "make test-cov"

# Help text for each target
help-test:
	@echo "test: Run all zarrcompatibility tests using pytest"

help-test-quick:
	@echo "test-quick: Run only fast tests, skipping slow integration tests"

help-clean:
	@echo "clean: Remove all test artifacts and cache files"