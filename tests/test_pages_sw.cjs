/* GitHub Pages subpath and emulator-jar range regression. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const base = 'https://popruns.github.io/pop-mobile-browser/';
const callbacks = {};
const stored = new Map();
const cache = {
  match: async request => stored.get(request.url)?.clone(),
  put: async (request,response) => stored.set(request.url,response.clone())
};
const bytes = Buffer.from('PK\x03\x04 emulator binary test', 'binary');
let fetchCount = 0;
const context = {
  URL, Request, Response, Blob, Uint8Array, Number,
  caches:{open:async()=>cache},
  fetch: async request => {
    fetchCount++;
    assert.equal(request.url,base+'emulator/freej2me-web.jar');
    return new Response(bytes);
  },
  self:{
    registration:{scope:base},
    addEventListener:(type,callback)=>callbacks[type]=callback,
    skipWaiting:async()=>{}, clients:{claim:async()=>{}}
  }
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../sw-jar.js'),'utf8'),context);
async function request(relative, options){
  let result;
  callbacks.fetch({request:new Request(base+relative,options),respondWith:response=>result=response});
  return result || null;
}
(async()=>{
  const firstRequests = await Promise.all([
    request('emulator/freej2me-web.jar',{headers:{Range:'bytes=0-7'}}),
    request('emulator/freej2me-web.jar',{headers:{Range:'bytes=1-8'}}),
    request('emulator/freej2me-web.jar',{headers:{Range:'bytes=2-9'}})
  ]);
  let response=firstRequests[0];
  assert.equal(response.status,206);
  assert.equal(response.headers.get('Content-Range'),`bytes 0-7/${bytes.length}`);
  assert.deepEqual(Buffer.from(await response.arrayBuffer()),bytes.subarray(0,8));
  response=await request('emulator/freej2me-web.jar',{headers:{Range:'bytes=-4'}});
  assert.equal(response.status,206);
  assert.deepEqual(Buffer.from(await response.arrayBuffer()),bytes.subarray(-4));
  assert.equal(fetchCount,1);
  // Service worker MUST NOT catch routes outside its registration's project path.
  let didRespond=false;
  callbacks.fetch({request:new Request('https://popruns.github.io/unrelated/emulator/freej2me-web.jar'),respondWith:()=>didRespond=true});
  assert.equal(didRespond,false);
  console.log('GitHub Pages subpath and emulator Range responses pass');
})().catch(error=>{console.error(error);process.exitCode=1});
