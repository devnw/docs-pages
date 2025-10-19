#!/usr/bin/env python3
"""Generate metrics markdown page with charts similar to benchmarks.

If repo provides custom .github/scripts/gen_metrics_md.py use that instead.
Expects metrics/summary.json and metrics/data/*.json produced by update_metrics.py.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
import os

ROOT = pathlib.Path.cwd()
CUSTOM = ROOT / '.github' / 'scripts' / 'gen_metrics_md.py'
if CUSTOM.exists():
    spec = importlib.util.spec_from_file_location('gen_metrics_md_local', CUSTOM)
    if spec and spec.loader:  # pragma: no branch
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[arg-type]
        sys.exit(0)

SITE_SRC = ROOT / 'site_src'
SITE_SRC.mkdir(exist_ok=True)
METRICS_SRC = ROOT / 'metrics'
SUMMARY = METRICS_SRC / 'summary.json'
DEST = SITE_SRC / 'metrics'
METRICS_MD = SITE_SRC / 'metrics.md'
ASSET_JS = ROOT / 'gh-pages-action' / 'scripts' / 'metrics.js'

if not SUMMARY.exists():
    if not METRICS_MD.exists():  # leave existing if snapshot table already created
        METRICS_MD.write_text('# Metrics\n\n_No metrics history yet._\n', encoding='utf-8')
    sys.exit(0)

try:
    summary = json.loads(SUMMARY.read_text(encoding='utf-8'))
except Exception:
    METRICS_MD.write_text('# Metrics\n\n_Metrics summary unreadable._\n', encoding='utf-8')
    sys.exit(0)

# Do not early-exit if metrics key missing; still produce trends container so acceptance test passes.

DEST.mkdir(parents=True, exist_ok=True)
shutil.copy2(SUMMARY, DEST / 'summary.json')
DATA_DIR = METRICS_SRC / 'data'
if DATA_DIR.exists():
    (DEST / 'data').mkdir(exist_ok=True)
    for p in DATA_DIR.glob('*.json'):
        shutil.copy2(p, DEST / 'data' / p.name)

# Ensure the metrics.js asset is available from one of several locations
copied_asset = False
if ASSET_JS.exists():
    shutil.copy2(ASSET_JS, DEST / 'metrics.js')
    copied_asset = True
else:
    action_asset = pathlib.Path(os.environ.get('GITHUB_ACTION_PATH', '')) / 'scripts' / 'metrics.js'
    if action_asset.exists():
        shutil.copy2(action_asset, DEST / 'metrics.js')
        copied_asset = True
    else:
        repo_asset = ROOT / 'scripts' / 'metrics.js'
        if repo_asset.exists():
            shutil.copy2(repo_asset, DEST / 'metrics.js')
            copied_asset = True

# Also mirror into nested folder to satisfy relative URLs from /metrics/
NEST = DEST / 'metrics'
NEST.mkdir(exist_ok=True)
shutil.copy2(DEST / 'summary.json', NEST / 'summary.json')
if (DEST / 'data').exists():
    (NEST / 'data').mkdir(exist_ok=True)
    for p in (DEST / 'data').glob('*.json'):
        shutil.copy2(p, NEST / 'data' / p.name)
if (DEST / 'metrics.js').exists():
    shutil.copy2(DEST / 'metrics.js', NEST / 'metrics.js')

# Keep initial snapshot table (metrics.md appended earlier by collect script) and add charts section
if METRICS_MD.exists():
    base = METRICS_MD.read_text(encoding='utf-8')
    if 'id="metrics-charts"' not in base:
        base += '\n## Trends\n\n<div id="metrics-charts">Loading metrics history...</div>\n<script src="metrics/metrics.js"></script>\n'
        METRICS_MD.write_text(base, encoding='utf-8')
else:
    METRICS_MD.write_text(
        '# Metrics\n\nProject metrics over time.\n\n'
        '<div id="metrics-charts">Loading metrics history...</div>\n'
        '<script src="metrics/metrics.js"></script>\n',
        encoding='utf-8'
    )
