#!/usr/bin/env python3
"""Simplified benchmark history updater for standalone action.

Expects bench.out already produced in CWD.
Stores JSON time series in a dedicated branch (BENCH_BRANCH), but this script
assumes caller has fetched repository and has auth.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

BENCH_BRANCH = os.environ.get('BENCH_BRANCH', 'bench-data')
TOKEN = os.environ.get('TOKEN')

ROOT = pathlib.Path.cwd()
WORKTREE = ROOT / 'bench_history_wt'
DATA_DIR = ROOT / 'bench'
OUT_SERIES = DATA_DIR / 'data'
SUMMARY = DATA_DIR / 'summary.json'
BENCH_OUT = ROOT / 'bench.out'


def run(cmd: list[str], check=True, capture=False):
    kwargs = {}
    if capture:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['text'] = True
    try:
        proc = subprocess.run(cmd, **kwargs)
    except FileNotFoundError:
        print(f"Warning: command not found: {cmd[0]}")
        return subprocess.CompletedProcess(cmd, 0, '', '') if capture else subprocess.CompletedProcess(cmd, 0)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return proc


def parse_bench() -> dict[str, dict[str, float]]:
    if not BENCH_OUT.exists():
        return {}
    results: dict[str, dict[str, float]] = {}
    for line in BENCH_OUT.read_text(encoding='utf-8').splitlines():
        if not line.startswith('Benchmark'):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        name = parts[0]
        rec: dict[str, float] = {}
        for i, tok in enumerate(parts):
            if tok in ('ns/op', 'B/op', 'allocs/op') and i > 0:
                try:
                    val = float(parts[i-1])
                except ValueError:
                    continue
                if tok == 'ns/op':
                    rec['ns_per_op'] = val
                elif tok == 'B/op':
                    rec['bytes_per_op'] = val
                elif tok == 'allocs/op':
                    rec['allocs_per_op'] = val
        if rec:
            results[name] = rec
    return results


def main() -> int:
    if TOKEN:
        run(['git', 'config', '--global', 'user.name', 'github-actions'])
        run(['git', 'config', '--global', 'user.email', 'github-actions@github.com'])
    # Detect remote branch existence and prepare worktree
    ls = run(['git', 'ls-remote', '--heads', 'origin', BENCH_BRANCH], check=False, capture=True)
    branch_exists = bool((ls.stdout or '').strip()) if hasattr(ls, 'stdout') else False
    created_branch = False
    if branch_exists:
        fetch_proc = run(['git', 'fetch', 'origin', f'{BENCH_BRANCH}:{BENCH_BRANCH}'], check=False, capture=True)
        if fetch_proc.returncode == 0:
            created_branch = True
            run(['git', 'worktree', 'add', '-f', str(WORKTREE), BENCH_BRANCH], check=False)
    else:
        print(f"Info: history branch '{BENCH_BRANCH}' not found; skipping benchmark history persistence.")

    DATA_DIR.mkdir(exist_ok=True)
    OUT_SERIES.mkdir(parents=True, exist_ok=True)

    # Pre-load previous history locally if available via worktree
    if created_branch and WORKTREE.exists():
        prev = WORKTREE / 'bench'
        if prev.exists():
            try:
                run(['rsync', '-aL', str(prev) + '/', str(DATA_DIR) + '/'], check=False)
            except Exception:
                pass

    parsed = parse_bench()
    if not parsed:
        return 0

    timestamp = datetime.now(timezone.utc).isoformat()
    summary = {'generated_at': timestamp, 'benchmarks': []}
    for name, rec in sorted(parsed.items()):
        file_safe = name.replace('/', '_') + '.json'
        series_file = OUT_SERIES / file_safe
        series = []
        if series_file.exists():
            try:
                series = json.loads(series_file.read_text(encoding='utf-8'))
            except Exception:
                series = []
        entry = {'time': timestamp, **rec}
        series.append(entry)
        series_file.write_text(json.dumps(series, indent=2), encoding='utf-8')
        summary['benchmarks'].append({'name': name, 'file': file_safe})
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    # Commit changes in worktree if any
    if created_branch and WORKTREE.exists():
        try:
            os.chdir(WORKTREE)
        except Exception:
            return 0
        target_bench = WORKTREE / 'bench'
        target_bench.mkdir(exist_ok=True)
        run(['rsync', '-aL', str(DATA_DIR) + '/', str(target_bench) + '/'], check=False)
        run(['git', 'add', 'bench'], check=False)
        if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode != 0:
            run(['git', 'commit', '-m', 'Update benchmark history'], check=False)
            run(['git', 'push', 'origin', BENCH_BRANCH], check=False)
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
