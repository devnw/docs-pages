#!/usr/bin/env python3
"""Generate benchmark markdown page with charts.

If repository provides .github/scripts/gen_bench_md.py we defer to it.
Else we build a page using bench/summary.json and bench/data/*.json produced by update_bench.py.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path.cwd()
CUSTOM = ROOT / '.github' / 'scripts' / 'gen_bench_md.py'
if CUSTOM.exists():
    spec = importlib.util.spec_from_file_location('gen_bench_md_local', CUSTOM)
    if spec and spec.loader:  # pragma: no branch
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[arg-type]
        sys.exit(0)

SITE_SRC = ROOT / 'site_src'
SITE_SRC.mkdir(exist_ok=True)
BENCH_SRC = ROOT / 'bench'
SUMMARY = BENCH_SRC / 'summary.json'
DEST = SITE_SRC / 'bench'
BENCH_MD = SITE_SRC / 'bench.md'
ASSET_JS = ROOT / 'gh-pages-action' / 'scripts' / 'bench.js'
ALT_JS = ROOT / 'scripts' / 'bench.js'

if not SUMMARY.exists():
    BENCH_MD.write_text('# Benchmarks\n\n_No benchmark history yet._\n', encoding='utf-8')
    # Ensure a destination dir exists for consistency
    DEST.mkdir(parents=True, exist_ok=True)
    # No summary/data to copy; page exists so nav can show it
    sys.exit(0)

try:
    summary = json.loads(SUMMARY.read_text(encoding='utf-8'))
    if not summary.get('benchmarks'):
        BENCH_MD.write_text('# Benchmarks\n\n_Benchmark summary empty._\n', encoding='utf-8')
        sys.exit(0)
except Exception:
    BENCH_MD.write_text('# Benchmarks\n\n_Benchmark summary unreadable._\n', encoding='utf-8')
    sys.exit(0)

DEST.mkdir(parents=True, exist_ok=True)
shutil.copy2(SUMMARY, DEST / 'summary.json')
DATA_DIR = BENCH_SRC / 'data'
if DATA_DIR.exists():
    (DEST / 'data').mkdir(exist_ok=True)
    for p in DATA_DIR.glob('*.json'):
        shutil.copy2(p, DEST / 'data' / p.name)
if ASSET_JS.exists():
    shutil.copy2(ASSET_JS, DEST / 'bench.js')
elif ALT_JS.exists():
    shutil.copy2(ALT_JS, DEST / 'bench.js')
else:
    bench_js = (
        "(function(){"
        "var root=document.getElementById('bench-charts'); if(!root) return;"
        "fetch('bench/summary.json').then(function(r){return r.json();}).then(function(s){"
        "var list=document.createElement('div');"
        "(s.benchmarks||[]).forEach(function(b){var div=document.createElement('div'); div.className='bench-chart'; div.innerHTML='<h4>'+b.name+'</h4><canvas width=240 height=60></canvas>'; list.appendChild(div); fetch('bench/data/'+b.file).then(function(r){return r.json();}).then(function(series){"
        "var c=div.querySelector('canvas'); var ctx=c.getContext('2d'); var w=c.width,h=c.height;"
        "var pts=series.map(function(s){return {t:new Date(s.time), v:s.ns_per_op||0};}); if(!pts.length) return;"
        "var min=Math.min.apply(null, pts.map(function(p){return p.v;})); var max=Math.max.apply(null, pts.map(function(p){return p.v;}));"
        "ctx.strokeStyle='#2f81f7'; ctx.lineWidth=2; ctx.beginPath(); for(var i=0;i<pts.length;i++){var x=(i/(pts.length-1))*(w-10)+5; var y=h-5-((max===min?0.5:(pts[i].v-min)/(max-min))*(h-10)); if(i){ctx.lineTo(x,y);}else{ctx.moveTo(x,y);}} ctx.stroke(); ctx.fillStyle='#555'; ctx.font='10px sans-serif'; ctx.fillText(min.toFixed(2),4,h-2); ctx.fillText(max.toFixed(2),4,10);"
        "}).catch(function(){});});"
        "root.innerHTML=''; root.appendChild(list);"
        "}).catch(function(){root.textContent='Failed to load benchmark history.';});"
        "})();"
    )
    (DEST / 'bench.js').write_text(bench_js + '\n', encoding='utf-8')

BENCH_MD.write_text(
    '# Benchmarks\n\nBenchmark performance over time.\n\n'
    '[summary.json](bench/summary.json)\n\n'
    '<div id="bench-charts">Loading benchmark history...</div>\n'
    '<script src="bench/bench.js"></script>\n',
    encoding='utf-8'
)
