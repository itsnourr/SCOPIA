.PHONY: help setup install clean run test lint format db-init db-migrate db-reset

# Default target
help:
	@echo "Forensic Crime Analysis Agent - Available Commands"
	@echo "=================================================="
	@echo "setup        - Complete first-time setup (venv + install + db-init)"
	@echo "install      - Install dependencies from requirements.txt"
	@echo "clean        - Remove virtual environment and cache files"
	@echo "run          - Start the Streamlit application"
	@echo "test         - Run test suite with coverage"
	@echo "lint         - Run code quality checks (flake8, mypy)"
	@echo "format       - Format code with black"
	@echo "db-init      - Initialize database schema"
	@echo "db-migrate   - Run database migrations"
	@echo "db-reset     - Reset database (WARNING: destroys all data)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. Copy env.example to .env and fill in values"
	@echo "  2. Run: make setup"
	@echo "  3. Run: make run"

# Complete first-time setup
setup:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Activating venv and installing dependencies..."
	@if [ -f venv/Scripts/activate ]; then \
		. venv/Scripts/activate && pip install --upgrade pip && pip install -r requirements.txt; \
	else \
		. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt; \
	fi
	@echo "Creating data directories..."
	mkdir -p data/encrypted data/chroma
	@echo "Initializing database..."
	@if [ -f venv/Scripts/activate ]; then \
		. venv/Scripts/activate && python -m app.db.init_db; \
	else \
		. venv/bin/activate && python -m app.db.init_db; \
	fi
	@echo "Setup complete! Copy env.example to .env and configure your settings."

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf venv
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

# Run Streamlit app
run:
	streamlit run app/ui/app.py --server.port=$${STREAMLIT_PORT:-8501}

# Run tests
test:
	pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	@echo "Running flake8..."
	flake8 app --max-line-length=100 --ignore=E203,W503
	@echo "Running mypy..."
	mypy app --ignore-missing-imports

# Format code
format:
	black app --line-length=100

# Initialize database
db-init:
	python -m app.db.init_db

# Run migrations (placeholder for future migration tool)
db-migrate:
	@echo "Migrations not yet implemented. Use db-init for now."

# Reset database
db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	python -m app.db.init_db --reset

# Generate encryption key
generate-key:
	@python -c "import secrets; print('AES_MASTER_KEY=' + secrets.token_hex(32))"

