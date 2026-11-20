"""Simple static route contract for service-worker compatibility."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class BrowserCacheRouteTest(unittest.TestCase):
    def test_server_serves_worker_from_root(self):
        source = (ROOT / 'server.py').read_text()
        self.assertIn("if path == '/sw-jar.js':", source)
        self.assertIn("self.serve_file(ROOT, 'sw-jar.js', head)", source)
        self.assertTrue((ROOT / 'sw-jar.js').is_file())

    def test_html_loads_library_before_app(self):
        html = (ROOT / 'catalogue.html').read_text()
        self.assertLess(html.index('assets/jar-library.js'), html.index('assets/app.js'))
        for control in ('jar-upload', 'jar-file-picker', 'jar-status', 'jar-index-link', 'numpad-standard'):
            self.assertIn('id="' + control + '"', html)

if __name__ == '__main__': unittest.main()
