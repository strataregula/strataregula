# StrataRegula Makefile
# Development and quality assurance tasks

.PHONY: help install test lint format clean
.PHONY: golden-baseline golden-check golden-report golden-clean
.PHONY: docs build release

# Default target
help:
	@echo "StrataRegula Development Tasks"
	@echo "=============================="
	@echo ""
	@echo "Development:"
	@echo "  install          Install dependencies and development tools"
	@echo "  test             Run all tests"
	@echo "  lint             Run code linting (ruff, mypy)"
	@echo "  format           Format code (ruff format)"
	@echo "  clean            Clean build artifacts"
	@echo ""
	@echo "Golden Metrics Guard:"
	@echo "  golden-baseline  Capture new performance baseline"
	@echo "  golden-check     Run regression guard (fail on regressions)"
	@echo "  golden-report    Generate regression report (non-failing)"
	@echo "  golden-clean     Clean all golden reports"
	@echo ""
	@echo "Release:"
	@echo "  docs             Generate documentation"
	@echo "  build            Build distribution packages"
	@echo "  release          Full release workflow"

# Development tasks
install:
	pip install -e .
	pip install -r requirements.txt
	@echo "✅ StrataRegula development environment ready"

test:
	pytest -v
	@echo "✅ All tests passed"

lint:
	ruff check .
	mypy strataregula/ --python-version 3.11
	@echo "✅ Code quality checks passed"

format:
	ruff format .
	@echo "✅ Code formatted"

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ __pycache__/ .mypy_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Build artifacts cleaned"

# Golden Metrics Guard tasks
golden-baseline:
	@echo "🎯 Capturing new Golden Metrics baseline..."
	@mkdir -p tests/golden/baseline
	@python scripts/golden_capture.py --out tests/golden/baseline
	@git add tests/golden/baseline/*.json
	@echo "✅ Baseline captured and staged for commit"
	@echo ""
	@echo "⚠️  IMPORTANT: Review baseline changes before committing!"
	@echo "   git diff --cached tests/golden/baseline/"
	@echo "   git commit -m \"Update golden metrics baseline\""

golden-check:
	@echo "🔍 Running Golden Metrics regression guard..."
	@pytest -v tests/golden/test_regression_guard.py
	@echo "✅ No performance regressions detected"

golden-report:
	@echo "📊 Generating Golden Metrics regression report..."
	@pytest -v tests/golden/test_regression_guard.py || true
	@echo ""
	@echo "📋 Reports generated:"
	@ls -la reports/diff/*.md 2>/dev/null || echo "   No reports found"
	@ls -la reports/current/*.json 2>/dev/null || echo "   No current metrics found"
	@echo ""
	@echo "💡 Review reports in reports/diff/ and reports/current/"

golden-clean:
	@echo "🧹 Cleaning Golden Metrics reports..."
	@rm -rf reports/current reports/diff reports/junit
	@mkdir -p reports/current reports/diff reports/junit
	@touch reports/.gitkeep
	@echo "✅ Golden reports cleaned (ready for next run)"

# Documentation and release tasks
docs:
	@echo "📚 Generating documentation..."
	@echo "TODO: Add documentation generation command"

build: clean lint test
	@echo "🏗️  Building StrataRegula distribution..."
	python -m build
	@echo "✅ Build complete"
	@ls -la dist/

release: build golden-check
	@echo "🚀 Release workflow complete"
	@echo "📦 Packages ready in dist/"
	@echo "✅ Golden metrics verified - no performance regressions"

# Environment-specific golden metrics tasks
golden-ci:
	@echo "🤖 CI Golden Metrics Check"
	GOLDEN_LATENCY_ALLOW_PCT=1.5 \
	GOLDEN_P95_ALLOW_PCT=2.0 \
	GOLDEN_THROUGHPUT_ALLOW_PCT=1.0 \
	GOLDEN_MEMORY_ALLOW_PCT=3.0 \
	pytest -v tests/golden/test_regression_guard.py --junitxml=reports/junit/golden-results.xml

golden-strict:
	@echo "🎯 Strict Golden Metrics Check (production-ready)"
	GOLDEN_LATENCY_ALLOW_PCT=0.5 \
	GOLDEN_P95_ALLOW_PCT=0.8 \
	GOLDEN_THROUGHPUT_ALLOW_PCT=0.2 \
	GOLDEN_MEMORY_ALLOW_PCT=1.0 \
	pytest -v tests/golden/test_regression_guard.py

# Development shortcuts
dev-setup: install golden-baseline
	@echo "🎉 StrataRegula development environment fully configured!"

quick-check: lint test golden-check
	@echo "⚡ Quick quality check complete"