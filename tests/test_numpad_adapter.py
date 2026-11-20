"""Verifies the numpad adapter without changing/compiling upstream FreeJ2ME."""
from pathlib import Path
import subprocess
import shutil
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
from test_resolution import UPSTREAM_FIXTURE

class NumpadAdapterTests(unittest.TestCase):
    def test_injection_and_unchanged_upstream(self):
        combined=server.inject_numpad_hook(server.inject_resolution_hook(UPSTREAM_FIXTURE))
        self.assertEqual(combined.count('function popMapNumpadKey('),1)
        self.assertIn("event.data?.type !== 'pop-mobile:numpad'",combined)
        self.assertIn('const popCode = popMapNumpadKey(e)',combined)
        self.assertIn('keyRepeatManager.post(isDown, popCode',combined)
        self.assertIn('FreeJ2ME.main(args)',combined)
        self.assertIn('keyRepeatManager.post(isDown, e.code',UPSTREAM_FIXTURE)
        with self.assertRaisesRegex(ValueError,'keyboard anchor'):
            server.inject_numpad_hook('const keyRepeatManager = new KeyRepeatManager();')
    @unittest.skipUnless(shutil.which('node'),'Node.js needed only for JS unit test')
    def test_mapping_switch_and_key_release(self):
        adapter=server.EMULATOR_KEYPAD_STATE
        js=r'''
const assert=require('node:assert/strict');
let listener;
const location={origin:'http://127.0.0.1:8000'};
const parent={};
const window={parent,addEventListener(type,cb){if(type==='message')listener=cb;}};
const sp=new URLSearchParams('?numpad=phone');
'''+adapter+r'''
function event(code,type='keydown'){return {code,type};}
assert.equal(popMapNumpadKey(event('Numpad1')),'Numpad1');
assert.equal(popMapNumpadKey(event('Numpad1','keyup')),'Numpad1');
listener({source:parent,origin:location.origin,data:{type:'pop-mobile:numpad',mode:'standard'}});
assert.equal(popMapNumpadKey(event('Numpad1')),'Digit1');
assert.equal(popMapNumpadKey(event('Numpad2','keyup')),'Digit2');
assert.equal(popMapNumpadKey(event('Numpad3')),'Digit3');
assert.equal(popMapNumpadKey(event('Numpad9')),'Digit9');
assert.equal(popMapNumpadKey(event('Digit3')),'Digit3');
assert.equal(popMapNumpadKey(event('Numpad0')),'Numpad0');
// Changing modes while the key is held must not send keyup for the wrong key.
listener({source:parent,origin:location.origin,data:{type:'pop-mobile:numpad',mode:'phone'}});
assert.equal(popMapNumpadKey(event('Numpad3','keyup')),'Digit3');
assert.equal(popMapNumpadKey(event('Numpad9','keyup')),'Digit9');
assert.equal(popMapNumpadKey(event('Numpad3')),'Numpad3');
listener({source:{},origin:location.origin,data:{type:'pop-mobile:numpad',mode:'standard'}});
assert.equal(popMapNumpadKey(event('Numpad4')),'Numpad4');
listener({source:parent,origin:'https://attacker.example',data:{type:'pop-mobile:numpad',mode:'standard'}});
assert.equal(popMapNumpadKey(event('Numpad5')),'Numpad5');
console.log('keyboard event routing passed');
'''
        result=subprocess.run(['node','-e',js],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_manual_download_ui(self):
        html=(ROOT/'catalogue.html').read_text()
        app=(ROOT/'assets'/'app.js').read_text()
        self.assertIn('id="jar-index-link"',html)
        self.assertIn('id="jar-upload"',html)
        self.assertLess(html.index('id="jar-index-link"'),html.index('id="jar-upload"'))
        self.assertNotIn('id="jar-fetch"',html)
        self.assertNotIn('id="jar-recover"',html)
        self.assertIn('jarLibrary.archiveSearchLink(build)',app)
        self.assertIn('jarLibrary.storeFile(build, file)',app)
        self.assertNotIn('fetchMirrors(',app)
        self.assertIn("numpad: numpadMode",app)
        self.assertIn('localStorage.setItem(NUMPAD_SETTING_KEY',app)

if __name__=='__main__': unittest.main()
