#!/usr/bin/env python3
"""Collect GitHub security information with pagination & schema validation.

Outputs:
  site_src/security.json
  site_src/security.md

Exit codes:
  0 success
  2 schema validation failure (SCHEMA_ERROR logged)
"""
from __future__ import annotations
import json, os, pathlib, sys, time, argparse, urllib.request, urllib.error, re

ROOT = pathlib.Path.cwd()
SCHEMA = ROOT / 'schema' / 'security.schema.json'
DEFAULT_OUTPUT_DIR = ROOT / 'site_src'

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY', ''), help='Owner/repo (default from GITHUB_REPOSITORY)')
    p.add_argument('--token-env', default='GITHUB_TOKEN,TOKEN', help='Comma list env var names to look for token')
    p.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR), help='Output directory for site_src (default site_src)')
    p.add_argument('--dry-run', action='store_true', help='Fetch & print JSON only (no files written)')
    p.add_argument('--api-base', default=os.environ.get('SECURITY_API_BASE', ''), help='Override API base (tests) e.g. http://localhost:8000/repos')
    return p.parse_args()

def find_token(names: str) -> str | None:
    for n in [x.strip() for x in names.split(',') if x.strip()]:
        v = os.environ.get(n)
        if v:
            return v
    return None

def request_json(url: str, headers: dict) -> tuple[int, object | None, dict]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read().decode()
            link = r.headers.get('Link', '')
            return r.status, json.loads(data), {'link': link}
    except urllib.error.HTTPError as e:
        return e.code, None, {}
    except Exception:
        return 0, None, {}

def paginate(base_url: str, headers: dict, max_retries: int = 5, deadline_sec: int = 60) -> list[dict]:
    results: list[dict] = []
    url = base_url
    backoff = 1.0
    attempts = 0
    start = time.time()
    while url:
        if time.time() - start > deadline_sec:
            print(f"INFO: pagination deadline reached for {base_url}")
            break
        status, payload, meta = request_json(url, headers)
        if status in (403, 429):
            attempts += 1
            if attempts > max_retries:
                print(f"INFO: exceeded retry limit ({max_retries}) for {base_url} (status {status})")
                break
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
            continue
        attempts = 0  # reset on success / different status
        if not isinstance(payload, list):
            break
        results.extend(payload)
        link = meta.get('link', '')
        m = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = m.group(1) if m else None
    return results

def build_snapshot(repo: str, token: str | None, api_base: str | None = None) -> dict:
    if not repo:
        return {'severity': {}, 'code_scanning': {}, 'secret_scanning': {}}
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    api_root = api_base.rstrip('/') if api_base else 'https://api.github.com/repos'
    api = f'{api_root}/{repo}'
    sev_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    dep = paginate(api + '/dependabot/alerts?state=open&per_page=100', headers)
    for a in dep:
        level = (a.get('security_advisory') or {}).get('severity') or a.get('severity')
        if level in sev_counts:
            sev_counts[level] += 1
    code = paginate(api + '/code-scanning/alerts?state=open&per_page=100', headers)
    secret = paginate(api + '/secret-scanning/alerts?state=open&per_page=100', headers)
    return {
        'severity': sev_counts,
        'code_scanning': {'open': len(code)},
        'secret_scanning': {'open': len(secret)},
    }

def validate_schema(obj: dict) -> bool:
    try:
        schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    except Exception:
        # If schema missing treat as pass (non-fatal)
        return True
    # Minimal inline validation (no external lib allowed):
    if not isinstance(obj, dict):
        return False
    required = schema.get('required', [])
    for r in required:
        if r not in obj:
            return False
    # Basic type checks
    if not isinstance(obj.get('severity'), dict):
        return False
    for k in ['critical', 'high', 'medium', 'low']:
        if not isinstance(obj['severity'].get(k, 0), int):
            return False
    for sec_key in ['code_scanning', 'secret_scanning']:
        if not isinstance(obj.get(sec_key), dict):
            return False
        if not isinstance(obj[sec_key].get('open', 0), int):
            return False
    return True

def write_markdown(snapshot: dict, md_path: pathlib.Path):
    sev = snapshot.get('severity', {})
    color_map = {'critical': '#b60205', 'high': '#d93f0b', 'medium': '#dbab09', 'low': '#e3c907'}
    def badge(label, val, color):
        return f"<span style='display:inline-block;margin:2px;padding:2px 8px;border-radius:12px;background:{color};color:#fff;font-size:12px'>{label}: {val}</span>"
    badges = []
    if sev:
        total = sum(sev.values())
        badges.append(badge('Vulns', total, '#d73a49' if total else '#22863a'))
        for k in ['critical', 'high', 'medium', 'low']:
            v = sev.get(k, 0)
            if v:
                badges.append(badge(k.capitalize(), v, color_map[k]))
    if snapshot.get('code_scanning', {}).get('open'):
        badges.append(badge('CodeQL', snapshot['code_scanning']['open'], '#6f42c1'))
    if snapshot.get('secret_scanning', {}).get('open'):
        badges.append(badge('Secrets', snapshot['secret_scanning']['open'], '#fbca04'))
    lines = ['# Security', '', ' '.join(badges), '', '| Metric | Value |', '|--------|-------|']
    if sev:
        for k in ['critical', 'high', 'medium', 'low']:
            lines.append(f"| {k.capitalize()} Vulns | {sev.get(k,0)} |")
        lines.append(f"| Total Vulns | {sum(sev.values())} |")
    if snapshot.get('code_scanning'):
        lines.append(f"| Open Code Scanning Alerts | {snapshot['code_scanning'].get('open',0)} |")
    if snapshot.get('secret_scanning'):
        lines.append(f"| Open Secret Scanning Alerts | {snapshot['secret_scanning'].get('open',0)} |")
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

def main() -> int:
    args = parse_args()
    out_dir = pathlib.Path(args.output_dir)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    token = find_token(args.token_env)
    snapshot = build_snapshot(args.repo, token, api_base=args.api_base or None)
    if not validate_schema(snapshot):
        print('SCHEMA_ERROR: security snapshot invalid', file=sys.stderr)
        return 2
    if args.dry_run:
        print(json.dumps(snapshot, indent=2))
        return 0
    (out_dir / 'security.json').write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
    write_markdown(snapshot, out_dir / 'security.md')
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
