/* Node test harness: verifies manual import, SHA checks, cache and service-worker ranges. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const path = require('node:path');
const base = path.join(__dirname, '..');
const entries = new Map();
const requestKey = req => (req.url || req).split('?')[0];
const cache = {
  async put(req, response) { entries.set(requestKey(req), response.clone()); },
  async match(req) { return entries.get(requestKey(req))?.clone(); },
  async delete(req) { return entries.delete(requestKey(req)); }
};
const memoryCaches = {async open() {return cache;}};
const listeners = {};
const origin = 'http://localhost:8000/';
// A first visit or Ctrl+Shift+R force refresh can have a null controller.
// The new iframe still needs only an active service worker at the site scope.
const activeWorker = {scriptURL:'http://localhost:8000/sw-jar.js'};
const navigator = {serviceWorker:{controller: null, async register(){return {active:activeWorker,scope:origin}}, ready:Promise.resolve({active:activeWorker,scope:origin})}};
const context = {URL, Request, Response, Blob, Headers, Uint8Array, ArrayBuffer, crypto:crypto.webcrypto,
  setTimeout, clearTimeout, navigator, caches:memoryCaches,
  document:{baseURI:origin}, window:{caches:memoryCaches},
};
context.window.PoPJarLibrary = null;
context.self = {
  registration:{scope:origin},
  skipWaiting: async()=>{}, clients:{claim: async()=>{}},
  addEventListener:(kind,cb)=>{listeners[kind]=cb}
};
context.fetch = async ()=>{ throw new Error('Network fallback should not be used'); };
vm.runInNewContext(fs.readFileSync(path.join(base,'assets/jar-library.js'),'utf8'), context);
vm.runInNewContext(fs.readFileSync(path.join(base,'sw-jar.js'),'utf8'), context);
(async()=>{
  const lib=context.window.PoPJarLibrary;
  assert.equal(await lib.ensureWorker(), true, 'active worker must be accepted even without a page controller');
  const archiveHash = 'a'.repeat(64);
  assert.equal(lib.archiveSearchLink({sha256:archiveHash}),
    'https://toca-1.github.io/new-j2me-software-archive-search/?sha256='+archiveHash);
  assert.equal(typeof lib.fetchMirrors, 'undefined', 'No automatic mirror-fetching API');
  assert.equal(typeof lib.mirrorSources, 'undefined', 'No mirror candidate-generation API');
  const bytes=Buffer.from('PK\x03\x04fake archive content for test','binary');
  const build={sha256:crypto.createHash('sha256').update(bytes).digest('hex'), size:bytes.length};
  const ab = Uint8Array.from(bytes).buffer;
  await assert.rejects(lib.storeBytes({...build,sha256:'f'.repeat(64)},ab), /SHA-256 mismatch/);
  assert.equal(entries.size,0,'bad JAR must not be cached');
  await assert.rejects(lib.storeBytes({...build,size:bytes.length+1},ab), /Wrong file size/);
  await lib.storeBytes(build,ab);
  assert.equal(await lib.cached(build),true);
  const request = new Request(new URL('emulator/jar/'+build.sha256+'.jar',origin));
  // Reject a Cache Storage entry with valid-looking metadata but truncated bytes.
  await cache.put(request, new Response(Buffer.from('PK\x03\x04wrong', 'binary'), {headers: {
    'X-PoP-Verified-SHA256':build.sha256, 'X-PoP-JAR-Size':String(build.size)
  }}));
  assert.equal(await lib.cached(build),false,'wrong cached byte length must not start emulator');
  await lib.storeBytes(build,ab);
  assert.equal(await lib.cached(build),true);
  // A local server JAR can be probed with HEAD; a browser-cached JAR should
  // NOT take this path because the parent page can be uncontrolled by the SW.
  let localProbeCount = 0;
  context.fetch = async request => {
    localProbeCount++;
    assert.equal(request.method, 'HEAD');
    return new Response(null,{status:200,headers:{'Content-Length':String(build.size)}});
  };
  assert.equal((await lib.reachableLocal(build)).ok,true);
  assert.equal(localProbeCount,1);
  context.fetch = async()=>new Response(null,{status:404});
  assert.equal((await lib.reachableLocal(build)).ok,false);
  assert.equal((await lib.reachableLocal(build)).reason, 'HTTP 404');
  context.fetch = async()=>{throw new Error('Unexpected network access')};
  async function swFetch(req) {
    let promise=null;
    const event={request:req, respondWith(p){promise=p}};
    listeners.fetch(event);
    assert(promise,'SW must intercept cached JAR URL');
    return promise;
  }
  const url=new URL('emulator/jar/'+build.sha256+'.jar',origin);
  let resp=await swFetch(new Request(url));
  assert.equal(resp.status,200);
  assert.deepEqual(Buffer.from(await resp.arrayBuffer()), bytes);
  resp=await swFetch(new Request(url,{headers:{Range:'bytes=4-8'}}));
  assert.equal(resp.status,206);
  assert.equal(resp.headers.get('Content-Range'),`bytes 4-8/${bytes.length}`);
  assert.deepEqual(Buffer.from(await resp.arrayBuffer()),bytes.subarray(4,9));
  resp=await swFetch(new Request(url,{method:'HEAD'}));
  assert.equal(resp.headers.get('Content-Length'),String(bytes.length));
  assert.equal((await resp.arrayBuffer()).byteLength,0);
  assert.equal(await lib.forget(build),true);
  assert.equal(await lib.cached(build),false);
  // Static GitHub Pages: the emulator JAR itself must receive range responses
  // even if the upstream static host returns a full-file HTTP 200.
  const runtime = new URL('emulator/freej2me-web.jar', origin);
  const fakeEmulator = Buffer.from('PK\x03\x04fake compiled emulator JAR', 'binary');
  let fetches = 0;
  context.fetch = async request => {
    fetches++;
    assert.equal(request.url, runtime.href);
    assert.equal(request.headers.get('range'), null,
      'Runtime bootstrap must fetch the whole JAR before serving ranges');
    return new Response(fakeEmulator);
  };
  resp = await swFetch(new Request(runtime, {headers:{Range:'bytes=2-8'}}));
  assert.equal(resp.status, 206);
  assert.equal(resp.headers.get('Content-Range'), `bytes 2-8/${fakeEmulator.length}`);
  assert.deepEqual(Buffer.from(await resp.arrayBuffer()),fakeEmulator.subarray(2,9));
  resp = await swFetch(new Request(runtime, {headers:{Range:'bytes=-4'}}));
  assert.equal(resp.status,206);
  assert.deepEqual(Buffer.from(await resp.arrayBuffer()),fakeEmulator.subarray(-4));
  resp = await swFetch(new Request(runtime, {headers:{Range:'bytes=-0'}}));
  assert.equal(resp.status,416);
  resp = await swFetch(new Request(runtime, {method:'HEAD'}));
  assert.equal(resp.status,200);
  assert.equal(resp.headers.get('Content-Length'),String(fakeEmulator.length));
  assert.equal(fetches,1,'Runtime JAR must be cached after first request');
  console.log('browser JAR library: SHA / cache / ranges / null-controller regression all pass');
})().catch(e=>{console.error(e);process.exitCode=1});
