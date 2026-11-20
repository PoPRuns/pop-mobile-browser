"""Local-only, SHA-verified preview-server behavior."""
import hashlib
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = server.AppHandler
        handler.builds = server.load_builds()
        handler.jar_source = 'local'
        handler.local_jars = {}
        handler.scan_stats = {'filesScanned': 0, 'unknownFiles': 0, 'duplicates': 0}
        handler.jar_dir = ROOT / 'not-installed-test-dir'
        cls.web = server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.url = 'http://127.0.0.1:' + str(cls.web.server_port)
        cls.thread = threading.Thread(target=cls.web.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.web.shutdown()
        cls.web.server_close()
        cls.thread.join(timeout=3)

    def test_serves_home_catalogue_and_public_credits(self):
        with urllib.request.urlopen(self.url + '/') as r:
            self.assertEqual(r.status, 200)
            html = r.read().decode('utf-8')
            self.assertIn('id="game-grid"', html)
            self.assertIn('>Source code</a>', html)
            self.assertIn('Prince of Persia · Java Mobile Game Archive', html)
            self.assertIn('href="https://github.com/PoPRuns/pop-mobile-browser" target="_blank"', html)
            self.assertIn('NOT AFFILIATED WITH UBISOFT OR GAMELOFT', html)
            self.assertNotIn('Many kingdoms', html)
            self.assertNotIn('id="approach"', html)
        with urllib.request.urlopen(self.url + '/data/catalogue.json') as r:
            self.assertEqual(len(json.load(r)['builds']), 950)
        with urllib.request.urlopen(self.url + '/THIRD_PARTY_NOTICES.md') as r:
            self.assertEqual(r.status, 200)
            self.assertIn(b'CheerpJ', r.read())
        with urllib.request.urlopen(self.url + '/LICENSE') as r:
            self.assertIn(b'GNU GENERAL PUBLIC LICENSE', r.read())

    def test_range_and_head(self):
        req = urllib.request.Request(self.url + '/assets/app.js', headers={'Range': 'bytes=0-3'})
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 206)
            self.assertEqual(len(r.read()), 4)
            self.assertEqual(r.headers.get('Accept-Ranges'), 'bytes')
        with urllib.request.urlopen(urllib.request.Request(self.url + '/assets/site.css', method='HEAD')) as r:
            self.assertEqual(r.status, 200)
            self.assertTrue(int(r.headers['Content-Length']) > 1000)

    def test_safe_routes_and_removed_downloader(self):
        with urllib.request.urlopen(self.url + '/api/status') as r:
            status = json.load(r)
            self.assertIn('emulatorReady', status)
            self.assertEqual(status['jarSource'], 'local')
            self.assertEqual(status['localJarCount'], 0)
            self.assertFalse(status['jarDirectoryFound'])
            self.assertNotIn('downloaderReady', status)
        unknown = '0' * 64
        for suffix in ('/emulator/jar/' + unknown + '.jar', '/server.py', '/api/recover/' + unknown):
            with self.subTest(suffix=suffix), self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(self.url + suffix)
            self.assertEqual(ctx.exception.code, 404)
        req = urllib.request.Request(self.url + '/api/recover/' + unknown, method='POST')
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 501, 'No command-invoking POST endpoint is installed')

    def test_unmatched_known_hash_gives_manual_import_guidance(self):
        sha = next(iter(server.AppHandler.builds))
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self.url + '/emulator/jar/' + sha + '.jar')
        self.assertEqual(ctx.exception.code, 404)
        self.assertIn(b'Choose JAR file', ctx.exception.read())

    def test_local_scan_matches_nested_renamed_jars_by_sha256(self):
        payload = b'PK\x03\x04sample mobile JAR bytes'
        sha = hashlib.sha256(payload).hexdigest()
        build = {'sha256': sha, 'size': len(payload), 'urls': []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'some nested folder').mkdir()
            jar = root / 'some nested folder' / 'unexpected-filename.JAR'
            jar.write_bytes(payload)
            (root / 'other.jar').write_bytes(b'PK\x03\x04not a known JAR')
            matches, stats = server.index_local_jars(root, {sha: build})
            self.assertEqual(matches, {sha: jar})
            self.assertEqual(stats['filesScanned'], 2)
            self.assertEqual(stats['unknownFiles'], 1)
            self.assertEqual(server.load_verified_local_jar(build, jar), payload)
            jar.write_bytes(b'PK\x03\x04modified file content')
            with self.assertRaises(ValueError):
                server.load_verified_local_jar(build, jar)

    def test_local_only_jar_endpoint_verifies_before_serving(self):
        payload = b'PK\x03\x04testable local jar data'
        sha = hashlib.sha256(payload).hexdigest()
        other = 'f' * 64
        if sha == other:
            other = 'e' * 64
        build = {'sha256': sha, 'size': len(payload), 'urls': []}
        missing = {'sha256': other, 'size': len(payload), 'urls': []}
        handler = server.AppHandler
        original = handler.builds, handler.local_jars, handler.jar_dir, handler.scan_stats
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                jar = root / 'not-named-after-sha.jar'
                jar.write_bytes(payload)
                handler.builds = {sha: build, other: missing}
                handler.jar_dir = root
                handler.local_jars, handler.scan_stats = server.index_local_jars(root, handler.builds)
                with urllib.request.urlopen(self.url + '/api/status') as r:
                    status = json.load(r)
                    self.assertEqual(status['localJarCount'], 1)
                    self.assertEqual(status['localJarHashes'], [sha])
                req = urllib.request.Request(self.url + '/emulator/jar/' + sha + '.jar',
                                             headers={'Range': 'bytes=0-3'})
                with urllib.request.urlopen(req) as r:
                    self.assertEqual(r.status, 206)
                    self.assertEqual(r.read(), payload[:4])
                    self.assertEqual(r.headers['Content-Range'], f'bytes 0-3/{len(payload)}')
                with urllib.request.urlopen(urllib.request.Request(
                        self.url + '/emulator/jar/' + sha + '.jar', method='HEAD')) as r:
                    self.assertEqual(r.status, 200)
                    self.assertEqual(int(r.headers['Content-Length']), len(payload))
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(self.url + '/emulator/jar/' + other + '.jar')
                self.assertEqual(ctx.exception.code, 404)
                jar.write_bytes(b'PK\x03\x04wrong replacement')
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(self.url + '/emulator/jar/' + sha + '.jar')
                self.assertEqual(ctx.exception.code, 409)
        finally:
            handler.builds, handler.local_jars, handler.jar_dir, handler.scan_stats = original

    def test_range_parser(self):
        self.assertEqual(server.parse_byte_range('bytes=10-19', 100), (10, 19))
        self.assertEqual(server.parse_byte_range('bytes=-5', 100), (95, 99))
        self.assertEqual(server.parse_byte_range('bytes=10-', 100), (10, 99))
        with self.assertRaises(ValueError):
            server.parse_byte_range('bytes=120-', 100)


if __name__ == '__main__':
    unittest.main()
