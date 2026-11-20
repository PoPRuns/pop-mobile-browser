"""Fresh-clone and release-readiness regression checks."""
from pathlib import Path
import json
import shutil
import socket
import subprocess
import sys
import time
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


class RepositoryReadinessTests(unittest.TestCase):
    def test_fresh_clone_with_no_jar_database_starts(self):
        # The archive intentionally contains no original game JARs.
        absent = ROOT / 'definitely-not-present-game-jar-database'
        self.assertFalse(absent.exists())
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        command = [sys.executable, str(ROOT / 'server.py'), '--port', str(port), '--jar-dir', str(absent)]
        proc = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        try:
            status = None
            for _ in range(60):
                if proc.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/status', timeout=.2) as response:
                        status = json.load(response)
                    break
                except (OSError, ValueError):
                    time.sleep(.1)
            self.assertIsNotNone(status, 'The preview server did not start without a game folder')
            self.assertEqual(status['cataloguedBuilds'], 950)
            self.assertEqual(status['localJarCount'], 0)
            self.assertFalse(status['jarDirectoryFound'])
            self.assertTrue(status['emulatorReady'])
        finally:
            proc.terminate()
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=5)

    def test_removed_downloaders_and_visible_credits(self):
        server = (ROOT / 'server.py').read_text(encoding='utf8')
        library = (ROOT / 'assets/jar-library.js').read_text(encoding='utf8')
        for token in ('--enable-downloader', 'RecoveryManager', 'fetch_verified_jar', 'urllib.request'):
            self.assertNotIn(token, server)
        for token in ('fetchMirrors', 'mirrorSources'):
            self.assertNotIn(token, library)
        for html in ('index.html', 'catalogue.html'):
            source = (ROOT / html).read_text(encoding='utf8')
            self.assertIn('Built with CheerpJ', source)
            self.assertIn('href="THIRD_PARTY_NOTICES.md"', source)
        self.assertNotIn('setup-emulator.sh', (ROOT / 'README.md').read_text(encoding='utf8'))
        self.assertFalse((ROOT / 'tools/jarchive_download.py').exists())

    def test_only_one_identical_cover_file(self):
        home = (ROOT / 'assets/home.js').read_text(encoding='utf8')
        self.assertIn("'classic-two-thrones':'two-thrones.jpg'", home)
        self.assertFalse((ROOT / 'assets/covers/classic-two-thrones.jpg').exists())


if __name__ == '__main__':
    unittest.main()
