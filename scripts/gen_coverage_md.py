#!/usr/bin/env python3
"""Wrapper script importing project coverage generator if present, else inline fallback.
Supports Go cover.out and Zig HTML coverage (zig build test -Dcoverage).
"""
from __future__ import annotations

import importlib.util
import pathlib
import os
import sys
import re

ROOT = pathlib.Path.cwd()
SCRIPT = ROOT / '.github' / 'scripts' / 'gen_coverage_md.py'
EMBED = (os.environ.get('EMBED_COVERAGE', 'true').lower() == 'true')

if SCRIPT.exists():
    spec = importlib.util.spec_from_file_location('gen_coverage_md_local', SCRIPT)
    if spec and spec.loader:  # pragma: no branch
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[arg-type]
        sys.exit(0)

site_src = ROOT / 'site_src'
site_src.mkdir(exist_ok=True)
cover_profile = ROOT / 'cover.out'
cover_html = ROOT / 'cover.html'
zig_cov_dir_candidates = [site_src / 'zig_coverage', ROOT / 'zig-out' / 'coverage', ROOT / 'zig-out' / 'coverage_html']
md = site_src / 'coverage.md'

rows = []
overall = None
per_file_available = False

def parse_go_cover() -> tuple[list[tuple[str,int,int,float]], float] | tuple[None, None]:
    if not cover_profile.exists():
        return None, None
    totals = {}
    try:
        with cover_profile.open(encoding='utf-8') as f:
            first = f.readline()
            if not first.startswith('mode:'):
                raise ValueError('invalid header')
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    loc_part, stmts_s, count_s = line.rsplit(' ', 2)
                    file_path = loc_part.split(':', 1)[0]
                    stmts = int(stmts_s)
                    cnt = int(count_s)
                except Exception:
                    continue
                rec = totals.setdefault(file_path, {'stmts': 0, 'covered': 0})
                rec['stmts'] += stmts
                if cnt > 0:
                    rec['covered'] += stmts
    except Exception:
        return None, None
    rows = []
    total_stmts = total_cov = 0
    for fp, rec in sorted(totals.items()):
        s = rec['stmts']; c = rec['covered']; pct = (c / s * 100) if s else 0.0
        rows.append((fp, s, c, pct))
        total_stmts += s; total_cov += c
    overall = (total_cov / total_stmts * 100) if total_stmts else 0.0
    return rows, overall


def find_zig_cov_dir() -> pathlib.Path | None:
    for d in zig_cov_dir_candidates:
        if d.is_dir() and (d / 'index.html').exists():
            return d
    return None


def extract_zig_percent(index_html: str) -> float | None:
    # Heuristics: look for a percent near a Total row
    # Try common patterns
    patterns = [
        r'Total[^%]{0,200}([0-9]+(?:\.[0-9]+)?)%'
    ]
    for pat in patterns:
        m = re.search(pat, index_html, flags=re.I|re.S)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    # Fallback: first percentage in file
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)%', index_html)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None

# Compute Go coverage if available
rows, overall = parse_go_cover()
per_file_available = bool(rows)

parts = ['# Coverage Report', '']

if overall is not None:
    parts.append(f'Overall Go statements coverage: **{overall:.2f}%**')
    parts.append('')
    if cover_html.exists():
        parts.append('[Open full Go coverage report](cover.html)')
    if EMBED and cover_html.exists():
        parts += ['', '<details><summary>Embedded Go coverage (HTML)</summary>', '<iframe src="cover.html" style="width:100%;height:70vh;border:0" title="Go Coverage"></iframe>', '</details>']

# Zig coverage section
zig_cov_dir = find_zig_cov_dir()
if zig_cov_dir:
    try:
        idx = (zig_cov_dir / 'index.html').read_text(encoding='utf-8', errors='ignore')
    except Exception:
        idx = ''
    zig_pct = extract_zig_percent(idx) if idx else None
    parts += ['', '## Zig Coverage', '']
    if zig_pct is not None:
        parts.append(f'Overall Zig coverage: **{zig_pct:.2f}%**')
    rel = zig_cov_dir.relative_to(site_src) if zig_cov_dir.is_relative_to(site_src) else pathlib.Path('reference/zig/index.html')
    # If coverage dir is under site_src (preferred), link directly
    if (site_src / rel).exists():
        parts.append(f'[Open full Zig coverage report]({rel.as_posix()}/index.html)')
        if EMBED:
            parts += ['', '<details><summary>Embedded Zig coverage (HTML)</summary>', f'<iframe src="{rel.as_posix()}/index.html" style="width:100%;height:70vh;border:0" title="Zig Coverage"></iframe>', '</details>']
    else:
        # Fallback generic link if copied under reference/zig
        parts.append('[Open Zig docs/coverage](reference/zig/index.html)')

# Per-file table for Go
if per_file_available:
    def color(p: float) -> str:
        return '#d9534f' if p < 50 else '#f0ad4e' if p < 70 else '#5bc0de' if p < 80 else '#5cb85c'
    def bar(p: float) -> str:
        return f'<div style="background:#eee;border:1px solid #ccc;width:120px;height:10px"><div style="background:{color(p)};height:100%;width:{p:.2f}%"></div></div>'
    table = ['| File | Stmts | Covered | % | Graph |', '|------|-------|---------|----|-------|']
    for fp, s, c, pct in rows:
        table.append(f'| `{fp}` | {s} | {c} | {pct:.2f}% | {bar(pct)} |')
    parts += ['', '## Per-file Go Coverage', '', *table]

if not per_file_available and not zig_cov_dir:
    parts = ['# Coverage Report', '', 'No coverage profile produced.', '']

parts += ['', '_Auto-generated by action._']
md.write_text('\n'.join([p for p in parts if p is not None]), encoding='utf-8')
