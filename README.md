# go-docs-bench-coverage Action

Composite GitHub Action that:

1. Runs Go tests with coverage (atomic) and generates cover.html
2. Produces a markdown coverage summary (overall + per-file table)
3. Optionally runs benchmarks and maintains a JSON history branch
4. Generates package reference docs by embedding `go doc -all` output per package (markdown, no external HTML dependency)
5. Builds a MkDocs Material site (README as home, reference, coverage, benchmarks, docs/)
6. Uploads a Pages artifact (caller workflow still deploys)

## What’s included

This action is now a composite action that installs its own prerequisites:

- Node.js 20 (to run the generator)
- Go (stable), plus optional tools:
  - gocyclo (complexity) — installed via `go install`
- Python 3.x and pip packages:
  - mkdocs, mkdocs-material
- rsync (for history and doc copying if available)

You no longer need to pre-install these in your workflow.

## Inputs

| Input               | Default                            | Description                              |
| ------------------- | ---------------------------------- | ---------------------------------------- |
| github_token        | (required)                         | Token with contents: write permissions   |
| run_benchmarks      | true                               | Run benchmarks & update history          |
| bench_branch        | bench-data                         | Branch storing JSON benchmark history    |
| site_name           | (derived)                          | Override site title                      |
| extra_nav_docs      | true                               | Include docs/ in nav                     |
| nav_order           | home,reference,coverage,bench,docs | Custom nav ordering                      |
| embed_coverage_html | true                               | Embed cover.html iframe in coverage page |
| fail_on_test_failure | false                              | Fail action if Go tests fail             |

## Outputs

| Output           | Description                         |
| ---------------- | ----------------------------------- |
| site_dir         | Built site directory path           |
| coverage_percent | Overall statements coverage percent |

## Example Usage

```yaml
name: docs
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Generate site
        id: docs
        uses: devnw/doc-pages@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ${{ steps.docs.outputs.site_dir }}
      - name: Deploy Pages
        uses: actions/deploy-pages@v4
```

To enable benchmark history persistence ensure the branch (default `bench-data`) exists or the action can create it via a push using the provided token.

## Notes

- The action still runs the Node-based generator internally (`dist/index.js`).
- It installs tools only when missing; failures to install optional tools don’t fail the job.
- Nav ordering skips absent sections automatically.
- Large repositories may wish to scope benchmarks with custom inputs (future enhancement).

## Script CLI Flags

Python helper scripts now expose non-breaking CLI flags (env vars still work):

`collect_metrics.py`

- `--metrics` (comma list) mirrors `METRICS` env (e.g. coverage,tests,files,loc,complexity)
- `--high-complexity-threshold` mirrors `HIGH_COMPLEXITY_THRESHOLD` (default 10)
- `--root` repo root (auto-detected normally)
- `--output-dir` target site directory (default `site_src`)

`collect_security.py`

- `--repo` override `GITHUB_REPOSITORY`
- `--token-env` ordered env var search list (default `GITHUB_TOKEN,TOKEN`)
- `--output-dir` as above
- `--dry-run` prints JSON only (no writes)
- `--api-base` internal/testing override of API root (defaults to GitHub API). Can also set `SECURITY_API_BASE` env.

`gen_metrics_md.py` / `gen_security_md.py`

- Auto-detect history (`metrics/` or `security/`) and ensure a Trends section with a container div + JS asset.

## JSON Schema Validation

Snapshots are validated against JSON schemas in `schema/`. Failures:

- Logged with level `ERROR` and code `SCHEMA_ERROR`
- Exit with code 2 (distinct from other failures)

## Troubleshooting

| Symptom | Cause | Resolution |
| ------- | ----- | ---------- |
| Missing reference docs | `go doc` invocation failed | Ensure Go toolchain (Go) is installed and on PATH |
| No complexity column | `gocyclo` not installed | Install `gocyclo` (`go install github.com/fzipp/gocyclo/cmd/gocyclo@latest`) |
| Security snapshot empty | Repo private without proper token scopes | Provide a token with `security_events: read` or use default GITHUB_TOKEN with proper permissions |
| Pagination not aggregating | Custom self-hosted GitHub or test harness | Use `--api-base` or `SECURITY_API_BASE` to point scripts at the correct root |
| Schema validation exit 2 | Output shape mismatch | Inspect logged JSON, update scripts or schemas accordingly |
| Benchmarks page missing previously | (Historical) no placeholder | Now always generated even without data |
| Go tests fail and action stops | Non-zero exit aborted earlier version | Action now logs a warning and continues building site |
| Need raw test output | Test summaries lost | See `site_src/tests.txt` for persisted test output |
| History (bench/metrics) not updating | History branch absent | Create branch (default `bench-data`) or ignore; action now skips silently |

## Testing

Node tests (charts rendering):

```bash
npm test
```

Python tests (metrics, security, trends, pagination):

```bash
pytest -q
```

Install Python dev deps locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Design Rationale (Concise)

1. Composite action for deterministic dependency bootstrap without pre-steps.
2. Lightweight inline JSON schema validation (no external deps) for fast fail & deterministic output.
3. Pagination + exponential backoff hardens security data collection against rate limits.
4. CLI flags mirror env vars for local dev ergonomics without breaking action defaults.
5. Placeholder generation guarantees stable MkDocs nav (no 404 links) regardless of optional tools.
6. Separation of snapshot (JSON) and presentation (MD + JS) simplifies testing & future asset changes.
7. Exit code stratification (2 for schema errors) enables precise workflow gating.

## License

All new additions (schemas, tests) follow the existing repository license. If contributing external schema changes ensure compatibility with the project license.
