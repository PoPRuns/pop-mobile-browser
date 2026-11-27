/* PoP Mobile — verified user JARs + CheerpJ byte-range support on static hosts.
 * The service worker is scoped to the project base path, including GitHub Pages.
 * No game JARs are fetched or hosted by PoP Mobile automatically.
 */
'use strict';
const CACHE_NAME = 'pop-mobile-verified-jars-v1';
const RUNTIME_CACHE = 'pop-mobile-emulator-runtime-c19416e-v11';
const PATH_RE = /\/emulator\/jar\/([a-f0-9]{64})\.jar$/;
const EMULATOR_JAR = '/emulator/freej2me-web.jar';
let runtimeJarFlight = null; // Share a single download across parallel CheerpJ Range requests.
self.addEventListener('install', event => { event.waitUntil(self.skipWaiting()); });
self.addEventListener('activate', event => { event.waitUntil(self.clients.claim()); });

function respondFromBlob(request, blob) {
  const size = blob.size;
  const headers = {
    'Content-Type': 'application/java-archive',
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff'
  };
  const range = request.headers.get('range');
  if (range) {
    const found = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
    if (!found || (!found[1] && !found[2])) {
      return new Response(null, {status: 416, headers: {'Content-Range': `bytes */${size}`}});
    }
    const suffix = !found[1] && Number(found[2]);
    if (suffix === 0) {
      return new Response(null, {status: 416, headers: {'Content-Range': `bytes */${size}`}});
    }
    const start = found[1] ? Number(found[1]) : Math.max(0, size - suffix);
    const end = found[1] && found[2] ? Math.min(size - 1, Number(found[2])) : size - 1;
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start >= size || start > end) {
      return new Response(null, {status: 416, headers: {'Content-Range': `bytes */${size}`}});
    }
    headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
    headers['Content-Length'] = String(end - start + 1);
    return new Response(request.method === 'HEAD' ? null : blob.slice(start, end + 1), {status: 206, headers});
  }
  headers['Content-Length'] = String(size);
  return new Response(request.method === 'HEAD' ? null : blob, {status: 200, headers});
}

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const scope = new URL(self.registration.scope);
  if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  if (!['GET', 'HEAD'].includes(event.request.method)) return;
  const match = PATH_RE.exec(url.pathname);
  const runtime = url.pathname === scope.pathname.replace(/\/$/, '') + EMULATOR_JAR;
  if (!match && !runtime) return;

  event.respondWith((async () => {
    const pathnameRequest = new Request(url.origin + url.pathname);
    if (runtime) {
      // Pages/CDNs are not guaranteed to return 206 for static .jar files.
      // Fetch the known emulator JAR in full, then synthesize precise 206s.
      // This is the GPL-licensed emulator, never a copyrighted game JAR.
      const cache = await caches.open(RUNTIME_CACHE);
      let stored = await cache.match(pathnameRequest);
      if (!stored) {
        if (!runtimeJarFlight) {
          runtimeJarFlight = (async () => {
            const downloaded = await fetch(pathnameRequest);
            if (!downloaded.ok) return downloaded;
            const bytes = await downloaded.arrayBuffer();
            const magic = new Uint8Array(bytes, 0, 4);
            if (bytes.byteLength < 4 || magic[0] !== 80 || magic[1] !== 75 || magic[2] !== 3 || magic[3] !== 4) {
              return new Response('Emulator JAR is invalid', {status: 502});
            }
            const response = new Response(bytes, {headers: {'Content-Type': 'application/java-archive'}});
            await cache.put(pathnameRequest, response.clone());
            return response;
          })().finally(() => { runtimeJarFlight = null; });
        }
        stored = (await runtimeJarFlight).clone();
        if (!stored.ok) return stored;
      }
      return respondFromBlob(event.request, await stored.blob());
    }
    const cache = await caches.open(CACHE_NAME);
    const stored = await cache.match(pathnameRequest);
    if (!stored || stored.headers.get('X-PoP-Verified-SHA256') !== match[1]) {
      // In local preview, the SHA-verified Python server may have the JAR.
      // On static hosting this safely becomes 404 (no game is downloaded).
      return fetch(event.request);
    }
    const blob = await stored.blob();
    if (Number(stored.headers.get('X-PoP-JAR-Size')) !== blob.size) return fetch(event.request);
    return respondFromBlob(event.request, blob);
  })());
});
