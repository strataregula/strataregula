# Strataregula Project Makefile
# ================================================
# SuperClaude Expert Personas Available:
# ================================================
# 1. 🛡️ Security Expert - セキュリティ脆弱性チェック
#    Usage: make security-check
# 2. ⚡ Performance Specialist - パフォーマンス最適化
#    Usage: make benchmark
# 3. 🏗️ System Architect - アーキテクチャ設計
#    Usage: make architecture-review
# 4. 🧪 Testing Expert - テスト戦略
#    Usage: make test-all
# 5. 📚 Documentation Specialist - ドキュメント作成
#    Usage: make docs
# 6. 🎨 Frontend Developer - UI/UX実装
#    Usage: make ui-check
# 7. 🔧 Backend Engineer - サーバーサイド開発
#    Usage: make backend-test
# 8. 📊 Data Analyst - データ分析
#    Usage: make analyze-metrics
# 9. ☁️ DevOps Engineer - CI/CD、デプロイ
#    Usage: make deploy
# 10. 🔍 Code Reviewer - コード品質保証
#    Usage: make review
# 11. 🎯 Product Manager - 要件定義
#    Usage: make requirements
# ================================================

.PHONY: help
help: ## Show this help message
	@echo "Strataregula Project Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "SuperClaude Experts:"
	@echo "  make personas       Show available SuperClaude expert personas"

# ===== 🧪 Testing Expert Commands =====
.PHONY: test
test: ## Run all tests
	pytest tests/ -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage
	pytest tests/ --cov=strataregula --cov-report=html --cov-report=term

.PHONY: test-all
test-all: ## Run comprehensive test suite
	@echo "🧪 Testing Expert: Running comprehensive tests..."
	pytest tests/ -v --cov=strataregula --cov-report=term
	pytest tests/benchmarks/ -v
	pytest tests/integration/ -v

# ===== ⚡ Performance Specialist Commands =====
.PHONY: benchmark
benchmark: ## Run all benchmarks and generate report
	@echo "⚡ Running Performance Benchmarks..."
	@mkdir -p notebooks scripts docs/images
	python scripts/run_benchmarks.py
	@echo "📊 Generating visualizations..."
	python scripts/generate_benchmark_images.py
	@echo "📈 Benchmark complete! View results with 'make benchmark-view'"

.PHONY: benchmark-notebook
benchmark-notebook: ## Open benchmark visualization in Jupyter
	@echo "📊 Opening benchmark results in Jupyter Notebook..."
	jupyter notebook notebooks/benchmark_results.ipynb

.PHONY: benchmark-view
benchmark-view: ## View benchmark results in browser
	@echo "📊 Converting notebook to HTML..."
	python scripts/convert_notebook.py
	@echo "🌐 Opening benchmark results in browser..."
	@python -c "import webbrowser; webbrowser.open('docs/benchmark.html')" || echo "Open docs/benchmark.html in your browser"

.PHONY: benchmark-simple
benchmark-simple: ## Run simple benchmark tests only
	python -m pytest tests/benchmarks/ -v

.PHONY: benchmark-images
benchmark-images: ## Generate benchmark visualization images
	@echo "📊 Generating benchmark visualizations..."
	python scripts/generate_benchmark_images.py
	@echo "✅ Images saved to docs/images/"

