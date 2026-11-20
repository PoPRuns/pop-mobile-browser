#!/usr/bin/env python3
"""Local PoP Mobile preview. Standard library only; games are never copied to site files."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
EMULATOR_ROOT = ROOT / 'vendor' / 'freej2me-web' / 'web'
DEFAULT_JAR_DIR = ROOT / 'PoP JAR Database 2026'
MAX_JAR_SIZE = 8 * 1024 * 1024
JAR_PATH_RE = re.compile(r'/emulator/jar/([a-f0-9]{64})\.jar\Z')
RANGE_RE = re.compile(r'bytes=(\d*)-(\d*)\Z')


# The embedded freej2me-web launcher only accepts 'jar' and 'app' URLs. For our
# local preview, insert a startup configuration hook into the JS we serve. This
# leaves the user's git checkout and the compiled emulator JAR completely intact.
# The hook uses CheerpJ's documented Java library bridge, then invokes the
# original FreeJ2ME.main. No rebuild and no game files added to the website.
EMULATOR_MAIN_ANCHOR = '    FreeJ2ME.main(args).catch(e => {'
EMULATOR_RESOLUTION_HOOK = r"""
    // PoP Mobile: apply the catalogue-selected LCD resolution before Java ME starts.
    // FreeJ2ME stores per-app settings in [appId]/config/settings.conf, so
    // updating its default alone would not override a previously played game.
    const popW = Number(sp.get('screenWidth'));
    const popH = Number(sp.get('screenHeight'));
    if (!sp.has('app') && Number.isInteger(popW) && Number.isInteger(popH) &&
        popW >= 32 && popW <= 1024 && popH >= 32 && popH <= 1024) {
        const report = (ok, error) => {
            if (window.parent !== window) {
                window.parent.postMessage({type: 'pop-mobile:resolution', ok,
                    width: popW, height: popH, error: error || ''}, location.origin);
            }
        };
        try {
            const File = await lib.java.io.File;
            const MIDletLoader = await lib.org.recompile.mobile.MIDletLoader;
            const LauncherUtil = await lib.pl.zb3.freej2me.launcher.LauncherUtil;
            const Config = await lib.org.recompile.freej2me.Config;
            const jarFile = await new File(cheerpjWebRoot + '/jar/' + (sp.get('jar') || 'game.jar'));
            const loader = await MIDletLoader.getMIDletLoader(jarFile);
            if (!loader) throw new Error('Could not open the JAR manifest');
            await LauncherUtil.ensureAppId(loader, await jarFile.getName());
            const appId = await loader.getAppId();
            if (!appId) throw new Error('No game ID could be determined');
            const config = await new Config();
            await config.init('./' + appId);
            await config.appSettings.put('width', String(popW));
            await config.appSettings.put('height', String(popH));
            await config.saveConfig();
            console.info(`PoP Mobile: configured ${appId} for ${popW}x${popH}`);
            report(true);
        } catch (error) {
            console.warn('PoP Mobile: unable to set initial screen size:', error);
            report(false, String(error));
            // Let the game start normally so manual settings remain available.
        }
    }
