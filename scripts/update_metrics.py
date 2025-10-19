#!/usr/bin/env python3
"""Maintain metrics history similar to benchmarks.

Reads current metrics.json (snapshot) and appends values to per-metric series
JSON files stored in a separate worktree branch (METRICS_BRANCH).
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path.cwd()
METRICS_BRANCH = os.environ.get('METRICS_BRANCH', 'bench-data')
TOKEN = os.environ.get('TOKEN')
WORKTREE = ROOT / 'metrics_history_wt'
SNAPSHOT = ROOT / 'site_src' / 'metrics.json'
METRICS_DIR = ROOT / 'metrics'
DATA_DIR = METRICS_DIR / 'data'
SUMMARY = METRICS_DIR / 'summary.json'


def run(cmd: list[str], check=True):
    try:
        proc = subprocess.run(cmd)
    except FileNotFoundError:
        print(f"Warning: command not found: {cmd[0]}")
        return subprocess.CompletedProcess(cmd, 0)
    if check and proc.returncode != 0:
        raise RuntimeError('command failed: ' + ' '.join(cmd))
    return proc


def main() -> int:
    if not SNAPSHOT.exists():
        return 0
    if TOKEN:
        run(['git', 'config', '--global', 'user.name', 'github-actions'], check=False)
        run(['git', 'config', '--global', 'user.email', 'github-actions@github.com'], check=False)
    ls = subprocess.run(['git', 'ls-remote', '--heads', 'origin', METRICS_BRANCH], capture_output=True, text=True)
    branch_exists = bool(ls.stdout.strip())
    created_branch = False
    if branch_exists:
        fetch_proc = subprocess.run(['git', 'fetch', 'origin', f'{METRICS_BRANCH}:{METRICS_BRANCH}'])
        if fetch_proc.returncode == 0:
            subprocess.run(['git', 'worktree', 'add', '-f', str(WORKTREE), METRICS_BRANCH])
            created_branch = True
    else:
        print(f"Info: history branch '{METRICS_BRANCH}' not found; skipping metrics history persistence.")

    METRICS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    timestamp = datetime.now(timezone.utc).isoformat()
    summary = {'generated_at': timestamp, 'metrics': []}

    for key, value in sorted(snapshot.items()):
        series_file = DATA_DIR / f'{key}.json'
        try:
            series = json.loads(series_file.read_text(encoding='utf-8')) if series_file.exists() else []
        except Exception:
            series = []
        series.append({'time': timestamp, 'value': value})
        series_file.write_text(json.dumps(series, indent=2), encoding='utf-8')
        summary['metrics'].append({'name': key, 'file': f'{key}.json'})
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    # Commit via worktree
    if created_branch and WORKTREE.exists():
        try:
            os.chdir(WORKTREE)
        except Exception:
            return 0
        target_metrics = WORKTREE / 'metrics'
        target_metrics.mkdir(exist_ok=True)
        run(['rsync', '-aL', str(METRICS_DIR) + '/', str(target_metrics) + '/'], check=False)
        run(['git', 'add', 'metrics'], check=False)
        if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode != 0:
            run(['git', 'commit', '-m', 'Update metrics history'], check=False)
            run(['git', 'push', 'origin', METRICS_BRANCH], check=False)
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
