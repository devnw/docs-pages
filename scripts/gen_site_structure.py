#!/usr/bin/env python3
from __future__ import annotations

import os
import pathlib
import subprocess
import shutil

ROOT = pathlib.Path.cwd()
SITE_SRC = ROOT / 'site_src'
SITE_SRC.mkdir(exist_ok=True)
REFERENCE = SITE_SRC / 'reference'
REFERENCE.mkdir(exist_ok=True)

repo = os.environ.get('GITHUB_REPOSITORY', '')
repo_name = repo.split('/', 1)[-1] if repo else ROOT.name
site_name_override = os.environ.get('SITE_NAME', '').strip()
site_name = site_name_override or f"{repo_name} — Go Package Site"
extra_docs = os.environ.get('EXTRA_DOCS', 'true').lower() == 'true'
nav_order_cfg = [p.strip().lower() for p in os.environ.get('NAV_ORDER', 'home,reference,coverage,metrics,security,bench,docs,kb,specs').split(',') if p.strip()]

readme = ROOT / 'README.md'
index_md = SITE_SRC / 'index.md'
if readme.exists():
    index_md.write_text(readme.read_text(encoding='utf-8'), encoding='utf-8')
else:
    index_md.write_text(f"# {repo_name}\n", encoding='utf-8')

zig_bin = shutil.which('zig')
zig_build_file = ROOT / 'build.zig'
zig_present = bool(zig_bin and zig_build_file.exists())

go_bin = shutil.which('go')
go_mod = ROOT / 'go.mod'
go_present = bool(go_bin)
both_langs = zig_present and go_mod.exists()

REFERENCE_GO = REFERENCE / 'go' if both_langs else REFERENCE
REFERENCE_ZIG = REFERENCE / 'zig'
if both_langs:
    REFERENCE_GO.mkdir(parents=True, exist_ok=True)

pkg_entries: list[tuple[str,str]] = []
if go_present:
    try:
        listing = subprocess.check_output([go_bin, 'list', '-f', '{{.Dir}}||{{.ImportPath}}', './...'], text=True).strip().splitlines()
        for line in listing:
            if '||' not in line:
                continue
            d, ip = line.split('||', 1)
            if '/vendor/' in d:
                continue
            pkg_entries.append((d, ip))
    except subprocess.CalledProcessError:
        pkg_entries = []

