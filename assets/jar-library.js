/* PoP Mobile — browser-owned JAR library; manually imported files are SHA-256 verified before caching. */
(() => {
  'use strict';
  const CACHE_NAME = 'pop-mobile-verified-jars-v1';
  const MAX_BYTES = 8 * 1024 * 1024;
  const HASH = /^[a-f0-9]{64}$/;
  let workerPromise;

  function jarRequest(sha) {
    if (!HASH.test(sha)) throw new Error('Invalid SHA-256');
    return new Request(new URL('emulator/jar/' + sha + '.jar', document.baseURI).href);
  }

  // A registered, ACTIVE worker is sufficient for a *new* emulator iframe.
  // The outer catalogue page need not have a controller: Firefox can report
  // navigator.serviceWorker.controller === null on the first visit or after a
  // hard reload (Ctrl+Shift+R), even though new in-scope frames are controlled.
  async function ensureWorker() {
    if (!('serviceWorker' in navigator) || !('caches' in window) || !crypto.subtle) {
      throw new Error('Browser storage needs a secure origin (HTTPS or localhost), Service Workers, Cache Storage and Web Crypto.');
    }
    if (!workerPromise) {
      workerPromise = (async () => {
        const script = new URL('sw-jar.js', document.baseURI);
        const scope = new URL('./', document.baseURI);
        const registration = await navigator.serviceWorker.register(script.href, {
          scope: scope.pathname
        });
        // `ready` resolves when the registration serving this page has an
        // active worker. Bound the wait: disabled SW/storage must not leave
        // the Play button spinning forever.
        const ready = await Promise.race([
          navigator.serviceWorker.ready,
          new Promise((_, reject) => setTimeout(() =>
            reject(new Error('Service worker did not activate. Check Firefox Settings → Privacy & Security, or try a normal Ctrl+R refresh.')), 12000))
        ]);
        const active = registration.active || ready.active;
        if (!active || active.scriptURL !== script.href ||
            new URL(registration.scope).href !== scope.href) {
          throw new Error('The JAR service worker is not the active worker for this website. Check browser site storage and reload normally.');
        }
        return true;
      })().catch(error => { workerPromise = null; throw error; });
    }
    return workerPromise;
  }

  async function cached(build) {
    const cache = await caches.open(CACHE_NAME);
    const response = await cache.match(jarRequest(build.sha256));
    return Boolean(response?.ok && response.headers.get('X-PoP-Verified-SHA256') === build.sha256 &&
      Number(response.headers.get('X-PoP-JAR-Size')) === Number(build.size));
  }

  async function forget(build) {
    return (await caches.open(CACHE_NAME)).delete(jarRequest(build.sha256));
  }

  function verifyInfo(build) {
    const size = Number(build.size);
    if (!HASH.test(build.sha256) || !Number.isSafeInteger(size) || size < 4 || size > MAX_BYTES) {
      throw new Error('Invalid catalogue size or SHA-256');
    }
    return size;
  }

  async function storeBytes(build, bytes) {
    await ensureWorker();
    const size = verifyInfo(build);
    if (bytes.byteLength !== size) throw new Error(`Wrong file size: expected ${size} bytes, got ${bytes.byteLength}`);
    const magic = new Uint8Array(bytes, 0, 4);
    if (magic[0] !== 80 || magic[1] !== 75 || magic[2] !== 3 || magic[3] !== 4)
      throw new Error('This is not a JAR/ZIP file');
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)))
      .map(n => n.toString(16).padStart(2, '0')).join('');
    if (digest !== build.sha256) throw new Error(`SHA-256 mismatch (downloaded ${digest.slice(0, 16)}…, expected ${build.sha256.slice(0, 16)}…). No file was cached.`);
    const cache = await caches.open(CACHE_NAME);
    const blob = new Blob([bytes], {type: 'application/java-archive'});
    await cache.put(jarRequest(build.sha256), new Response(blob, {headers: {
      'Content-Type': 'application/java-archive',
      'X-PoP-Verified-SHA256': build.sha256,
      'X-PoP-JAR-Size': String(size)
    }}));
    return {sha256: digest, size};
  }

  async function storeFile(build, file) {
    if (!file || file.size !== verifyInfo(build))
      throw new Error(`Wrong file size: expected ${build.size} bytes, got ${file?.size ?? 'no file'}.`);
    return storeBytes(build, await file.arrayBuffer());
  }

  function archiveSearchLink(build) {
    if (!HASH.test(build.sha256)) throw new Error('Invalid SHA-256');
    return `https://toca-1.github.io/new-j2me-software-archive-search/?sha256=${build.sha256}`;
  }

  window.PoPJarLibrary = Object.freeze({ ensureWorker, cached, forget, storeBytes, storeFile, archiveSearchLink });
})();
