import json, pathlib, subprocess, sys, textwrap, os, tempfile

def run_script(tmp, env):
    proc = subprocess.run([sys.executable, str(pathlib.Path('scripts/collect_metrics.py'))], cwd=tmp, env=env, capture_output=True, text=True)
    return proc

def test_metrics_basic(tmp_path, monkeypatch):
    # Arrange repo
    (tmp_path / 'main.go').write_text('package main\nfunc main() {}\n')
    (tmp_path / 'main_test.go').write_text('package main\nimport "testing"\nfunc TestA(t *testing.T) {}\nfunc TestB(t *testing.T) {}\n')
    (tmp_path / '.coverage_percent').write_text('88.5')
    env = {**os.environ, 'METRICS': 'coverage,tests,files,loc', 'HIGH_COMPLEXITY_THRESHOLD': '10'}
    proc = subprocess.run([sys.executable, str(pathlib.Path('scripts/collect_metrics.py')), '--root', str(tmp_path), '--output-dir', str(tmp_path/'site_src'), '--metrics', 'coverage,tests,files,loc'], capture_output=True, text=True)
    assert proc.returncode == 0
    out_json = json.loads((tmp_path/'site_src'/'metrics.json').read_text())
    assert out_json == {
        'coverage_percent': 88.5,
        'test_functions': 2,
        'go_files': 2,
        'loc': 2
    }
    md = (tmp_path/'site_src'/'metrics.md').read_text()
    assert '| Coverage (%) | 88.5 |' in md
