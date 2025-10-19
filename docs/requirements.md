## Requirements Document (v1.0)

### 2.1 Overview

Deliver a reproducible, composite GitHub Action that:

1. runs Go tests with atomic coverage, emits `cover.html`;
2. optionally runs benchmarks and maintains a JSON history branch;
3. generates API docs using `godocdown`;
4. builds an MkDocs Material site where README is the home and pages include reference/coverage/bench/docs;
5. uploads a Pages artifact for deployment by the caller workflow. Inputs/outputs and installer behavior match the README.&#x20;

### 2.2 Components & Data Flow

* **Action runner** (composite): installs Node 20, Go (stable), Python 3.x, optional tools (`godocdown`, `gocyclo`, mkdocs-material), then runs the generator steps.&#x20;
* **Metrics**: `collect_metrics.py` reads repo state and optional `.coverage_percent`, writes `site_src/metrics.json` and `site_src/metrics.md`. `gen_metrics_md.py` optionally appends a “Trends” section and copies history + `metrics.js`.  &#x20;
* **Security**: `collect_security.py` calls GH APIs to count open Dependabot/CodeQL/Secret alerts, writes `site_src/security.json` and adds badges/table in `site_src/security.md`. `gen_security_md.py` optionally appends a “Trends” section and copies history + `security.js`.  &#x20;

### 2.3 Interfaces (Inputs/Outputs)

* **Inputs**: `github_token` (required); `run_benchmarks` (bool, default true); `bench_branch` (default `bench-data`); `site_name` (optional override); `extra_nav_docs` (bool, default true); `nav_order` (comma order); `embed_coverage_html` (bool, default true).&#x20;
* **Outputs**: `site_dir` (path); `coverage_percent` (float, overall).&#x20;

### 2.4 Functional Rules

* **Coverage**: compute atomic coverage via `go test`; write overall percentage to `.coverage_percent`; embed/iframe `cover.html` when `embed_coverage_html=true`.&#x20;
* **Metrics Selection** (`collect_metrics.py`): enabled via env `METRICS` (comma‑sep: `coverage,tests,files,loc,avg_complexity,high_complexity`); `HIGH_COMPLEXITY_THRESHOLD` default **10**; ignore `vendor/`.&#x20;
* **Security** (`collect_security.py`): if `GITHUB_REPOSITORY` and `GITHUB_TOKEN|TOKEN` are set, fetch lists for `/dependabot/alerts?state=open&per_page=100`, `/code-scanning/alerts?state=open&per_page=100`, `/secret-scanning/alerts?state=open&per_page=100`; tally severities and open counts; render HTML badges; persist JSON + MD.&#x20;
* **History → Trends**: when `metrics/summary.json` or `security/summary.json` exists, copy `summary.json` and `data/*.json` to `site_src/{metrics,security}/` and ensure a “Trends” block with a `<div id="...-charts">` and `<script src="{metrics|security}/{metrics|security}.js"></script>`. &#x20;
* **Charts**: front‑end renderers iterate `summary.metrics`, fetch each `data/*.json`, and draw tiny line charts on a 240×60 canvas. Failures show a fallback message. &#x20;

### 2.5 Non‑Functional Targets

* Runner time: under 5 minutes on `ubuntu-latest` for medium repos.
* Idempotence: re‑running produces the same `site_src/` content given identical repo state.
* Portability: no OS‑specific paths; POSIX shell ok within action.

### 2.6 Security & Compliance

* Use least‑privilege PAT/`GITHUB_TOKEN` (contents\:write for history branch; pages/id‑token as needed per README example).&#x20;
* No secrets in logs; redact tokens.
* Backoff on 403/429; timeouts on network calls (Python default in script is `timeout=20`).&#x20;

### 2.7 Error Handling & Edge Cases

* Missing `.coverage_percent` → omit that field in metrics (no failure).&#x20;
* `gocyclo` missing → skip complexity metrics (no failure).&#x20;
* Metrics/security history missing → generate pages without trends; scripts are no‑ops or write a placeholder. &#x20;

### 2.8 Observability

* JSON Lines logs at INFO; ERROR on failures; include timing for external calls and counts written (files/metrics/alerts).

### 2.9 Testing (Acceptance)

Use the **three exact tests** listed in the Copilot prompt above (same commands & outputs). Add smoke tests to ensure the two “Trends” `<div>`s exist and that the JS replaces placeholder text with chart containers. &#x20;

### 2.10 Build/Run

* Action usage: follow README example workflow (checkout → run action → upload Pages artifact → deploy Pages).&#x20;
* Local debug: run Python scripts from repo root with envs set; open `site_src/*.md` to verify.

### 2.11 Out‑of‑Scope

* Re‑theming MkDocs beyond nav ordering.
* Changing public input/output names.
* Generating full benchmark tooling beyond what README states.&#x20;
