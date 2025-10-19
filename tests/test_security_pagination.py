import json, os, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess

# Simple mock server to emulate GitHub paginated responses
DATA_DEPENDABOT = [
    {'severity': 'critical'},
    {'severity': 'high'},
]
DATA_DEPENDABOT_2 = [
    {'severity': 'low'},
]
DATA_CODE = [{}, {}]
DATA_SECRET = [{}]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/repos/acme/x/dependabot/alerts'):
            if 'page=2' in self.path:
                body = json.dumps(DATA_DEPENDABOT_2)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body.encode())
            else:
                body = json.dumps(DATA_DEPENDABOT)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Link', '<http://localhost:8001/repos/acme/x/dependabot/alerts?page=2>; rel="next"')
                self.end_headers()
                self.wfile.write(body.encode())
        elif self.path.startswith('/repos/acme/x/code-scanning/alerts'):
            body = json.dumps(DATA_CODE)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path.startswith('/repos/acme/x/secret-scanning/alerts'):
            body = json.dumps(DATA_SECRET)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def run_server():
    httpd = HTTPServer(('localhost', 8001), Handler)
    httpd.serve_forever()


def test_security_pagination(tmp_path, monkeypatch):
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.2)

    env = os.environ.copy()
    env['GITHUB_REPOSITORY'] = 'acme/x'
    env['GITHUB_TOKEN'] = 'test'
    env['SECURITY_API_BASE'] = 'http://localhost:8001/repos'

    # Run script
    subprocess.check_call(['python3', 'scripts/collect_security.py'], env=env, cwd=str(Path(__file__).resolve().parents[1]))

    data = json.loads(Path('site_src/security.json').read_text())
    assert data == {
        "severity": {"critical": 1, "high": 1, "medium": 0, "low": 1},
        "code_scanning": {"open": 2},
        "secret_scanning": {"open": 1}
    }
