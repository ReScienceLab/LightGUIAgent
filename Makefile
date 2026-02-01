.PHONY: help sync test test-verbose lint format format-check check clean run example-simple example-order dev

help:  ## Show this help
	@echo "LightGUIAgent - Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

sync:  ## Install/sync dependencies with uv
	uv sync

test:  ## Run all tests
	uv run python tests/test_grid_system.py

test-verbose:  ## Run tests with verbose output
	uv run python tests/test_grid_system.py -v

lint:  ## Run linter (ruff)
	uv run ruff check .

format:  ## Auto-format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting without changes
	uv run ruff format --check .

check:  ## Run all checks (lint + format-check + test)
	@echo "Running format check..."
	@make format-check
	@echo "\nRunning linter..."
	@make lint
	@echo "\nRunning tests..."
	@make test

clean:  ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

run:  ## Run main.py with a task (usage: make run TASK="Open Meituan")
	@if [ -z "$(TASK)" ]; then \
		echo "❌ Error: TASK not specified"; \
		echo "Usage: make run TASK=\"Your task description\""; \
		exit 1; \
	fi
	uv run python main.py "$(TASK)"

example-simple:  ## Run simple click example
	uv run python examples/simple_click.py

example-order:  ## Run meituan order example
	uv run python examples/meituan_order.py

dev:  ## Setup development environment
	@echo "Setting up development environment..."
	@make sync
	@echo "\n✅ Setup complete! Try 'make test' to verify."
