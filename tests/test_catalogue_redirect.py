"""Exercise the actual catalogue startup script with a minimal browser stub."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Node.js is required for browser-script checks')
class CatalogueRedirectTests(unittest.TestCase):
    def test_unknown_collection_redirects_without_masking_load_errors(self):
        subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/app.js', 'utf8');
const data = JSON.parse(fs.readFileSync('data/catalogue.json', 'utf8'));
function expectedCount(game) {
  // Unplayable builds are hidden until the visitor opts to show them.
  const visible = data.builds.filter(b => b.game === game.id && !b.unplayable);
  const families = (data.families || []).filter(f =>
    f.game === game.id && visible.some(b => b.family === f.id));
  if (game.id === 'harem-adventures' && families.length) {
    // The family overview deliberately has no build-count heading.
    return '';
  }
  return `SHOWING ${visible.length} JAR BUILDS`;
}
async function run(url, response = {ok:true, json:async()=>data}) {
  const nodes = new Map();
  const get = id => {
    if (!nodes.has(id)) nodes.set(id, {value:'', textContent:'', innerHTML:'',
      addEventListener(){}, append(){}, replaceChildren(){this.innerHTML='';}, querySelector(){return null;}});
    return nodes.get(id);
  };
  const parsed = new URL(url);
  const redirects = [];
  let workerCalls = 0;
  const classes = new Set();
  const document = {body:{classList:{
      toggle(name, enabled){ if (enabled) classes.add(name); else classes.delete(name); },
      contains(name){ return classes.has(name); }
    }}, getElementById:get, querySelector(){return null;},
    createElement:()=>({}), addEventListener(){}, baseURI:url};
  const window = {PoPJarLibrary:{ensureWorker(){workerCalls++;return Promise.resolve();}}, addEventListener(){}};
  const location = {href:url, search:parsed.search, hash:parsed.hash, origin:parsed.origin,
    replace:dest=>redirects.push(dest)};
  vm.runInNewContext(source, {document, window, location, URL, URLSearchParams,
    localStorage:{getItem(){return null;},setItem(){}}, console,
    fetch:async path=>path==='data/catalogue.json'?response:{ok:false}});
  await new Promise(resolve=>setImmediate(resolve));
  return {redirects, count:get('result-count').textContent, workerCalls,
    familyOverview:classes.has('family-overview-mode')};
}
(async()=>{
  for (const root of ['https://popruns.github.io/pop-mobile-browser/', 'http://localhost:8000/']) {
    for (const query of ['?game=harem-adventuress','?game=','?game=unknown&sha256=123#group/foo']) {
      const result = await run(root+'catalogue.html'+query);
      assert.deepEqual(result.redirects,[root+'index.html']);
      assert.equal(result.workerCalls,0);
      assert.equal(result.count,'');
    }
    for (const game of data.games) {
      const result = await run(root+'catalogue.html?game='+encodeURIComponent(game.id));
      assert.deepEqual(result.redirects,[]);
      assert.equal(result.count,expectedCount(game));
      assert.equal(result.familyOverview,
        game.id === 'harem-adventures' && (data.families || []).some(f => f.game === game.id));
      assert.equal(result.workerCalls,1);
    }
    const defaultGame = await run(root+'catalogue.html');
    assert.equal(defaultGame.count,expectedCount(data.games.find(g => g.id === 'harem-adventures')));
    assert.equal(defaultGame.familyOverview,true);
    assert.deepEqual(defaultGame.redirects,[]);
    const failure = await run(root+'catalogue.html?game=unknown',{ok:false,status:503});
    assert.equal(failure.count,'COULD NOT LOAD CATALOGUE');
    assert.deepEqual(failure.redirects,[]);
    const invalid = await run(root+'catalogue.html?game=unknown',{ok:true,json:async()=>({})});
    assert.equal(invalid.count,'COULD NOT LOAD CATALOGUE');
    assert.deepEqual(invalid.redirects,[]);
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
'''], cwd=ROOT, check=True)
