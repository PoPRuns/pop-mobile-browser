"""Screen-size integration checks for the no-rebuild emulator bridge."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server

UPSTREAM_FIXTURE = '''const sp = new URLSearchParams(location.search);
const keyRepeatManager = new KeyRepeatManager();
function setListeners() {
    function handleKeyEvent(e) {
        const isDown = e.type === 'keydown';
        if (codeMap[e.code]) {
            keyRepeatManager.post(isDown, e.code, {
                symbol: e.key.length == 1 ? e.key.charCodeAt(0) : '\x00',
                ctrlKey: e.ctrlKey,
                shiftKey: e.shiftKey
            })
        }
        e.preventDefault();
    }
}
async function init() {
    const lib = await cheerpjRunLibrary("/app/freej2me-web.jar");
    const FreeJ2ME = await lib.org.recompile.freej2me.FreeJ2ME;
    FreeJ2ME.main(args).catch(e => {
        e.printStackTrace();
    });
}
'''


class ResolutionTests(unittest.TestCase):
    def test_injection_before_java_launch(self):
        patched = server.inject_resolution_hook(UPSTREAM_FIXTURE)
        self.assertIn('await config.saveConfig()', patched)
        self.assertIn('await LauncherUtil.ensureAppId(', patched)
        self.assertLess(patched.index('await config.saveConfig()'), patched.index('FreeJ2ME.main(args)'))
        self.assertEqual(patched.count('PoP Mobile: apply the catalogue-selected'), 1)
        self.assertEqual(UPSTREAM_FIXTURE.count('pop-mobile:'), 0)

    def test_reject_unknown_upstream_source(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported freej2me-web'):
            server.inject_resolution_hook('const FreeJ2ME = await lib.org.recompile.freej2me.FreeJ2ME;')

    def test_http_emulator_launcher_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            emulator = Path(tmp)
            (emulator / 'src').mkdir()
            script = emulator / 'src' / 'main.js'
            script.write_text(UPSTREAM_FIXTURE)
            with mock.patch.object(server, 'EMULATOR_ROOT', emulator):
                web = server.ThreadingHTTPServer(('127.0.0.1', 0), server.AppHandler)
                base = f'http://127.0.0.1:{web.server_port}'
                thread = threading.Thread(target=web.serve_forever, daemon=True)
                thread.start()
                try:
                    with urllib.request.urlopen(base + '/emulator/src/main.js') as r:
                        output = r.read().decode()
                        self.assertEqual(r.status, 200)
                        self.assertIn('no-store', r.headers.get('Cache-Control'))
                        self.assertIn('text/javascript', r.headers.get('Content-Type'))
                        self.assertIn('await config.saveConfig()', output)
                        self.assertIn('const popCode = popMapNumpadKey(e)', output)
                    # No changes are written back into the upstream checkout.
                    self.assertEqual(script.read_text(), UPSTREAM_FIXTURE)
                    with urllib.request.urlopen(urllib.request.Request(
                        base + '/emulator/src/main.js', method='HEAD')) as r:
                        self.assertEqual(r.status, 200)
                        self.assertEqual(r.read(), b'')
                    script.write_text('invalid source')
                    with self.assertRaises(urllib.error.HTTPError) as err:
                        urllib.request.urlopen(base + '/emulator/src/main.js')
                    self.assertEqual(err.exception.code, 502)
                finally:
                    web.shutdown()
                    web.server_close()
                    thread.join(timeout=3)

    @unittest.skipUnless(shutil.which('node'), 'Node.js optional: browser logic checked when available')
    def test_browser_selection_and_emulator_bridge_mocks(self):
        # Test the real browser function, not a hand-reimplemented Python algorithm.
        app = (ROOT / 'assets' / 'app.js').read_text()
        match = re.search(r'  const SCREEN_PRESETS = Object.freeze\([\s\S]*?(?=  const jarLibrary)', app)
        self.assertIsNotNone(match)
        code = match.group(0)
        runner = r'''
            const assert = require('node:assert/strict');
            const resolutions = JSON.parse(process.argv[1]);
            const catalogue = resolutions.map(s => [s, chooseEmulatorResolution(s)]);
            const expected = {
                '96x65':'96x65','90x96':'96x96','101x80':'104x80',
                '128x128':'128x128','128x140':'128x160',
                '128x151':'128x160','128x160':'128x160',
                '128x189':'176x208','176x208':'176x208','176x220':'176x220'
            };
            for (const [catalogued, chosen] of catalogue) {
                const actual = `${chosen.width}x${chosen.height}`;
                assert.equal(actual, expected[catalogued]);
                assert.ok(chosen.width >= Number(catalogued.split('x')[0]));
                assert.ok(chosen.height >= Number(catalogued.split('x')[1]));
            }
            assert.equal(chooseEmulatorResolution('bad'), null);
            assert.equal(chooseEmulatorResolution('0x0'), null);
            assert.equal(chooseEmulatorResolution('2048x8192'), null);
            console.log(JSON.stringify(catalogue));
        '''
        catalogue = json.loads((ROOT / 'data' / 'catalogue.json').read_text())
        res = sorted({build['resolution'] for build in catalogue['builds'] if build['collection'] == 'Harem Adventures' and build['resolution']})
        result = subprocess.run(['node', '-e', code + runner, json.dumps(res)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Node.js optional: browser logic checked when available')
    def test_hook_runs_with_mocked_cheerpj_java_bridge(self):
        # The hook is executed in Node against a small fake CheerpJ object graph;
        # real CheerpJ/game execution still requires the user's Firefox runtime.
        script = r'''
            const assert = require('node:assert/strict');
            let writes = [];
            let parentMessages = [];
            const window = {parent: {postMessage: (message) => parentMessages.push(message)}};
            const location = {origin:'http://127.0.0.1:8000'};
            const cheerpjWebRoot = '/app/emulator';
            class File {constructor(path) {this.path = path;} async getName(){return 'test.jar';}}
            class Config {
              constructor() {this.appSettings = {put: async (key,val) => writes.push([key,val])};}
              async init(path) {writes.push(['init',path]);}
              async saveConfig() {writes.push(['save',true]);}
            }
            const lib = {
              java:{io:{File:Promise.resolve(File)}},
              org:{recompile:{mobile:{MIDletLoader:Promise.resolve({getMIDletLoader:async()=>({getAppId:async()=> 'Prince'})})},
                 freej2me:{Config:Promise.resolve(Config)}}},
              pl:{zb3:{freej2me:{launcher:{LauncherUtil:Promise.resolve({ensureAppId:async()=>{}})}}}}
            };
            async function run() {
              const sp = new URLSearchParams('?jar=test.jar&screenWidth=128&screenHeight=160');
        '''
        script += server.EMULATOR_RESOLUTION_HOOK
        script += r'''
            }
            run().then(() => {
                assert.deepEqual(writes, [['init','./Prince'],['width','128'],['height','160'],['save',true]]);
                assert.equal(parentMessages.length,1);
                assert.equal(parentMessages[0].ok,true);
                console.log('hook completed');
            }).catch(e=>{console.error(e);process.exitCode=1});
        '''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('hook completed', result.stdout)


if __name__ == '__main__':
    unittest.main()
