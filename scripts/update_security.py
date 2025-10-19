#!/usr/bin/env python3
"""Append security snapshot to history (per-metric series) on metrics branch."""
from __future__ import annotations
import json, os, pathlib, subprocess
from datetime import datetime, timezone
ROOT=pathlib.Path.cwd()
SNAP=ROOT/'site_src'/'security.json'
BRANCH=os.environ.get('METRICS_BRANCH','bench-data')
TOKEN=os.environ.get('TOKEN')
WORKTREE=ROOT/'security_history_wt'
SEC_DIR=ROOT/'security'
DATA_DIR=SEC_DIR/'data'
SUMMARY=SEC_DIR/'summary.json'

def run(cmd):
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print(f"Warning: command not found: {cmd[0]}")

def main()->int:
    if not SNAP.exists(): return 0
    if TOKEN:
        run(['git','config','--global','user.name','github-actions'])
        run(['git','config','--global','user.email','github-actions@github.com'])
    run(['git','fetch','origin', f'{BRANCH}:{BRANCH}'])
    run(['git','worktree','add','-f', str(WORKTREE), BRANCH])
    SEC_DIR.mkdir(exist_ok=True); DATA_DIR.mkdir(parents=True, exist_ok=True)
    snap=json.loads(SNAP.read_text())
    ts=datetime.now(timezone.utc).isoformat()
    summary={'generated_at':ts,'metrics':[]}
    flat={}
    sev=snap.get('severity',{})
    for k,v in sev.items(): flat[f'severity_{k}']=v
    flat['total_vulns']=sum(sev.values()) if sev else 0
    if snap.get('code_scanning'): flat['code_scanning_open']=snap['code_scanning'].get('open',0)
    if snap.get('secret_scanning'): flat['secret_scanning_open']=snap['secret_scanning'].get('open',0)
    for key,value in sorted(flat.items()):
        f=DATA_DIR/f'{key}.json'
        try: series=json.loads(f.read_text()) if f.exists() else []
        except Exception: series=[]
        series.append({'time':ts,'value':value})
        f.write_text(json.dumps(series, indent=2))
        summary['metrics'].append({'name':key,'file':f'{key}.json'})
    SUMMARY.write_text(json.dumps(summary, indent=2))
    import os as _os; _os.chdir(WORKTREE)
    t=WORKTREE/'security'; t.mkdir(exist_ok=True)
    run(['rsync','-aL', str(SEC_DIR)+'/', str(t)+'/'])
    run(['git','add','security'])
    if subprocess.run(['git','diff','--cached','--quiet']).returncode!=0:
        run(['git','commit','-m','Update security history'])
        run(['git','push','origin', BRANCH])
    return 0
if __name__=='__main__': raise SystemExit(main())
