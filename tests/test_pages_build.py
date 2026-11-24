"""Static Pages artifact: project subpath, source adapters, and no game JARs."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_pages import build_site

class PagesBuildTests(unittest.TestCase):
    def test_static_site(self):
        with tempfile.TemporaryDirectory() as temp:
            site = build_site(Path(temp) / 'pop-mobile-browser')
            self.assertTrue((site / 'index.html').is_file())
            self.assertTrue((site / '.nojekyll').exists())
            self.assertTrue((site / 'sw-jar.js').exists())
            self.assertTrue((site / 'emulator/freej2me-web.jar').is_file())
            html = (site / 'catalogue.html').read_text()
            self.assertIn('name="pop-mobile-static"', html)
            self.assertIn('assets/app.js?v=pages-playback-form-1', html)
            main = (site / 'emulator/src/main.js').read_text()
            upstream = (ROOT / 'vendor/freej2me-web/web/src/main.js').read_text()
            self.assertNotIn('popMapNumpadKey(', upstream)
            self.assertIn('popMapNumpadKey(', main)
            self.assertIn('await config.saveConfig()', main)
            self.assertIn('cheerpOSAddStringFile(path, bytes)', main)
            self.assertIn('await new File(args[1])', main)
            self.assertFalse((site / 'server.py').exists())
            self.assertFalse((site / 'tools').exists())
            self.assertFalse((site / 'docs').exists())
            self.assertTrue((site / 'THIRD_PARTY_NOTICES.md').is_file())
            self.assertFalse((site / '.git').exists())
            self.assertEqual([x for x in site.rglob('*.jar')], [site / 'emulator/freej2me-web.jar'])
            self.assertIn('pop-mobile:resolution', main)
            self.assertIn("next.searchParams.set('popNativeRestart', '1')", main)
            self.assertIn('...popFpsNatives', main)
            self.assertIn('src/main.js?v=family-fps-1', (site / 'emulator/run.html').read_text())
            for html_name in ('index.html','catalogue.html'):
                self.assertIn('Built with CheerpJ', (site / html_name).read_text())

if __name__ == '__main__': unittest.main()
