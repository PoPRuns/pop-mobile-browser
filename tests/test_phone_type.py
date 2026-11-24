"""Workbook phone hints and per-build phone selection through the shared hook."""
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server
from tools import import_pop_workbook as importer


class PhoneTypeTests(unittest.TestCase):
    def test_device_classifier(self):
        cases = {
            'Nokia Series 60': 'Nokia',
            'Nokia C3-00 and Nokia E71': 'Nokia',
            'SIEMENS handset (model unverified)': 'Siemens',
            'Motorola RAZR V3': 'Motorola',
            'Sony Ericsson T610': 'SonyEricsson',
            'SonyEricsson K800i': 'SonyEricsson',
            'Sony-Ericsson W810i': 'SonyEricsson',
            'Samsung SGH-F480': None,
            'LG KU990': None,
            'LG U880, SonyEricsson K700, K750i': None,
            'Samsung SGH-F480 and Nokia C2-03': None,
            'SonyEricsson SATIO, U5i Vivaz, Nokia 5800 Xpress Music': None,
            'Nokia and Alcatel': None,
            'Nokia and Motorola': None,
            'Nokia and Sony': None,
            'notnokia': None,
            '-': None,
            '': None,
            None: None,
        }
        for device, expected in cases.items():
            with self.subTest(device=device):
                self.assertEqual(importer.classify_device(device), expected)

    @unittest.skipUnless(shutil.which('node'), 'Node.js required for bridge mock')
    def test_launcher_and_per_build_overrides(self):
        app = (ROOT / 'assets/app.js').read_text()
        code = re.search(r"    if \(Object.prototype.hasOwnProperty.call\(build, 'phoneType'\)\) \{[\s\S]*?\n    }", app).group(0)
        script = r'''
            const assert = require('node:assert/strict');
            function paramsFor(build) {
                const params = new URLSearchParams();
        ''' + code + r'''
                return params;
            }
            assert.equal(paramsFor({phoneType:'Siemens'}).get('phoneType'), 'Siemens');
            assert.equal(paramsFor({phoneType:null}).get('phoneType'), 'Nokia');
            assert.equal(paramsFor({phoneType:'invalid'}).get('phoneType'), 'Nokia');
            assert.equal(paramsFor({}).has('phoneType'), false);

            const A = 'a'.repeat(64), B = 'b'.repeat(64), C = 'c'.repeat(64);
            const phoneKey = sha => 'pop-mobile-phone-v1:' + sha;
            const sizeKey = sha => 'pop-mobile-resolution-v1:' + sha;
            const values = new Map();
            let blocked = false, wrap = false, reloads = 0;
            const localStorage = {
                getItem(k){if(blocked) throw Error('blocked');return values.get(k) ?? null;},
                setItem(k,v){if(blocked) throw Error('blocked');values.set(k,v);}
            };
            const location = {href:'',origin:'http://localhost:8000',reload(){reloads++;}};
            const history = {replaceState(a,b,url){location.href=url;}};
            const window = {parent:{postMessage(){}}};
            // Deliberately use one shared config for all three JARs.
            let disk = {phone:'Motorola',width:'128',height:'128',sound:'on'};
            let saves = 0;
            class File { constructor(path){this.path=path;} async getName(){return 'game.jar';} }
            class Config {
                async init(){this.data={...disk};this.appSettings={
                    put:async(k,v)=>{this.data[k]=v;},
                    get:async(k)=>wrap?{toString:async()=>this.data[k]}:this.data[k]
                };}
                async getWidth(){return Number(this.data.width);}
                async getHeight(){return Number(this.data.height);}
                async saveConfig(){disk={...this.data};saves++;}
            }
            const lib = {java:{io:{File}},org:{recompile:{mobile:{MIDletLoader:{
                getMIDletLoader:async()=>({getAppId:async()=> 'Prince'})}},freej2me:{Config}}},
                pl:{zb3:{freej2me:{launcher:{LauncherUtil:{ensureAppId:async()=>{}}}}}}};
            async function launch(sha, phone, url, width=128, height=128) {
                const next=new URL('http://localhost:8000/emulator/run.html');
                next.searchParams.set('jar',sha+'.jar');
                if(phone!==null)next.searchParams.set('phoneType',phone);
                if(width)next.searchParams.set('screenWidth',String(width));
                if(height)next.searchParams.set('screenHeight',String(height));
                location.href=url||next.href;
                const sp=new URL(location.href).searchParams;
                const args=['jar','/str/'+sha+'.jar'];
        ''' + server.EMULATOR_RESOLUTION_HOOK + r'''
            }
            async function restart() {
                const sp = new URL(location.href).searchParams;
                const natives = {
        ''' + server.EMULATOR_RESTART_REPLACEMENT + r'''
                };
                await natives.Java_pl_zb3_freej2me_bridge_shell_Shell_restart();
            }
            async function run() {
                await launch(A,'Siemens'); assert.equal(disk.phone,'Siemens');
                assert.equal(values.has(phoneKey(A)),false);
                await restart(); await launch(A,'Siemens',location.href);
                assert.equal(values.has(phoneKey(A)),false);
                disk.phone='Standard'; disk.width='96'; disk.height='96';
                await restart(); wrap=true;
                await launch(A,'Siemens',location.href); wrap=false;
                assert.equal(values.get(phoneKey(A)),'Standard');
                assert.deepEqual(JSON.parse(values.get(sizeKey(A))),{width:96,height:96});
                assert.equal(new URL(location.href).searchParams.has('popNativeRestart'),false);
                await launch(B,'Nokia'); assert.equal(disk.phone,'Nokia');
                assert.equal(disk.width,'128');
                await launch(A,'Siemens'); assert.equal(disk.phone,'Standard');
                assert.equal(disk.width,'96');
                await launch(B,'Nokia'); assert.equal(disk.phone,'Nokia');
                values.set(phoneKey(B),'bogus'); await launch(B,'Nokia');
                assert.equal(disk.phone,'Nokia');
                await launch(C,'SonyEricsson',undefined,0,0);
                assert.equal(disk.phone,'SonyEricsson');
                assert.equal(disk.sound,'on');
                const before=saves;
                await launch(C,null,undefined,0,0); assert.equal(saves,before);
                assert.equal(disk.phone,'SonyEricsson');
                blocked=true; await launch(A,'Siemens'); assert.equal(disk.phone,'Siemens');
                disk.phone='Motorola'; await restart();
                await launch(A,'Siemens',location.href);
                assert.equal(new URL(location.href).searchParams.get('phoneType'),'Motorola');
                assert.equal(disk.phone,'Motorola');
                assert.equal(reloads,3);
            }
            run().catch(e=>{console.error(e);process.exitCode=1;});
        '''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