"""



# PoP Mobile keyboard adapter; upstream files under vendor/ are NOT modified.
# The default FreeJ2ME numpad behaviour swaps physical 1-2-3 / 7-8-9.
# For "standard", pass the equivalent DigitN Java key instead of NumpadN.
EMULATOR_KEYPAD_INIT_ANCHOR = 'const keyRepeatManager = new KeyRepeatManager();'
EMULATOR_KEYPAD_EVENT_ANCHOR = """        if (codeMap[e.code]) {
            keyRepeatManager.post(isDown, e.code, {"""
EMULATOR_KEYPAD_STATE = r"""
// PoP Mobile adapter: keyboard layout is controlled by a first-party checkbox.
// Upstream freej2me-web is unchanged; see THIRD_PARTY_NOTICES.md (if present).
let popNumpadMode = sp.get('numpad') === 'standard' ? 'standard' : 'phone';
const popHeldNumpadKeys = new Map();
function popMapNumpadKey(event) {
    const code = event.code;
    if (!/^Numpad[1-9]$/.test(code)) return code;
    // Lock the mapping at keydown so switching modes while holding a key
    // doesn't send its release to a different emulated key.
    if (event.type === 'keyup') {
        const mapped = popHeldNumpadKeys.get(code) ||
            (popNumpadMode === 'standard' ? 'Digit' + code.slice(6) : code);
        popHeldNumpadKeys.delete(code);
        return mapped;
    }
    if (!popHeldNumpadKeys.has(code)) {
        popHeldNumpadKeys.set(code, popNumpadMode === 'standard' ? 'Digit' + code.slice(6) : code);
    }
    return popHeldNumpadKeys.get(code);
}
window.addEventListener('message', event => {
    if (event.source !== window.parent || event.origin !== location.origin ||
        event.data?.type !== 'pop-mobile:numpad') return;
    if (event.data.mode === 'phone' || event.data.mode === 'standard') {
        popNumpadMode = event.data.mode;
    }
});
"""
EMULATOR_KEYPAD_EVENT_REPLACEMENT = """        const popCode = popMapNumpadKey(e);
        if (codeMap[popCode]) {
            keyRepeatManager.post(isDown, popCode, {"""


def inject_numpad_hook(upstream_source: str) -> str:
    """Add an opt-in numpad layout choice without changing the upstream checkout."""
    if upstream_source.count(EMULATOR_KEYPAD_INIT_ANCHOR) != 1 or \
            upstream_source.count(EMULATOR_KEYPAD_EVENT_ANCHOR) != 1:
        raise ValueError('Unsupported freej2me-web launcher version: keyboard anchor has changed')
    source = upstream_source.replace(EMULATOR_KEYPAD_INIT_ANCHOR,
        EMULATOR_KEYPAD_INIT_ANCHOR + '\n' + EMULATOR_KEYPAD_STATE, 1)
    return source.replace(EMULATOR_KEYPAD_EVENT_ANCHOR,
                          EMULATOR_KEYPAD_EVENT_REPLACEMENT, 1)


def inject_resolution_hook(upstream_source: str) -> str:
    """Inject once into the known upstream JS launcher (source stays unchanged)."""
    if upstream_source.count(EMULATOR_MAIN_ANCHOR) != 1 or not all(
        marker in upstream_source for marker in (
            'const sp = new URLSearchParams(location.search)',
            'const lib = await cheerpjRunLibrary(',
            'const FreeJ2ME = await lib.org.recompile.freej2me.FreeJ2ME',
        )
    ):
        raise ValueError('Unsupported freej2me-web launcher version: startup anchor has changed')
    return upstream_source.replace(EMULATOR_MAIN_ANCHOR,
                                   EMULATOR_RESOLUTION_HOOK + '\n' + EMULATOR_MAIN_ANCHOR, 1)


def load_builds():
    path = ROOT / 'data' / 'catalogue.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    return {item['sha256']: item for item in data['builds']}


def parse_byte_range(header: str | None, length: int):
    if not header:
        return None
    match = RANGE_RE.fullmatch(header.strip())
    if not match or length <= 0:
        raise ValueError('Invalid byte range')
    start_s, end_s = match.groups()
    if not start_s and not end_s:
        raise ValueError('Invalid byte range')
    if not start_s:
        suffix = int(end_s)
        if suffix == 0:
            raise ValueError('Invalid byte range')
        return max(length - suffix, 0), length - 1
    start = int(start_s)
    end = min(int(end_s), length - 1) if end_s else length - 1
    if start >= length or start > end:
        raise ValueError('Invalid byte range')
    return start, end


def index_local_jars(folder: Path, builds: dict) -> tuple[dict[str, Path], dict]:
    """Recursively index JARs by their actual SHA-256, not their filenames.

    The catalogue and local collection can use unrelated filenames. Skip symlinks,
    oversize files and entries that do not match a known catalogue checksum.
    """
    matches: dict[str, Path] = {}
    stats = {'filesScanned': 0, 'unknownFiles': 0, 'duplicates': 0}
    if not folder.is_dir():
        return matches, stats
    root = folder.resolve()
    catalogue_sizes = {int(item['size']) for item in builds.values()}
    for path in folder.rglob('*'):
        if path.suffix.lower() != '.jar' or not path.is_file() or path.is_symlink():
            continue
        if not path.resolve().is_relative_to(root):
            continue
        stats['filesScanned'] += 1
        try:
            length = path.stat().st_size
            if length not in catalogue_sizes or length > MAX_JAR_SIZE or length < 4:
                stats['unknownFiles'] += 1
                continue
            digest = hashlib.sha256()
            with path.open('rb') as file:
                if not file.read(4).startswith(b'PK'):
                    stats['unknownFiles'] += 1
                    continue
                file.seek(0)
                for chunk in iter(lambda: file.read(65536), b''):
                    digest.update(chunk)
            sha = digest.hexdigest()
            if sha in builds and length == int(builds[sha]['size']):
                if sha in matches:
                    stats['duplicates'] += 1
                else:
                    matches[sha] = path
            else:
                stats['unknownFiles'] += 1
        except OSError:
            stats['unknownFiles'] += 1
    return matches, stats


def load_verified_local_jar(build: dict, path: Path) -> bytes:
    """Re-verify on each request in case a file changed after server startup."""
    expected_size = int(build['size'])
    if expected_size > MAX_JAR_SIZE or expected_size < 4:
        raise ValueError('Invalid catalogue JAR size')
    with path.open('rb') as file:
        payload = file.read(expected_size + 1)
    if len(payload) != expected_size:
        raise ValueError('Local JAR size changed since catalogue matching')
    if hashlib.sha256(payload).hexdigest() != build['sha256'] or not payload.startswith(b'PK'):
        raise ValueError('Local JAR SHA-256 mismatch; file may have changed since startup')
    return payload


class AppHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    builds = {}
    jar_source = 'local'  # retained for /api/status and --jar-source local compatibility
    jar_dir = DEFAULT_JAR_DIR
    local_jars = {}
    scan_stats = {}

    def do_GET(self):
        self.dispatch(False)

    def do_HEAD(self):
        self.dispatch(True)

    def log_message(self, fmt, *args):
        sys.stderr.write('%s - %s\n' % (self.log_date_time_string(), fmt % args))

    def respond_json(self, status: int, data: dict, head: bool = False):
        content = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head:
            self.wfile.write(content)

    def dispatch(self, head: bool):
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        if path == '/api/status':
            checkout = (EMULATOR_ROOT / 'run.html').is_file()
            built = (EMULATOR_ROOT / 'freej2me-web.jar').is_file()
            return self.respond_json(HTTPStatus.OK, {
                'emulatorReady': checkout and built,
                'emulatorCheckoutFound': checkout,
                'emulatorJarBuilt': built,
                'emulator': 'freej2me-web',
                'jarSource': self.jar_source,
                'jarDirectory': str(self.jar_dir),
                'jarDirectoryFound': self.jar_dir.is_dir(),
                'cataloguedBuilds': len(self.builds),
                'localJarCount': len(self.local_jars),
                'localJarHashes': sorted(self.local_jars),
                'scan': self.scan_stats,
            }, head)
        match = JAR_PATH_RE.fullmatch(path)
        if match:
            sha = match.group(1)
            build = self.builds.get(sha)
            if not build:
                return self.respond_json(HTTPStatus.NOT_FOUND, {'error': 'Unknown SHA-256'}, head)
            local_path = self.local_jars.get(sha)
            if local_path is None:
                # Never download a game on behalf of the visitor. The service
                # worker serves imported and verified JARs from Cache Storage;
                # otherwise the UI offers the external index and local picker.
                return self.respond_json(HTTPStatus.NOT_FOUND, {
                    'error': 'JAR not available locally. Use the J2ME index link and Choose JAR file in the player.'
                }, head)
            try:
                content = load_verified_local_jar(build, local_path)
            except (OSError, ValueError) as exc:
                return self.respond_json(HTTPStatus.CONFLICT, {'error': str(exc)}, head)
            return self.send_jar_headers(len(content), content, head)
        if path == '/emulator/src/main.js':
            return self.serve_emulator_launcher(head)
        if path.startswith('/emulator/'):
            relative = path[len('/emulator/'):]
            return self.serve_file(EMULATOR_ROOT, relative, head)
        if path == '/sw-jar.js':
            return self.serve_file(ROOT, 'sw-jar.js', head)
        if path == '/' or path == '/index.html':
            return self.serve_file(ROOT, 'index.html', head)
        if path == '/catalogue.html':
            return self.serve_file(ROOT, 'catalogue.html', head)
        if path in ('/THIRD_PARTY_NOTICES.md', '/LICENSE', '/README.md'):
            return self.serve_file(ROOT, path.lstrip('/'), head)
        if path.startswith('/assets/'):
            return self.serve_file(ROOT / 'assets', path[len('/assets/'):], head)
        if path == '/data/catalogue.json':
            return self.serve_file(ROOT / 'data', path[len('/data/'):], head)
        return self.respond_json(HTTPStatus.NOT_FOUND, {'error': 'Not found'}, head)

    def serve_emulator_launcher(self, head: bool = False):
        path = EMULATOR_ROOT / 'src' / 'main.js'
        try:
            content = inject_numpad_hook(inject_resolution_hook(path.read_text(encoding='utf-8'))).encode('utf-8')
        except (OSError, UnicodeError, ValueError) as exc:
            return self.respond_json(HTTPStatus.BAD_GATEWAY, {'error': str(exc)}, head)
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'text/javascript; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head:
            self.wfile.write(content)

    def send_jar_headers(self, length: int, content: bytes | None, head: bool = False):
        try:
            chosen = parse_byte_range(self.headers.get('Range'), length)
        except ValueError:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header('Content-Range', f'bytes */{length}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        start, end = chosen if chosen else (0, length - 1)
        self.send_response(HTTPStatus.PARTIAL_CONTENT if chosen else HTTPStatus.OK)
        self.send_header('Content-Type', 'application/java-archive')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Disposition', 'inline')
        if chosen:
            self.send_header('Content-Range', f'bytes {start}-{end}/{length}')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head and content is not None:
            self.wfile.write(content[start:end + 1])

    def serve_file(self, root: Path, relative: str, head: bool = False):
        root = root.resolve()
        file_path = (root / relative).resolve()
        if not file_path.is_relative_to(root) or not file_path.is_file():
            return self.respond_json(HTTPStatus.NOT_FOUND, {'error': 'File not found'}, head)
        length = file_path.stat().st_size
        try:
            chosen = parse_byte_range(self.headers.get('Range'), length)
        except ValueError:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header('Content-Range', f'bytes */{length}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        start, end = chosen if chosen else (0, length - 1)
        typ = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
        if file_path.suffix.lower() in ('.js', '.mjs'):
            typ = 'text/javascript'
        if file_path.suffix.lower() == '.wasm':
            typ = 'application/wasm'
        self.send_response(HTTPStatus.PARTIAL_CONTENT if chosen else HTTPStatus.OK)
        self.send_header('Content-Type', typ + ('; charset=utf-8' if typ.startswith(('text/', 'application/json')) else ''))
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        if chosen:
            self.send_header('Content-Range', f'bytes {start}-{end}/{length}')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head:
            try:
                with file_path.open('rb') as file:
                    file.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        data = file.read(min(65536, remaining))
                        if not data:
                            break
                        self.wfile.write(data)
                        remaining -= len(data)
            except BrokenPipeError:
                pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1', help='Default localhost only. Never expose this test server publicly.')
    parser.add_argument('--jar-dir', type=Path, default=DEFAULT_JAR_DIR,
                        help='Folder containing local JARs, scanned recursively (default: PoP JAR Database 2026)')
    parser.add_argument('--jar-source', choices=('local',), default='local',
                        help='Only local JAR files are served (the default; kept for CLI compatibility)')
    args = parser.parse_args()
    if not 0 < args.port < 65536:
        parser.error('Invalid port')
    # No local JAR directory is required: new clones can start immediately.
    # An empty local index means that imported SHA-verified browser JARs are
    # the only playable game sources until a JAR folder is configured.
    AppHandler.builds = load_builds()
    AppHandler.jar_source = args.jar_source
    AppHandler.jar_dir = args.jar_dir.resolve()
    AppHandler.local_jars, AppHandler.scan_stats = index_local_jars(AppHandler.jar_dir, AppHandler.builds)
    httpd = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f'PoP Mobile: http://{args.host}:{args.port}/', flush=True)
    print(f'Catalogue: {len(AppHandler.builds)} JAR records | JAR mode: {args.jar_source}', flush=True)
    if args.jar_dir.is_dir():
        print(f'Local folder: {AppHandler.jar_dir}', flush=True)
        print(f'Matched {len(AppHandler.local_jars)} / {len(AppHandler.builds)} SHA-256 builds '
              f'({AppHandler.scan_stats["filesScanned"]} JAR files scanned).', flush=True)
    else:
        print('No local JAR folder detected. Catalogue is available; select JARs in the browser to play.', flush=True)
    if len(AppHandler.local_jars) != len(AppHandler.builds):
        print('Unmatched builds can be loaded using the SHA-verified browser file picker.', flush=True)
    if not (EMULATOR_ROOT / 'run.html').is_file() or not (EMULATOR_ROOT / 'freej2me-web.jar').is_file():
        print('Browser emulator not fully installed: verify vendor/freej2me-web/web/freej2me-web.jar exists.', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.', flush=True)
    finally:
        httpd.server_close()

if __name__ == '__main__':
    main()
