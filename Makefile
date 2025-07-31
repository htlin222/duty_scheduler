# 醫院值班排程 ICS 生成器 Makefile
# Hospital Duty Schedule ICS Generator

.PHONY: help install dev-install env run test clean lint check config debug

# Default target
help: ## Show this help message
	@echo "醫院值班排程 ICS 生成器 - Hospital Duty Schedule ICS Generator"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install project dependencies using uv
	@echo "🚀 Installing duty scheduler..."
	uv venv
	@echo "📦 Installing dependencies..."
	uv pip install -r requirements.txt
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit config.yml with your Google Sheets URL"
	@echo "  2. Run 'make config' to open the config file"
	@echo "  3. Run 'make run' to generate ICS files"

dev-install: install ## Install development dependencies
	@echo "🔧 Installing development tools..."
	uv pip install ruff black isort
	@echo "✅ Development environment ready!"

env: ## Setup and activate uv virtual environment
	@echo "🌟 Setting up uv virtual environment..."
	uv venv
	@echo "📦 Installing dependencies with uv..."
	uv pip install -r requirements.txt
	@echo "✅ Environment ready!"
	@echo ""
	@echo "To activate the environment, run:"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "Or use 'uv run <script>' to run scripts directly"

# Configuration
config: ## Open config.yml for editing
	@echo "📝 Opening configuration file..."
	@if command -v code >/dev/null 2>&1; then \
		code config.yml; \
	elif command -v vim >/dev/null 2>&1; then \
		vim config.yml; \
	elif command -v nano >/dev/null 2>&1; then \
		nano config.yml; \
	else \
		echo "Please edit config.yml manually"; \
		echo "Set your Google Sheets CSV URL and configure locations"; \
	fi

# Execution
run: ## Run the duty schedule generator
	@echo "🏥 Generating duty schedules..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	source .venv/bin/activate && python main.py

test: ## Run with sample data for testing
	@echo "🧪 Testing with sample data..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@# Backup current config
	@cp config.yml config.yml.backup
	@# Temporarily use sample data
	@sed 's|csv_url:.*|csv_url: "sample_duty.csv"|' config.yml.backup > config.yml
	@echo "Using sample data for testing..."
	source .venv/bin/activate && python main.py
	@# Restore original config
	@mv config.yml.backup config.yml
	@echo "✅ Test complete! Original config restored."

debug: ## Run with detailed debugging output
	@echo "🔍 Running in debug mode..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	source .venv/bin/activate && python -u main.py

# Quality assurance
lint: ## Run code formatting and linting
	@echo "🧹 Running code quality checks..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make dev-install' first."; \
		exit 1; \
	fi
	source .venv/bin/activate && ruff check --fix .
	source .venv/bin/activate && ruff format .
	@echo "✅ Code formatting complete!"

check: lint ## Run all quality checks
	@echo "✅ All quality checks passed!"

# Cleanup
clean: ## Clean up generated files and cache
	@echo "🧽 Cleaning up..."
	rm -rf output/*.ics
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf *.pyc
	@echo "✅ Cleanup complete!"

clean-all: clean ## Clean everything including virtual environment
	@echo "🗑️  Removing virtual environment..."
	rm -rf .venv
	@echo "✅ Complete cleanup done!"

# Utilities
show-output: ## Show generated ICS files
	@echo "📁 Generated ICS files:"
	@if [ -d "output" ]; then \
		ls -la output/*.ics 2>/dev/null || echo "No ICS files found in output/"; \
	else \
		echo "Output directory doesn't exist yet. Run 'make run' first."; \
	fi

validate-config: ## Validate configuration file
	@echo "🔍 Validating configuration..."
	@if [ ! -f "config.yml" ]; then \
		echo "❌ config.yml not found!"; \
		exit 1; \
	fi
	@echo "✅ Configuration file exists"
	@python -c "import yaml; yaml.safe_load(open('config.yml'))" && echo "✅ YAML syntax is valid" || echo "❌ Invalid YAML syntax"

# Documentation
readme: ## Open README.md
	@if command -v code >/dev/null 2>&1; then \
		code README.md; \
	elif command -v less >/dev/null 2>&1; then \
		less README.md; \
	else \
		cat README.md; \
	fi

# Quick start workflow
setup: install config ## Complete setup (install + config)
	@echo ""
	@echo "🎉 Setup complete!"
	@echo "You can now run 'make run' to generate duty schedules."

# Status check
status: ## Show project status and information
	@echo "醫院值班排程 ICS 生成器 - Status"
	@echo "=================================="
	@echo ""
	@echo "📁 Project structure:"
	@ls -la *.py *.yml *.txt *.md 2>/dev/null || true
	@echo ""
	@echo "🔧 Virtual environment:"
	@if [ -d ".venv" ]; then \
		echo "  ✅ Virtual environment exists"; \
		if [ -f ".venv/pyvenv.cfg" ]; then \
			echo "  📍 Python:" $$(grep "home" .venv/pyvenv.cfg | cut -d' ' -f3 2>/dev/null || echo "Unknown"); \
		fi; \
	else \
		echo "  ❌ Virtual environment not found (run 'make install')"; \
	fi
	@echo ""
	@echo "📊 Output files:"
	@if [ -d "output" ] && [ "$$(ls -A output 2>/dev/null)" ]; then \
		echo "  📁 $$(ls output/*.ics 2>/dev/null | wc -l | xargs) ICS files generated"; \
	else \
		echo "  📁 No output files yet (run 'make run')"; \
	fi
	@echo ""
	@echo "Next steps:"
	@echo "  • Run 'make config' to edit configuration"
	@echo "  • Run 'make run' to generate schedules"
	@echo "  • Run 'make test' to test with sample data"