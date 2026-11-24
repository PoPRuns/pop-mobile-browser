"""Playback reports use the labeled GitHub form and preserve per-build metadata."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PlaybackIssueReportingTests(unittest.TestCase):
    def test_labeled_form_and_fallback_url(self):
        form = (ROOT / '.github/ISSUE_TEMPLATE/broken-game.yml').read_text(encoding='utf-8')
        self.assertIn("labels: ['broken-game']", form)
        self.assertIn('id: jar_build_details', form)
        self.assertIn('id: what_went_wrong', form)
        self.assertIn('id: expected_behavior', form)
        html = (ROOT / 'catalogue.html').read_text(encoding='utf-8')
        self.assertIn('href="https://github.com/PoPRuns/pop-mobile-browser/issues/new?template=broken-game.yml"', html)

    def test_report_url_preserves_build_details(self):
        script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/app.js', 'utf8');
const start = source.indexOf('  function playerIssueUrl(');
const end = source.indexOf('  function loadPlayerOnce(', start);
assert.ok(start !== -1 && end > start);
const context = {
  URL,
  state: {currentGame: {title: 'Prince of Persia: Warrior Within'}},
  fmtBytes: n => `${(n / 1024).toFixed(1)} KB`,
  playerResolution: () => ({width: 130, height: 130})
};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const testBuild = {
  game: 'warrior-within', name: 'PrinceWW',
  sourceFilenames: 'PrinceWW (Gameloft).jar', vendor: 'Gameloft',
  version: '1.0', size: 123456, language: 'English',
  resolution: '130x130', fpsLimit: 15,
  sha256: 'abcdef1234567890'.repeat(4)
};
const url = new URL(vm.runInContext(
  'playerIssueUrl(' + JSON.stringify(testBuild) + ', {width: 208, height: 208})', context));
assert.equal(url.origin, 'https://github.com');
assert.equal(url.searchParams.get('template'), 'broken-game.yml');
assert.equal(url.searchParams.get('title'), '[Playback] Prince of Persia: Warrior Within: PrinceWW');
assert.equal(url.searchParams.has('body'), false);
const metadata = url.searchParams.get('jar_build_details');
for (const expected of [
    'PrinceWW (Gameloft).jar', 'Vendor: Gameloft', 'Version: 1.0',
    'Catalogued screen: 130x130', 'Emulator screen: 208x208',
    'FPS limit: 15', testBuild.sha256,
    'catalogue.html?game=warrior-within&sha256=' + testBuild.sha256
]) assert.ok(metadata.includes(expected), expected);
console.log('Playback issue URL and metadata OK');
"""
        subprocess.run(['node', '-e', script], cwd=ROOT, check=True)

if __name__ == '__main__':
    unittest.main()
