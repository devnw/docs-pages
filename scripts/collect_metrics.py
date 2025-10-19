#!/usr/bin/env python3
"""Collect repository metrics and write metrics.json + metrics.md with schema validation.

Env / Flags (flags override env):
    METRICS / --metrics (comma list)
    HIGH_COMPLEXITY_THRESHOLD / --high-complexity-threshold
    --root (default CWD)
    --output-dir (default site_src)

Exit codes:
    0 success
    2 schema validation failure (SCHEMA_ERROR)
"""
from __future__ import annotations

import json, os, pathlib, re, subprocess, argparse, sys
from typing import Dict, Any

SCHEMA = pathlib.Path('schema/metrics.schema.json')

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument('--metrics', default=os.environ.get('METRICS', ''), help='Comma list of metrics to collect')
    p.add_argument('--high-complexity-threshold', type=int, default=int(os.environ.get('HIGH_COMPLEXITY_THRESHOLD', '10')))
    p.add_argument('--root', default='.', help='Project root (default .)')
    p.add_argument('--output-dir', default='site_src', help='Output directory (default site_src)')
    return p.parse_args()

def validate_schema(data: dict) -> bool:
    try:
        schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    except Exception:
        return True  # no schema => skip
    if not isinstance(data, dict):
        return False
    for k, v in data.items():
        if k.endswith('_percent') and not isinstance(v, (int, float)):
            return False
        if k in ('test_functions', 'go_files', 'loc', 'high_complexity_functions') and not isinstance(v, int):
            return False
        if k == 'avg_cyclomatic_complexity' and not isinstance(v, (int, float)):
            return False
    return True

def main() -> int:
    args = parse_args()
    ROOT = pathlib.Path(args.root).resolve()
    SITE_SRC = pathlib.Path(args.output_dir)
    SITE_SRC.mkdir(parents=True, exist_ok=True)
    selected = {m.strip() for m in args.metrics.split(',') if m.strip()}
    threshold = args.high_complexity_threshold

    metrics: Dict[str, Any] = {}

    def run(cmd):
        try:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ''

    if 'coverage' in selected:
        cov_path = ROOT / '.coverage_percent'
        if cov_path.exists():
            try:
                metrics['coverage_percent'] = float(cov_path.read_text().strip())
            except Exception:
                pass
        zig_cov_idx = SITE_SRC / 'zig_coverage' / 'index.html'
        if zig_cov_idx.exists():
            try:
                import re as _re
                html = zig_cov_idx.read_text(encoding='utf-8', errors='ignore')
                m = _re.search(r'Total[^%]{0,200}([0-9]+(?:\.[0-9]+)?)%', html, flags=_re.I|_re.S)
                if m:
                    metrics['zig_coverage_percent'] = float(m.group(1))
            except Exception:
                pass

    go_files = []
    for p in ROOT.rglob('*.go'):
        posix = p.as_posix()
        if '/vendor/' in posix or posix.startswith('vendor/'):
            continue
        go_files.append(p)

    if 'files' in selected:
        metrics['go_files'] = len(go_files)

    if 'tests' in selected:
        test_funcs = 0
        func_re = re.compile(r'^func\s+Test[^(]+\(')
        for p in go_files:
            if p.name.endswith('_test.go'):
                try:
                    for line in p.read_text(encoding='utf-8').splitlines():
                        if func_re.match(line):
                            test_funcs += 1
                except Exception:
                    continue
        metrics['test_functions'] = test_funcs

    if 'loc' in selected:
        loc = 0
        for p in go_files:
            if p.name.endswith('_test.go'):
                continue
            try:
                for line in p.read_text(encoding='utf-8').splitlines():
                    if line.strip():
                        loc += 1
            except Exception:
                continue
        metrics['loc'] = loc

    if 'avg_complexity' in selected or 'high_complexity' in selected:
        if run(['bash', '-c', 'command -v gocyclo || true']):
            out = run(['gocyclo', *[p.as_posix() for p in go_files]])
            if out:
                scores = []
                high = 0
                for line in out.splitlines():
                    parts = line.split()
                    if not parts:
                        continue
                    try:
                        val = float(parts[0])
                    except ValueError:
                        continue
                    scores.append(val)
                    if val > threshold:
                        high += 1
                if scores and 'avg_complexity' in selected:
                    metrics['avg_cyclomatic_complexity'] = round(sum(scores)/len(scores), 2)
                if 'high_complexity' in selected:
                    metrics['high_complexity_functions'] = high

    if not validate_schema(metrics):
        print('SCHEMA_ERROR: metrics snapshot invalid', file=sys.stderr)
        return 2

    metrics_json = SITE_SRC / 'metrics.json'
    metrics_json.write_text(json.dumps(metrics, indent=2) + '\n', encoding='utf-8')

    table_lines = [
        '# Project Metrics',
        '',
        '| Metric | Value |',
        '|--------|-------|',
    ]
    display_order = [
        ('coverage_percent', 'Coverage (%)'),
        ('zig_coverage_percent', 'Zig Coverage (%)'),
        ('test_functions', 'Test Functions'),
        ('go_files', 'Go Files'),
        ('loc', 'Lines of Code (non-test)'),
        ('avg_cyclomatic_complexity', 'Avg Cyclomatic Complexity'),
        ('high_complexity_functions', f'Functions > {threshold} Complexity'),
    ]
    for key, label in display_order:
        if key in metrics:
            table_lines.append(f'| {label} | {metrics[key]} |')

    (SITE_SRC / 'metrics.md').write_text('\n'.join(table_lines) + '\n', encoding='utf-8')
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
