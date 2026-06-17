PYTHON ?= python3

.PHONY: help init check validate clean all

help:
	@echo "Available targets:"
	@echo "  make init   Install npm + guide for Browser MCP extension (one-time)"
	@echo "  make check  Validate data + check JS/HTML syntax"
	@echo "  make clean  Remove cache"

init:
	@echo "=== 1. Installing Node.js + npm (provides npx) ==="
	@if command -v npx >/dev/null 2>&1; then \
		echo "  npx already present: $$(command -v npx)"; \
	else \
		echo "  npx not found. Installing via apt (needs sudo)..."; \
		sudo apt update -qq && sudo apt install -y nodejs npm; \
	fi
	@command -v npx >/dev/null 2>&1 || { echo "ERROR: npx still not available"; exit 1; }
	@echo "  node $$(node --version)  npm $$(npm --version)  npx $$(npx --version)"
	@echo ""
	@echo "=== 2. Browser MCP extension (manual, ~30s) ==="
	@echo "  The @browsermcp/mcp server also needs its browser extension."
	@echo ""
	@echo "  Chrome:  https://chromewebstore.google.com/detail/bjfgambnhccakkhmjdoflnmmkfkcoambl"
	@echo "  Edge:    https://microsoftedge.microsoft.com/addons/detail/browser-mcp/knjblggclcdgfbgnamhofflpjgegafee"
	@echo ""
	@echo "  Steps:"
	@echo "    1. Open the link above in Chrome or Edge."
	@echo "    2. Click 'Add to <browser>'."
	@echo "    3. Click the Browser MCP icon in the toolbar — status must be 'Connected' (green)."
	@echo "    4. Quit and restart opencode so it picks up the new npx."
	@echo ""
	@echo "=== 3. Verify ==="
	@echo "  After the extension is active, run:"
	@echo "    opencode"
	@echo "    /mcp"
	@echo "  You should see 'browsermcp' listed as connected."

check: validate
	@echo "Checking data.js / app.js (node syntax check)..."
	@if command -v node >/dev/null 2>&1; then \
		node --check data.js && echo "  data.js: OK"; \
		node --check app.js && echo "  app.js: OK"; \
	else \
		echo "  data.js / app.js: node not installed, skipping"; \
	fi
	@echo "Checking index.html (basic well-formed)..."
	@$(PYTHON) -c "from html.parser import HTMLParser; \
		HTMLParser().feed(open('index.html').read()); \
		print('  index.html: OK')"

validate:
	$(PYTHON) validate.py

clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__ .cache
	@echo "Done"

all: check
