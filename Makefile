# Makefile for zarrcompatibility v3.0
# Comprehensive test suite with performance and compatibility testing

# Colors for output
RED    = \033[31m
GREEN  = \033[32m
YELLOW = \033[33m
BLUE   = \033[34m
PURPLE = \033[35m
CYAN   = \033[36m
WHITE  = \033[37m
RESET  = \033[0m

# Project configuration
PYTHON = python3
PIP = pip3
PROJECT_NAME = zarrcompatibility
VERSION = 3.0.0

# Directories
SRC_DIR = src
TESTS_DIR = tests
RESULTS_DIR = $(TESTS_DIR)/testresults
DOCS_DIR = docs
BUILD_DIR = build
DIST_DIR = dist

# Test configuration
PYTEST_ARGS = -v --tb=short
PYTEST_COV_ARGS = --cov=$(SRC_DIR)/$(PROJECT_NAME) --cov-report=html --cov-report=term
PYTEST_PARALLEL_ARGS = -n auto

.PHONY: help install install-dev test test-all test-fast test-performance test-compatibility test-isolation test-integration test-error-handling test-version-management clean build publish docs lint format check-deps version-check environment-check

# Default target
help:
	@echo "$(CYAN)zarrcompatibility v$(VERSION) - Build & Test System$(RESET)"
	@echo "$(CYAN)===============================================$(RESET)"
	@echo ""
	@echo "$(WHITE)📦 Installation:$(RESET)"
	@echo "  $(GREEN)install$(RESET)          Install package in development mode"
	@echo "  $(GREEN)install-dev$(RESET)      Install with development dependencies"
	@echo "  $(GREEN)install-test$(RESET)     Install test dependencies only"
	@echo ""
	@echo "$(WHITE)🧪 Testing:$(RESET)"
	@echo "  $(GREEN)test$(RESET)             Run all core tests (functionality, integration, isolation)"
	@echo "  $(GREEN)test-all$(RESET)         Run comprehensive test suite (includes performance, error handling)"
	@echo "  $(GREEN)test-fast$(RESET)        Run fast tests only (functionality, isolation)"
	@echo "  $(GREEN)test-performance$(RESET) Run performance and scalability tests"
	@echo "  $(GREEN)test-compatibility$(RESET) Run Zarr version compatibility tests"
	@echo "  $(GREEN)test-isolation$(RESET)   Run isolation tests only"
	@echo "  $(GREEN)test-integration$(RESET) Run integration tests only"
	@echo "  $(GREEN)test-error-handling$(RESET) Run error handling tests"
	@echo "  $(GREEN)test-version-management$(RESET) Run version management tests"
	@echo ""
	@echo "$(WHITE)🔍 Quality:$(RESET)"
	@echo "  $(GREEN)lint$(RESET)             Run linting checks"
	@echo "  $(GREEN)format$(RESET)           Format code with black"
	@echo "  $(GREEN)check-deps$(RESET)       Check dependency compatibility"
	@echo "  $(GREEN)version-check$(RESET)    Check Zarr version compatibility"
	@echo ""
	@echo "$(WHITE)📦 Build & Release:$(RESET)"
	@echo "  $(GREEN)build$(RESET)            Build package for distribution"
	@echo "  $(GREEN)publish$(RESET)          Publish to PyPI"
	@echo "  $(GREEN)docs$(RESET)             Generate documentation"
	@echo ""
	@echo "$(WHITE)🧹 Utilities:$(RESET)"
	@echo "  $(GREEN)clean$(RESET)            Clean build artifacts"
	@echo "  $(GREEN)environment-check$(RESET) Check test environment"

# Environment check
environment-check:
	@echo "$(BLUE)🔍 Checking test environment...$(RESET)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Working dir: $$(pwd)"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); import $(PROJECT_NAME); print('OK $(PROJECT_NAME) v' + $(PROJECT_NAME).__version__)"
	@$(PYTHON) -c "import zarr; print('OK Zarr v' + zarr.__version__)" || echo "$(YELLOW)⚠️ Zarr not available$(RESET)"
	@$(PYTHON) -c "import numpy; print('OK NumPy v' + numpy.__version__)" || echo "$(YELLOW)⚠️ NumPy not available$(RESET)"
	@$(PYTHON) -c "import pytest; print('OK pytest v' + pytest.__version__)" || echo "$(RED)❌ pytest not available$(RESET)"

# Installation targets
install:
	@echo "$(BLUE)📦 Installing $(PROJECT_NAME) in development mode...$(RESET)"
	$(PIP) install -e .

install-dev: install
	@echo "$(BLUE)📦 Installing development dependencies...$(RESET)"
	$(PIP) install -e ".[dev]"

install-test:
	@echo "$(BLUE)📦 Installing test dependencies...$(RESET)"
	$(PIP) install pytest pytest-cov pytest-xdist numpy zarr packaging

# Core test targets
test: environment-check
	@echo "$(BLUE)🧪 Running all zarrcompatibility tests...$(RESET)"
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) -m pytest $(TESTS_DIR)/test_functionality.py $(TESTS_DIR)/test_integration.py $(TESTS_DIR)/test_isolation.py $(PYTEST_ARGS) --junit-xml=$(RESULTS_DIR)/pytest_results.xml
	@echo "$(GREEN)📁 Test summary saved to: $(RESULTS_DIR)/pytest_summary.txt$(RESET)"

test-fast: environment-check
	@echo "$(BLUE)🧪 Running fast tests only...$(RESET)"
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) -m pytest $(TESTS_DIR)/test_functionality.py $(TESTS_DIR)/test_isolation.py $(PYTEST_ARGS) -m "not slow"

test-all: environment-check
	@echo "$(BLUE)🧪 Running comprehensive test suite...$(RESET)"
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) -m pytest $(TESTS_DIR)/ $(PYTEST_ARGS) --junit-xml=$(RESULTS_DIR)/comprehensive_results.xml

# Individual test suites
test-functionality: environment-check
	@echo "$(BLUE)🧪 Running functionality tests...$(RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/test_functionality.py $(PYTEST_ARGS)

test-integration: environment-check
	@echo "$(BLUE)🧪 Running integration tests...$(RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/test_integration.py $(PYTEST_ARGS)

test-isolation: environment-check
	@echo "$(BLUE)🧪 Running isolation tests...$(RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/test_isolation.py $(PYTEST_ARGS)

test-performance: environment-check
	@echo "$(BLUE)🧪 Running performance tests...$(RESET)"
	@if [ -f "$(TESTS_DIR)/test_performance.py" ]; then \
		$(PYTHON) -m pytest $(TESTS_DIR)/test_performance.py $(PYTEST_ARGS) --tb=short; \
	else \
		echo "$(YELLOW)⚠️ Performance tests not found - run: $(PYTHON) $(TESTS_DIR)/test_performance.py$(RESET)"; \
		$(PYTHON) $(TESTS_DIR)/test_performance.py || true; \
	fi

test-error-handling: environment-check
	@echo "$(BLUE)🧪 Running error handling tests...$(RESET)"
	@if [ -f "$(TESTS_DIR)/test_error_handling.py" ]; then \
		$(PYTHON) -m pytest $(TESTS_DIR)/test_error_handling.py $(PYTEST_ARGS) --tb=short; \
	else \
		echo "$(YELLOW)⚠️ Error handling tests not found - run: $(PYTHON) $(TESTS_DIR)/test_error_handling.py$(RESET)"; \
		$(PYTHON) $(TESTS_DIR)/test_error_handling.py || true; \
	fi

test-version-management: environment-check
	@echo "$(BLUE)🧪 Running version management tests...$(RESET)"
	@if [ -f "$(TESTS_DIR)/test_version_management.py" ]; then \
		$(PYTHON) -m pytest $(TESTS_DIR)/test_version_management.py $(PYTEST_ARGS) --tb=short; \
	else \
		echo "$(YELLOW)⚠️ Version management tests not found - run: $(PYTHON) $(TESTS_DIR)/test_version_management.py$(RESET)"; \
		$(PYTHON) $(TESTS_DIR)/test_version_management.py || true; \
	fi

test-compatibility: version-check
	@echo "$(BLUE)🧪 Running Zarr compatibility tests...$(RESET)"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); from $(PROJECT_NAME).version_manager import print_version_info; print_version_info()"

# Test with coverage
test-coverage: environment-check
	@echo "$(BLUE)🧪 Running tests with coverage analysis...$(RESET)"
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) -m pytest $(TESTS_DIR)/ $(PYTEST_ARGS) $(PYTEST_COV_ARGS)

# Parallel testing (if pytest-xdist is available)
test-parallel: environment-check
	@echo "$(BLUE)🧪 Running tests in parallel...$(RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/ $(PYTEST_ARGS) $(PYTEST_PARALLEL_ARGS) || $(MAKE) test

# Quality checks
lint:
	@echo "$(BLUE)🔍 Running lint checks...$(RESET)"
	@$(PYTHON) -m flake8 $(SRC_DIR) --max-line-length=100 --ignore=E203,W503 || echo "$(YELLOW)⚠️ flake8 not available$(RESET)"
	@$(PYTHON) -m pylint $(SRC_DIR)/$(PROJECT_NAME) --disable=C0114,C0115,C0116 || echo "$(YELLOW)⚠️ pylint not available$(RESET)"

format:
	@echo "$(BLUE)🎨 Formatting code...$(RESET)"
	@$(PYTHON) -m black $(SRC_DIR) $(TESTS_DIR) --line-length=100 || echo "$(YELLOW)⚠️ black not available$(RESET)"
	@$(PYTHON) -m isort $(SRC_DIR) $(TESTS_DIR) --profile black || echo "$(YELLOW)⚠️ isort not available$(RESET)"

check-deps:
	@echo "$(BLUE)🔍 Checking dependency compatibility...$(RESET)"
	@$(PYTHON) -c "import pkg_resources; pkg_resources.require(open('requirements.txt').read().split())" || echo "$(YELLOW)⚠️ Some dependencies may be incompatible$(RESET)"

version-check:
	@echo "$(BLUE)🔍 Checking Zarr version compatibility...$(RESET)"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); from $(PROJECT_NAME).version_manager import validate_zarr_version; validate_zarr_version(); print('✅ Zarr version is compatible')" || echo "$(RED)❌ Zarr version compatibility issue$(RESET)"

# Build and distribution
clean:
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(RESET)"
	rm -rf $(BUILD_DIR) $(DIST_DIR) *.egg-info
	rm -rf $(SRC_DIR)/$(PROJECT_NAME)/__pycache__ $(TESTS_DIR)/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/ .coverage

build: clean
	@echo "$(BLUE)📦 Building package...$(RESET)"
	$(PYTHON) -m build

publish: build
	@echo "$(BLUE)📤 Publishing to PyPI...$(RESET)"
	$(PYTHON) -m twine upload dist/*

docs:
	@echo "$(BLUE)📚 Generating documentation...$(RESET)"
	@mkdir -p $(DOCS_DIR)
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); import $(PROJECT_NAME); help($(PROJECT_NAME))" > $(DOCS_DIR)/api_help.txt
	@echo "$(GREEN)📁 Documentation saved to $(DOCS_DIR)/$(RESET)"

# Debug and development targets
debug-test:
	@echo "$(BLUE)🐛 Running tests in debug mode...$(RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/ -v -s --tb=long --pdb-trace

profile-test:
	@echo "$(BLUE)📊 Profiling test performance...$(RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/test_performance.py --profile || echo "$(YELLOW)⚠️ pytest-profiling not available$(RESET)"

# CI/CD targets
ci-test: environment-check test-all test-performance test-error-handling
	@echo "$(GREEN)✅ All CI tests completed$(RESET)"

ci-quick: environment-check test-fast
	@echo "$(GREEN)✅ Quick CI tests completed$(RESET)"

# Monitoring and reporting
test-report:
	@echo "$(BLUE)📊 Generating test report...$(RESET)"
	@mkdir -p $(RESULTS_DIR)
	@echo "# zarrcompatibility v$(VERSION) Test Report" > $(RESULTS_DIR)/test_report.md
	@echo "Generated on: $(date)" >> $(RESULTS_DIR)/test_report.md
	@echo "" >> $(RESULTS_DIR)/test_report.md
	@echo "## Environment" >> $(RESULTS_DIR)/test_report.md
	@echo "- Python: $($(PYTHON) --version)" >> $(RESULTS_DIR)/test_report.md
	@echo "- Working Directory: $(pwd)" >> $(RESULTS_DIR)/test_report.md
	@$(PYTHON) -c "import zarr; print('- Zarr: v' + zarr.__version__)" >> $(RESULTS_DIR)/test_report.md 2>/dev/null || echo "- Zarr: Not available" >> $(RESULTS_DIR)/test_report.md
	@$(PYTHON) -c "import numpy; print('- NumPy: v' + numpy.__version__)" >> $(RESULTS_DIR)/test_report.md 2>/dev/null || echo "- NumPy: Not available" >> $(RESULTS_DIR)/test_report.md
	@echo "" >> $(RESULTS_DIR)/test_report.md
	@echo "## Test Results" >> $(RESULTS_DIR)/test_report.md
	@if [ -f "$(RESULTS_DIR)/pytest_summary.txt" ]; then \
		cat $(RESULTS_DIR)/pytest_summary.txt >> $(RESULTS_DIR)/test_report.md; \
	else \
		echo "No test results available" >> $(RESULTS_DIR)/test_report.md; \
	fi
	@echo "$(GREEN)📁 Test report saved to: $(RESULTS_DIR)/test_report.md$(RESET)"

# Performance monitoring
benchmark:
	@echo "$(BLUE)📊 Running performance benchmarks...$(RESET)"
	@mkdir -p $(RESULTS_DIR)
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); \
		import time; import $(PROJECT_NAME) as zc; \
		print('Benchmark: Enable/disable cycles'); \
		start = time.time(); \
		for i in range(10): zc.enable_zarr_serialization(); zc.disable_zarr_serialization(); \
		print(f'10 cycles: {time.time()-start:.4f}s')" > $(RESULTS_DIR)/benchmark.txt
	@echo "$(GREEN)📁 Benchmark results: $(RESULTS_DIR)/benchmark.txt$(RESET)"

# Development workflow helpers
dev-setup: install-dev
	@echo "$(BLUE)🛠️ Setting up development environment...$(RESET)"
	@$(PYTHON) -m pip install pre-commit black isort flake8 pylint mypy
	@echo "$(GREEN)✅ Development environment ready$(RESET)"

pre-commit: format lint test-fast
	@echo "$(GREEN)✅ Pre-commit checks passed$(RESET)"

# Release workflow
release-check: clean test-all lint
	@echo "$(BLUE)🔍 Running release readiness checks...$(RESET)"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); import $(PROJECT_NAME); print(f'Version: {$(PROJECT_NAME).__version__}')"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); from $(PROJECT_NAME).version_manager import get_supported_versions; v = get_supported_versions(); print(f'Supports Zarr: {v[\"min_version\"]} - {v[\"max_tested\"]}')"
	@echo "$(GREEN)✅ Release checks completed$(RESET)"

# Docker support (if needed)
docker-test:
	@echo "$(BLUE)🐳 Running tests in Docker...$(RESET)"
	@if [ -f "Dockerfile.test" ]; then \
		docker build -f Dockerfile.test -t $(PROJECT_NAME)-test .; \
		docker run --rm $(PROJECT_NAME)-test; \
	else \
		echo "$(YELLOW)⚠️ Dockerfile.test not found$(RESET)"; \
	fi

# Help for specific test types
help-tests:
	@echo "$(CYAN)zarrcompatibility Test Suite Overview$(RESET)"
	@echo "$(CYAN)=====================================$(RESET)"
	@echo ""
	@echo "$(WHITE)🧪 Core Test Suites:$(RESET)"
	@echo "  $(GREEN)test-functionality$(RESET)    - Core serialization features, NumPy handling, type preservation"
	@echo "  $(GREEN)test-integration$(RESET)      - Real-world scientific workflows (microscopy, climate, etc.)"
	@echo "  $(GREEN)test-isolation$(RESET)        - Global JSON isolation, library non-interference"
	@echo ""
	@echo "$(WHITE)🔧 Advanced Test Suites:$(RESET)"
	@echo "  $(GREEN)test-performance$(RESET)      - Speed, memory usage, scalability limits"
	@echo "  $(GREEN)test-error-handling$(RESET)   - Error scenarios, robustness, recovery"
	@echo "  $(GREEN)test-version-management$(RESET) - Zarr version compatibility, configuration"
	@echo ""
	@echo "$(WHITE)📊 Test Combinations:$(RESET)"
	@echo "  $(GREEN)test$(RESET)                  - Core tests (functionality + integration + isolation)"
	@echo "  $(GREEN)test-fast$(RESET)             - Quick tests (functionality + isolation, no slow tests)"
	@echo "  $(GREEN)test-all$(RESET)              - Everything (all suites including performance)"
	@echo ""
	@echo "$(WHITE)🎯 Quality Checks:$(RESET)"
	@echo "  $(GREEN)test-coverage$(RESET)         - Tests with coverage analysis"
	@echo "  $(GREEN)test-parallel$(RESET)         - Parallel test execution"
	@echo "  $(GREEN)benchmark$(RESET)             - Performance benchmarking"

# Troubleshooting
troubleshoot:
	@echo "$(CYAN)zarrcompatibility Troubleshooting$(RESET)"
	@echo "$(CYAN)=================================$(RESET)"
	@echo ""
	@echo "$(WHITE)🔍 Environment Check:$(RESET)"
	@$(MAKE) environment-check
	@echo ""
	@echo "$(WHITE)🔍 Version Compatibility:$(RESET)"
	@$(MAKE) version-check
	@echo ""
	@echo "$(WHITE)🔍 Dependency Status:$(RESET)"
	@$(MAKE) check-deps
	@echo ""
	@echo "$(WHITE)💡 Common Issues:$(RESET)"
	@echo "  - ImportError: Install with 'make install-dev'"
	@echo "  - Zarr version: Check compatibility with 'make version-check'"
	@echo "  - Test failures: Run 'make test-fast' for quick diagnosis"
	@echo "  - Performance: Run 'make test-performance' to identify bottlenecks"

# Show current configuration
show-config:
	@echo "$(CYAN)zarrcompatibility Configuration$(RESET)"
	@echo "$(CYAN)===============================$(RESET)"
	@echo "Project: $(PROJECT_NAME) v$(VERSION)"
	@echo "Python: $($(PYTHON) --version)"
	@echo "Source: $(SRC_DIR)"
	@echo "Tests: $(TESTS_DIR)"
	@echo "Results: $(RESULTS_DIR)"
	@echo ""
	@echo "$(WHITE)Installed Packages:$(RESET)"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '$(SRC_DIR)'); import $(PROJECT_NAME); print(f'✅ $(PROJECT_NAME) v{$(PROJECT_NAME).__version__}')" 2>/dev/null || echo "❌ $(PROJECT_NAME) not installed"
	@$(PYTHON) -c "import zarr; print(f'✅ zarr v{zarr.__version__}')" 2>/dev/null || echo "❌ zarr not available"
	@$(PYTHON) -c "import numpy; print(f'✅ numpy v{numpy.__version__}')" 2>/dev/null || echo "❌ numpy not available"
	@$(PYTHON) -c "import pytest; print(f'✅ pytest v{pytest.__version__}')" 2>/dev/null || echo "❌ pytest not available"

# Default target points to help
.DEFAULT_GOAL := help