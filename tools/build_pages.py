#!/usr/bin/env python3
"""Create a no-Python GitHub Pages deployment from the tracked PoP Mobile source.

The vendored upstream freej2me-web source remains untouched. The generated
emulator/src/main.js includes the same resolution/numpad adapters that the
local preview server adds at request time.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_site(output: Path):
    import sys
    sys.path.insert(0, str(ROOT))
    import server

    output = output.resolve()
    if output == ROOT or ROOT in output.parents and output.name == 'vendor':
        raise ValueError('Refusing to overwrite source files')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for rel in ('index.html', 'catalogue.html', 'sw-jar.js',
                'THIRD_PARTY_NOTICES.md', 'LICENSE', 'README.md'):
        shutil.copy2(ROOT / rel, output / rel)
    # Documentation lives in Git; it is not needed in the deployed website.
    for directory in ('assets', 'data'):
        shutil.copytree(ROOT / directory, output / directory)

    # A build-time flag avoids calls to the unavailable /api/status endpoint.
    catalogue = output / 'catalogue.html'
    html = catalogue.read_text(encoding='utf-8')
    marker = '<meta name="pop-mobile-static" content="1">'
    if marker in html:
        raise ValueError('Unexpected duplicate static marker')
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n  ' + marker, 1)
    html = html.replace('assets/app.js?v=harem-families-1', 'assets/app.js?v=pages-harem-families-1')
    catalogue.write_text(html, encoding='utf-8')

    vendor = ROOT / 'vendor/freej2me-web/web'
    midi = vendor / 'libmidi/libmidi.wasm'
    if hashlib.sha256(midi.read_bytes()).hexdigest() != 'cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98':
        raise ValueError('Unexpected MIDI WebAssembly: release-approved replacement is missing')
    if b'Roland' in midi.read_bytes():
        raise ValueError('Legacy MIDI bank detected; public deployment is blocked')
    emulator = output / 'emulator'
    shutil.copytree(vendor, emulator)
    launcher = emulator / 'src/main.js'
    source = launcher.read_text(encoding='utf-8')
    adapted = server.inject_fps_hook(server.inject_numpad_hook(server.inject_resolution_hook(source)))
    launcher.write_text(adapted, encoding='utf-8')
    # Bust cached launcher modules when the player adapter changes.
    run_html = emulator / 'run.html'
    run_html.write_text(run_html.read_text(encoding='utf-8').replace(
        'src="src/main.js"', 'src="src/main.js?v=family-fps-1"', 1), encoding='utf-8')
    # Preserve upstream license in the downloadable static distribution.
    shutil.copy2(ROOT / 'vendor/freej2me-web/LICENSE', emulator / 'LICENSE')
    # Avoid Jekyll filtering underscore-named files on a project Pages site.
    (output / '.nojekyll').write_text('')
    if list(output.glob('**/jar/*.jar')):
        raise ValueError('A game JAR would be published')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '_site')
    args = parser.parse_args()
    target = build_site(args.output)
    print(f'PoP Mobile static Pages site: {target}')
    print('Note: publishing GPL binaries requires the corresponding-source distribution; see THIRD_PARTY_NOTICES.md.')


if __name__ == '__main__':
    main()