root_dir = ROOT.resolve()
links = []
if pkg_entries:
    for d, import_path in sorted(pkg_entries):
        p = pathlib.Path(d).resolve()
        try:
            rel_path = p.relative_to(root_dir)
            rel = rel_path.as_posix() or '.'
        except Exception:
            rel = os.path.relpath(p.as_posix(), root_dir.as_posix())
            if not rel or rel == '.':
                rel = '.'
            else:
                rel = rel.replace('\\', '/')
        base = REFERENCE_GO
        if rel == '.':
            outdir = base
            link_target = ('go/index.md' if both_langs else 'index.md')
        else:
            outdir = base / rel
            outdir.mkdir(parents=True, exist_ok=True)
            link_target = (f"go/{rel}/index.md" if both_langs else f"{rel}/index.md")
        idx = outdir / 'index.md'

        title = 'Root Package' if rel == '.' else f'Package {rel}'
        doc_blocks: list[str] = []
        try:
            detailed = subprocess.check_output(['go', 'doc', '-all', import_path], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            detailed = ''
        if not detailed:
            try:
                detailed = subprocess.check_output(['go', 'doc', import_path], text=True, stderr=subprocess.DEVNULL)
            except Exception:
                detailed = 'Documentation unavailable.'
        synopsis = ''
        if detailed:
            for line in detailed.splitlines():
                if line.strip():
                    synopsis = line.strip()
                    break
        import_line = f"Import path: `{import_path}`" if import_path else ''
        doc_blocks.append(f"# {title}\n")
        if import_line:
            doc_blocks.append(import_line + '\n')
        if synopsis and synopsis != 'Documentation unavailable.':
            doc_blocks.append(f"{synopsis}\n")
        doc_blocks.append('## API (raw go doc)\n')
        doc_blocks.append('```text\n')
        doc_blocks.append(detailed.rstrip() + '\n')
        doc_blocks.append('```\n')

        idx.write_text('\n'.join(doc_blocks), encoding='utf-8')
        display = 'root' if rel == '.' else rel
        links.append(f"- [{display}]({link_target})")

ref_index = (REFERENCE_GO if both_langs else REFERENCE) / 'index.md'
if ref_index.exists():
    with ref_index.open('a', encoding='utf-8') as f:
        f.write('\n## Packages\n')
        f.write('\n'.join(links) + '\n')
else:
    with ref_index.open('w', encoding='utf-8') as f:
        f.write('# Reference\n\n')
        if links:
            f.write('## Packages\n')
            f.write('\n'.join(links) + '\n')
        else:
            f.write('_No Go packages found or API docs not generated._\n')

zig_nav_target = None
if zig_present:
    try:
        subprocess.run([zig_bin, 'build', 'docs'], check=False)
    except Exception:
        pass
    candidates = [ROOT / 'zig-out' / 'docs', ROOT / 'zig-out' / 'doc', ROOT / 'docs']
    doc_src = None
    for c in candidates:
        if c.is_dir() and (c / 'index.html').exists():
            doc_src = c
            break
    dest = REFERENCE_ZIG
    dest.mkdir(parents=True, exist_ok=True)
    if doc_src:
        for child in dest.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
        shutil.copytree(doc_src, dest, dirs_exist_ok=True)
        zig_nav_target = 'reference/zig/index.html'
    else:
        (dest / 'index.md').write_text('# Zig Reference\n\n_No Zig docs were produced by the build script._\n', encoding='utf-8')
        zig_nav_target = 'reference/zig/index.md'

def copy_and_group(src: pathlib.Path, dest: pathlib.Path, title: str) -> None:
    if not src.is_dir():
        return
    try:
        subprocess.run(['rsync', '-aL', str(src) + '/', str(dest) + '/'], check=True)
    except Exception:
        for p in src.rglob('*'):
            if p.is_file():
                rel = p.relative_to(src)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    target.write_text(p.read_text(encoding='utf-8'), encoding='utf-8')
                except Exception:
                    pass
    idx = dest / 'index.md'
    groups: dict[str, list[pathlib.Path]] = {}
    top_files: list[pathlib.Path] = []
    for p in sorted(dest.rglob('*.md')):
        if p.name == 'index.md':
            continue
        rel = p.relative_to(dest)
        parts = rel.parts
        if len(parts) == 1:
            top_files.append(p)
        else:
            groups.setdefault(parts[0], []).append(p)
    lines = [f'# {title}', '']
    def display_title(md_path: pathlib.Path) -> str:
        try:
            first_line = md_path.read_text(encoding='utf-8', errors='ignore').splitlines()[:1]
            if first_line and first_line[0].startswith('#'):
                return first_line[0].lstrip('#').strip()
        except Exception:
            pass
        stem = md_path.stem
        return stem
    for p in top_files:
        rel = p.relative_to(dest).as_posix()
        lines.append(f"- [{display_title(p)}]({rel})")
    for grp, files in groups.items():
        lines += ['', f'## {grp}', '']
        for p in files:
            rel = p.relative_to(dest).as_posix()
            lines.append(f"- [{display_title(p)}]({rel})")
    if not idx.exists():
        idx.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    else:
        idx.write_text('\n'.join(lines) + '\n', encoding='utf-8')

DOCS_SRC = ROOT / 'docs'
KB_SRC = ROOT / 'kb'
SPECS_SRC = ROOT / 'specs'

docs_index_exists = False
if extra_docs and DOCS_SRC.is_dir():
    dest_docs = SITE_SRC / 'docs'
    copy_and_group(DOCS_SRC, dest_docs, 'Documentation')
    docs_index_exists = (dest_docs / 'index.md').exists()
    docs_readme_stub = dest_docs / 'README.md'
    if not docs_readme_stub.exists() and index_md.exists():
        docs_readme_stub.write_text('# README Alias\n\nThis page aliases the project root README.\n\n[View project README](../index.md)\n', encoding='utf-8')

kb_index_exists = False
if extra_docs and KB_SRC.is_dir():
    dest_kb = SITE_SRC / 'kb'
    copy_and_group(KB_SRC, dest_kb, 'KB')
    kb_index_exists = (dest_kb / 'index.md').exists()

specs_index_exists = False
if extra_docs and SPECS_SRC.is_dir():
    dest_specs = SITE_SRC / 'specs'
    copy_and_group(SPECS_SRC, dest_specs, 'Specs')
    specs_index_exists = (dest_specs / 'index.md').exists()

sections = {}
sections['home'] = '- Home: index.md'

reference_nav_lines: list[str] = []
if both_langs:
    reference_nav_lines.append('- Reference:')
    reference_nav_lines.append('    - Go: reference/go/index.md')
    if zig_nav_target:
        reference_nav_lines.append(f'    - Zig: {zig_nav_target}')
    else:
        reference_nav_lines.append('    - Zig: reference/zig/index.md')
    sections['reference'] = '\n'.join(reference_nav_lines)
else:
    if zig_present and not pkg_entries:
        if zig_nav_target:
            sections['reference'] = f'- Reference: {zig_nav_target}'
        else:
            sections['reference'] = '- Reference: reference/zig/index.md'
        if not (REFERENCE / 'index.md').exists():
            (REFERENCE / 'index.md').write_text('# Reference\n\n', encoding='utf-8')
    else:
        sections['reference'] = '- Reference: reference/index.md' if (REFERENCE / 'index.md').exists() else None

sections['coverage'] = '- Coverage: coverage.md'
sections['metrics'] = '- Metrics: metrics.md' if (SITE_SRC / 'metrics.md').exists() else None
sections['security'] = '- Security: security.md' if (SITE_SRC / 'security.md').exists() else None
sections['bench'] = '- Benchmarks: bench.md' if (SITE_SRC / 'bench.md').exists() else None
sections['docs'] = '- Docs: docs/index.md' if (extra_docs and docs_index_exists) else None
sections['kb'] = '- KB: kb/index.md' if (extra_docs and kb_index_exists) else None
sections['specs'] = '- Specs: specs/index.md' if (extra_docs and specs_index_exists) else None

nav = [sections[k] for k in nav_order_cfg if k in sections and sections[k]]

mkdocs_yml = f"""site_name: "{site_name}"
repo_url: "https://github.com/{repo}"
docs_dir: site_src
theme:
    name: material
    features:
        - navigation.top
extra_javascript:
    - extra_badges.js
markdown_extensions:
  - admonition
  - toc:
      permalink: true
nav:
""" + '\n'.join([f"  {n}" for n in nav]) + '\n'

security_json = SITE_SRC / 'security.json'
if security_json.exists():
    js = [
        "fetch('security.json').then(r=>r.json()).then(d=>{",
        "const header=document.querySelector('header.md-header__inner')||document.body; if(!header) return;",
        "function badge(label,value,color){const s=document.createElement('span');s.style.cssText='display:inline-block;margin-left:6px;padding:2px 6px;border-radius:12px;background:'+color+';color:#fff;font-size:12px;';s.textContent=label+': '+value;return s;}",
        "const sev=d.severity||{}; const total=(sev.critical||0)+(sev.high||0)+(sev.medium||0)+(sev.low||0);",
        "header.appendChild(badge('Vulns', total, total? '#d73a49':'#22863a'));",
        "if(sev.critical) header.appendChild(badge('Critical', sev.critical,'#b60205'));",
        "if(d.code_scanning && d.code_scanning.open) header.appendChild(badge('CodeQL', d.code_scanning.open,'#6f42c1'));",
        "if(d.secret_scanning && d.secret_scanning.open) header.appendChild(badge('Secrets', d.secret_scanning.open,'#fbca04'));",
        "}).catch(()=>{});"
    ]
    (SITE_SRC / 'extra_badges.js').write_text('\n'.join(js)+'\n', encoding='utf-8')
else:
    (SITE_SRC / 'extra_badges.js').write_text('// no security data\n', encoding='utf-8')

(ROOT / 'mkdocs.yml').write_text(mkdocs_yml, encoding='utf-8')
