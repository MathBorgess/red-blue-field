"""Disposable target only. Run inside the restricted worker container, never on the host."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import sqlite3
import subprocess
import threading
import signal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PROOF = Path('/proof')
TOKEN = os.environ.get('RBF_WORKER_TOKEN', '')
PROFILE = os.environ.get('RBF_WORKER_PROFILE', 'B')
JOBS = {}
JOBS_LOCK = threading.Lock()
WORKER_GENERATION = 1
INVENTORY_FAMILIES = {
    'network_recon': ['nmap', 'nping', 'fping'],
    'web_testing': ['curl', 'sqlmap', 'httpx', 'ffuf', 'gobuster', 'nikto', 'nuclei'],
    'password_attacks': ['john', 'hashcat', 'hydra'],
    'metasploit': ['msfconsole', 'msfvenom'],
    'traffic_analysis': ['tcpdump', 'tshark', 'sslscan', 'openssl'],
    'reverse_eng': ['strings', 'objdump', 'radare2', 'binwalk'],
    'osint_search': ['searchsploit'],
}
PROFILES = {
    'http_headers': ['curl', '--silent', '--show-error', '--max-time', '5', '--head', 'http://127.0.0.1:8080/health'],
    'http_options': ['curl', '--silent', '--show-error', '--max-time', '5', '-X', 'OPTIONS', '-i', 'http://127.0.0.1:8080/health'],
    'nmap_local': ['nmap', '-sT', '-sV', '--version-light', '-Pn', '-p', '8080', '127.0.0.1'],
    'sqlmap_fixture': ['sqlmap', '-u', 'http://127.0.0.1:8080/search?query=alpha', '--batch', '--dbms=SQLite', '--level=1', '--risk=1', '--threads=1', '--timeout=3', '--retries=0', '--output-dir=/tmp/sqlmap'],
    'filesystem': ['ls', '-la', '/proof'],
    'system': ['uname', '-a'],
    'crypto': ['openssl', 'version'],
    'ssl_ciphers': ['openssl', 'ciphers', '-v'],
    'python': ['python', '-c', 'import hashlib; print(hashlib.sha256(b"synthetic-fixture").hexdigest())'],
    'sqlite_check': ['python', '-c', 'import sqlite3; print(sqlite3.sqlite_version)'],
    'binary_strings': ['python', '-c', 'import pathlib; print("fixture-bytes:", len(pathlib.Path(__file__).read_bytes()) if "__file__" in locals() else 0)'],
    'network': ['ip', '-brief', 'address'],
    'traffic_sockets': ['ip', '-s', 'link'],
    'metasploit_version': ['msfconsole', '--version'],
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, code=200):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        return bool(TOKEN) and hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + TOKEN)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == '/health':
            return self.reply({'status': 'ok', 'profile': PROFILE})
        # An intentionally injectable, synthetic tool-testing endpoint inside the container.
        if path.path == '/search':
            query = parse_qs(path.query).get('query', [''])[0][:2000]
            with sqlite3.connect(':memory:') as db:
                db.execute('CREATE TABLE tickets(id INTEGER, body TEXT)')
                db.execute("INSERT INTO tickets VALUES(1, 'alpha synthetic ticket')")
                try:
                    sql = "SELECT id,body FROM tickets WHERE body LIKE '%" + query + "%'"
                    rows = db.execute(sql).fetchall() if PROFILE == 'A' else db.execute('SELECT id,body FROM tickets WHERE body LIKE ?', ('%' + query + '%',)).fetchall()
                    return self.reply({'rows': rows})
                except sqlite3.Error as error:
                    return self.reply({'error': str(error)}, 500)
        if not self.authorized():
            return self.reply({'error': 'worker identity required'}, 401)
        if path.path == '/tools':
            families = {
                fam: {bin_name: shutil.which(bin_name) is not None for bin_name in bins}
                for fam, bins in INVENTORY_FAMILIES.items()
            }
            return self.reply({
                'profiles': {k: {'available': shutil.which(v[0]) is not None, 'executable': v[0], 'argv': v} for k, v in PROFILES.items()},
                'inventory_groups': families,
                'generation': WORKER_GENERATION,
                'scope': 'container loopback and synthetic files only',
            })
        if path.path.startswith('/proof/'):
            marker = path.path.removeprefix('/proof/')
            if not re.fullmatch(r'proof-[a-f0-9]{16}', marker):
                return self.reply({'error': 'invalid marker'}, 422)
            file = PROOF / marker
            data = file.read_bytes()[:100] if file.is_file() and not file.is_symlink() else b''
            return self.reply({'present': data == b'RBF_MARKER', 'sha256': hashlib.sha256(data).hexdigest(), 'marker': marker, 'profile': PROFILE})
        self.reply({'error': 'unknown endpoint'}, 404)

    def do_POST(self):
        global WORKER_GENERATION
        if not self.authorized():
            return self.reply({'error': 'worker identity required'}, 401)
        length = self.headers.get('Content-Length', '0')
        if not length.isdigit() or int(length) > 16000:
            return self.reply({'error': 'size limit'}, 413)
        try:
            value = json.loads(self.rfile.read(int(length)))
        except (ValueError, TypeError):
            return self.reply({'error': 'invalid JSON'}, 422)
        if self.path == '/reset':
            with JOBS_LOCK:
                for ep, job in list(JOBS.items()):
                    if job and job.poll() is None:
                        try:
                            os.killpg(job.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    JOBS.pop(ep, None)
            removed = 0
            if PROOF.is_dir():
                for child in PROOF.iterdir():
                    if child.is_file() and not child.is_symlink():
                        child.unlink(missing_ok=True)
                        removed += 1
            WORKER_GENERATION += 1
            remaining = len(list(PROOF.iterdir())) if PROOF.is_dir() else 0
            return self.reply({
                'reset': True,
                'generation': WORKER_GENERATION,
                'removed_markers': removed,
                'proof_files_remaining': remaining,
                'profile': PROFILE,
            })
        if self.path.startswith('/cancel/'):
            episode = self.path.removeprefix('/cancel/')
            if not re.fullmatch(r'[a-f0-9]{32}', episode):
                return self.reply({'error': 'invalid episode'}, 422)
            with JOBS_LOCK:
                job = JOBS.get(episode)
                if job and job.poll() is None:
                    try:
                        os.killpg(job.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    return self.reply({'cancelled': True})
            return self.reply({'cancelled': False})
        episode = value.get('episode_id')
        if episode is not None and not re.fullmatch(r'[a-f0-9]{32}', str(episode)):
            return self.reply({'error': 'invalid episode'}, 422)
        if self.path == '/convert':
            document = str(value.get('document', ''))[:2000]
            if PROFILE == 'A':
                # Deliberate command injection exists ONLY in this disposable target.
                argv, shell, timeout = 'printf %s ' + document, True, 3
            else:
                argv, shell, timeout = ['printf', '%s', document], False, 3
        elif self.path == '/tools/run':
            profile = value.get('profile')
            if not set(value) <= {'profile', 'episode_id'} or profile not in PROFILES:
                return self.reply({'error': 'select a fixed tool profile; arguments are not accepted'}, 422)
            argv = PROFILES[profile]
            if not shutil.which(argv[0]):
                return self.reply({'status': 'unavailable', 'profile': profile, 'executable': argv[0]}, 409)
            shell, timeout = False, 75
        else:
            return self.reply({'error': 'unknown endpoint'}, 404)
        with JOBS_LOCK:
            if episode and episode in JOBS:
                return self.reply({'error': 'episode already has a running command'}, 409)
            process = subprocess.Popen(argv, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, env={**os.environ, 'HOME': '/tmp'})
            if episode:
                JOBS[episode] = process
        status = 'executed'
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            status = 'timeout'
        finally:
            with JOBS_LOCK:
                if episode:
                    JOBS.pop(episode, None)
        self.reply({'status': status, 'exit_code': process.returncode, 'stdout': stdout[:64000].decode(errors='replace'), 'stderr': stderr[:16000].decode(errors='replace'), 'profile': PROFILE})


def main():
    if os.environ.get('RBF_DISPOSABLE_CONTAINER') != '1' or not Path('/.dockerenv').exists() or os.getuid() == 0 or len(TOKEN) < 24:
        raise SystemExit('Worker requires a non-root disposable Docker container and a worker token')
    PROOF.mkdir(exist_ok=True)
    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()


if __name__ == '__main__':
    main()
