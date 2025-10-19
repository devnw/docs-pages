CRUSH.md — Dev quick ref for doc-pages

Commands
- JS build: npm run build (ncc) ➜ dist/
- JS tests: npm test
- JS single test: npx jest __tests__/index.test.js -t "renders charts"
- Python dev deps: python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt
- Python tests: pytest -q
- Python single test: pytest -q tests/test_metrics.py::test_metrics_basic
- MkDocs (optional, if installed): mkdocs build --site-dir site_build

Lint/format
- JS: ESLint recommended (not configured here). If present: npx eslint .
- Python: Follow PEP 8; no linter pinned. Keep lines ≤ 100 cols; docstrings for public funcs.

Code style (JS)
- Node 20, CommonJS require; 2-space indent; semicolons; const/let; async/await.
- Use @actions/core for inputs/outputs/logging; @actions/exec for processes. Prefer getExecOutput; set ignoreReturnCode when non-fatal; never log tokens.
- Env-driven config (TOKEN, NAV_ORDER, etc.); keep behavior when tools missing (core.warning), avoid new deps.

Code style (Python)
- Python 3.11 stdlib only; argparse + env fallbacks; snake_case; pure funcs where possible; deterministic I/O under site_src/.
- Errors: exit 0 on success, 2 for schema errors; JSON Lines logs at INFO, ERROR on failures; exponential backoff for GitHub 403/429; never print secrets.

Tests layout
- Jest matches __tests__/**/*.test.js (testEnvironment=node; jsdom used in charts tests).
- PyTest tests in tests/ (metrics, trends, security, pagination).

Copilot rules (see .github/copilot-instructions.md)
- Honor action contract (Go tests with atomic coverage + cover.html, optional benches/history, godocdown-like docs, MkDocs site, Pages artifact).
- Integrate helper scripts; wire outputs site_dir and coverage_percent; validate inputs; treat artifacts as data.
- Security: env tokens; least-privilege; backoff on 403/429. Tests: PyTest for Python scripts; Jest/jsdom for chart bootstrappers.