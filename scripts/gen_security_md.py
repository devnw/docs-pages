#!/usr/bin/env python3
"""Append trends section for security if history present."""
from __future__ import annotations
import json, pathlib, shutil, os
ROOT=pathlib.Path.cwd(); SITE=ROOT/'site_src'; SEC_SRC=ROOT/'security'
SUMMARY=SEC_SRC/'summary.json'; DEST=SITE/'security'; SEC_MD=SITE/'security.md'
ASSET=ROOT/'gh-pages-action'/'scripts'/'security.js'
if not SUMMARY.exists(): raise SystemExit(0)
try: summary=json.loads(SUMMARY.read_text())
except Exception: raise SystemExit(0)
DEST.mkdir(parents=True, exist_ok=True)
shutil.copy2(SUMMARY, DEST/'summary.json')
DATA=SEC_SRC/'data'
if DATA.exists():
    (DEST/'data').mkdir(exist_ok=True)
    for p in DATA.glob('*.json'): shutil.copy2(p, DEST/'data'/p.name)
# Try repository asset path, else fall back to action bundle path
copied=False
if ASSET.exists():
    shutil.copy2(ASSET, DEST/'security.js'); copied=True
else:
    action_asset = pathlib.Path(os.environ.get('GITHUB_ACTION_PATH',''))/'scripts'/'security.js'
    if action_asset.exists():
        shutil.copy2(action_asset, DEST/'security.js'); copied=True
    else:
        repo_asset = ROOT/'scripts'/'security.js'
        if repo_asset.exists():
            shutil.copy2(repo_asset, DEST/'security.js'); copied=True
content = SEC_MD.read_text() if SEC_MD.exists() else '# Security\n\n'
if 'id="security-charts"' not in content:
    content += '\n## Trends\n\n<div id="security-charts">Loading security history...</div>\n<script src="security/security.js"></script>\n'
SEC_MD.write_text(content)
