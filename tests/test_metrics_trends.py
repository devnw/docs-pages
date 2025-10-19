import os, shutil, subprocess, tempfile
from pathlib import Path

def test_metrics_trends(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    # work in isolated copy so we don't pollute real repo
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # copy script directory minimally
        (td_path / 'scripts').mkdir()
        shutil.copy2(repo_root / 'scripts' / 'gen_metrics_md.py', td_path / 'scripts' / 'gen_metrics_md.py')
        # create metrics history
        (td_path / 'metrics' / 'data').mkdir(parents=True)
        (td_path / 'metrics' / 'summary.json').write_text('{"metrics": {"coverage": []}}')
        (td_path / 'metrics' / 'data' / 'coverage.json').write_text('[{"t":1,"v":80},{"t":2,"v":90}]')
        # run script
        subprocess.check_call(['python3', 'scripts/gen_metrics_md.py'], cwd=str(td_path))
        md_path = td_path / 'site_src' / 'metrics.md'
        assert md_path.exists()
        expected = """# Metrics\n\nProject metrics over time.\n\n<div id=\"metrics-charts\">Loading metrics history...</div>\n<script src=\"metrics/metrics.js\"></script>\n"""
        assert md_path.read_text() == expected