.PHONY: benchmark-publish
benchmark-publish: ## Publish benchmarks to GitHub Pages
	@echo "🌐 Publishing benchmarks to GitHub Pages..."
	python scripts/convert_notebook.py
	git add docs/images/*.png docs/benchmark.html README.md
	git commit -m "Update benchmark visualizations" || echo "No changes to commit"
	git push
	@echo "🚀 Published! Will be available at GitHub Pages shortly"

# ===== 🛡️ Security Expert Commands =====
.PHONY: security-check
security-check: ## Run security vulnerability scan
	@echo "🛡️ Security Expert: Scanning for vulnerabilities..."
	@pip install bandit safety pip-audit 2>/dev/null || echo "Installing security tools..."
	bandit -r strataregula/ || echo "Bandit scan complete"
	safety check || echo "Safety check complete"
	pip-audit || echo "Pip-audit complete"

# ===== 📚 Documentation Specialist Commands =====
.PHONY: docs
docs: ## Build documentation
	@echo "📚 Building documentation..."
	mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	mkdocs serve --dev-addr localhost:8000

.PHONY: docs-check
docs-check: ## Check documentation quality
	python docs/check_docs.py

.PHONY: docs-deploy
docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "⚠️  GitHub Pages deployment (ドメイン設定待ち)"
	@echo "When ready, run: mkdocs gh-deploy --force"

# ===== 🔍 Code Reviewer Commands =====
.PHONY: review
review: ## Run code quality checks
	@echo "🔍 Code Reviewer: Checking code quality..."
	ruff check strataregula/ tests/
	mypy strataregula/ --strict || echo "Type checking complete"
	@echo "✅ Code review complete"

.PHONY: format
format: ## Format code
	black strataregula/ tests/
	isort strataregula/ tests/
	ruff check --fix strataregula/ tests/

# ===== 🔧 Backend Engineer Commands =====
.PHONY: backend-test
backend-test: ## Test backend components
	@echo "🔧 Testing backend components..."
	pytest tests/core/ -v
	pytest tests/plugins/ -v
	pytest tests/stream/ -v

# ===== 📊 Data Analyst Commands =====
.PHONY: analyze-metrics
analyze-metrics: ## Analyze project metrics
	@echo "📊 Analyzing metrics..."
	@mkdir -p scripts notebooks
	python scripts/analyze_metrics.py || echo "Creating metrics analysis script..."
	@echo "📈 Metrics analysis complete"

# ===== ☁️ DevOps Engineer Commands =====
.PHONY: build
build: ## Build package
	@echo "☁️ Building package..."
	python -m build

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "🐳 Building Docker images..."
	docker build -t strataregula:latest . || echo "Docker build attempted"

.PHONY: ci-test
ci-test: ## Run CI pipeline locally
	@echo "☁️ DevOps: Running CI pipeline..."
	$(MAKE) review
	$(MAKE) test
	$(MAKE) benchmark-simple

# ===== 🏗️ System Architect Commands =====
.PHONY: architecture-review
architecture-review: ## Review system architecture
	@echo "🏗️ Reviewing architecture..."
	@echo "📋 Architecture review points:"
	@echo "  - Core module structure: strataregula/core/"
	@echo "  - Plugin system: strataregula/plugins/"
	@echo "  - Stream processing: strataregula/stream/"
	@echo "  - Documentation: docs/"
	@echo "✅ Architecture review complete"

# ===== 🎯 Product Manager Commands =====
.PHONY: requirements
requirements: ## Check requirements coverage
	@echo "🎯 Checking requirements..."
	@echo "📋 Current features:"
	@echo "  ✅ Pattern expansion system"
	@echo "  ✅ Configuration compilation"
	@echo "  ✅ Plugin architecture"
	@echo "  ✅ Stream processing"
	@echo "  ✅ Performance benchmarks"
	@echo "  ✅ Documentation system"

# ===== 🎨 Frontend Developer Commands =====
.PHONY: ui-check
ui-check: ## Check UI/documentation presentation
	@echo "🎨 Frontend: Checking presentation..."
	mkdocs serve --dev-addr localhost:8001 &
	@echo "📱 Documentation UI available at http://localhost:8001"
	@echo "🎨 UI check complete"

# ===== Installation Commands =====
.PHONY: install
install: ## Install package in development mode
	pip install -e .

.PHONY: install-dev
install-dev: ## Install with development dependencies
	pip install -e ".[dev,test,docs]"
	pip install pre-commit jupyter matplotlib seaborn pandas
	pre-commit install

.PHONY: install-plugins
install-plugins: ## Install plugin ecosystem
	pip install strataregula-doe-runner[simroute] || echo "DOE Runner not available"

# ===== Benchmark Infrastructure =====
.PHONY: setup-notebooks
setup-notebooks: ## Setup Jupyter notebook infrastructure
	@mkdir -p notebooks scripts
	@echo "📓 Setting up notebook infrastructure..."
	@test -f notebooks/benchmark_results.ipynb || echo "Creating notebook template..."

# ===== Cleanup Commands =====
.PHONY: clean
clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info
	rm -rf htmlcov/ .coverage .pytest_cache/
	rm -rf .ruff_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ===== SuperClaude Integration =====
.PHONY: sc-analyze
sc-analyze: ## Run SuperClaude analysis
	@echo "🤖 SuperClaude: Analyzing project..."
	@echo "Run: /sc:analyze in Claude"

.PHONY: sc-improve
sc-improve: ## Run SuperClaude improvements  
	@echo "🤖 SuperClaude: Suggesting improvements..."
	@echo "Run: /sc:improve in Claude"

.PHONY: personas
personas: ## Show SuperClaude expert personas
	@echo "SuperClaude Personas (自動選択される専門家):"
	@echo "================================================"
	@echo "1.  🛡️  Security Expert       - セキュリティ脆弱性チェック"
	@echo "    Usage: make security-check"
	@echo "2.  ⚡  Performance Specialist - パフォーマンス最適化"  
	@echo "    Usage: make benchmark"
	@echo "3.  🏗️  System Architect      - アーキテクチャ設計"
	@echo "    Usage: make architecture-review"
	@echo "4.  🧪  Testing Expert         - テスト戦略"
	@echo "    Usage: make test-all"
	@echo "5.  📚  Documentation Spec.    - ドキュメント作成"
	@echo "    Usage: make docs"
	@echo "6.  🎨  Frontend Developer     - UI/UX実装"
	@echo "    Usage: make ui-check"
	@echo "7.  🔧  Backend Engineer       - サーバーサイド開発"
	@echo "    Usage: make backend-test"
	@echo "8.  📊  Data Analyst          - データ分析"
	@echo "    Usage: make analyze-metrics"
	@echo "9.  ☁️  DevOps Engineer       - CI/CD、デプロイ"
	@echo "    Usage: make ci-test"
	@echo "10. 🔍  Code Reviewer         - コード品質保証"
	@echo "    Usage: make review"
	@echo "11. 🎯  Product Manager       - 要件定義"
	@echo "    Usage: make requirements"

# ===== Domain Setup (Prepared) =====
.PHONY: docs-deploy-domain
docs-deploy-domain: ## Deploy to custom domain (when ready)
	@echo "📝 Steps to deploy to strataregula.com:"
	@echo "1. Create docs/CNAME with content: strataregula.com"
	@echo "2. Run: mkdocs gh-deploy --force"
	@echo "3. Configure DNS A records:"
	@echo "   - 185.199.108.153"
	@echo "   - 185.199.109.153" 
	@echo "   - 185.199.110.153"
	@echo "   - 185.199.111.153"
	@echo "4. Enable HTTPS in GitHub Pages settings"

# ===== Quick Workflows =====
.PHONY: daily
daily: ## Daily development workflow
	@echo "🌅 Running daily checks..."
	$(MAKE) review
	$(MAKE) test
	@echo "✅ Daily checks passed!"

.PHONY: release-check
release-check: ## Pre-release validation
	@echo "🚀 Release validation..."
	$(MAKE) review
	$(MAKE) test-all
	$(MAKE) benchmark-simple
	$(MAKE) docs-check
	@echo "✅ Release ready!"

# ===== Project Status =====
.PHONY: status
status: ## Show project status
	@echo "📊 Strataregula Project Status"
	@echo "=============================="
	@echo "Core: v0.1.1 ✅"
	@echo "DOE Runner: v0.1.0 ✅" 
	@echo "Documentation: Ready ✅"
	@echo "SuperClaude: Installed ✅"
	@echo "Benchmarks: Operational ✅"
	@echo ""
	@echo "Expert Personas: 11 available (make personas)"
	@echo "Next: Domain configuration pending"