PYTHON ?= python3
PORT ?= 8000

.PHONY: help serve validate validate-json check-syntax clean

help:
	@echo "Available targets:"
	@echo "  make serve        Start local HTTP server on port $(PORT)"
	@echo "  make validate     Run data.json validator (JSON + ranges + monotonicity)"
	@echo "  make check-syntax Lint JS and HTML files"
	@echo "  make clean        Stop any running server and remove cache"
	@echo "  make all          Run validate + check-syntax"

serve:
	@echo "Starting server at http://localhost:$(PORT)"
	@echo "Open http://localhost:$(PORT) in your browser"
	@echo "Press Ctrl+C to stop"
	$(PYTHON) -m http.server $(PORT)

validate:
	$(PYTHON) validate.py

check-syntax:
	@echo "Checking data.json..."
	@$(PYTHON) -c "import json; json.load(open('data.json')); print('  data.json: OK')"
	@echo "Checking app.js (node syntax check)..."
	@if command -v node >/dev/null 2>&1; then \
		node --check app.js && echo "  app.js: OK"; \
	else \
		echo "  app.js: node not installed, skipping"; \
	fi
	@echo "Checking index.html (basic well-formed)..."
	@$(PYTHON) -c "from html.parser import HTMLParser; \
		HTMLParser().feed(open('index.html').read()); \
		print('  index.html: OK')"

clean:
	@echo "Cleaning up..."
	@-pkill -f "http.server $(PORT)" 2>/dev/null; true
	@rm -rf __pycache__ .cache
	@echo "Done"

all: validate check-syntax
