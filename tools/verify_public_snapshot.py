#!/usr/bin/env python3
"""Verify a history-clean PoP Mobile public-repository *candidate*.

This checks the actual working files and, if present, every reachable Git
commit. It does not approve source-licensing or third-party artwork rights.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'vendor/freej2me-web/web/libmidi/libmidi.wasm':
        'cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98',
    'vendor/freej2me-web/web/freej2me-web.jar':
        '08ffc41af9e1bf815012a03d87e0af0e894eb98181f42b2302a2febf12b343eb',
    'vendor/freej2me-web/web/libmedia/transcode/transcode.wasm':
        'a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b',
}
EMULATOR_JAR = 'vendor/freej2me-web/web/freej2me-web.jar'
MIDI_PATH = 'vendor/freej2me-web/web/libmidi/libmidi.wasm'


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(['git', '-C', str(ROOT), *args],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate() -> None:
    problems: list[str] = []
    for rel, wanted in EXPECTED.items():
        path = ROOT / rel
        if not path.is_file():
            problems.append(f'Missing required emulator file: {rel}')
            continue
        actual = digest(path.read_bytes())
        if actual != wanted:
            problems.append(f'Unexpected SHA-256 for {rel}: {actual}')
        else:
            print(f'PASS: {rel} [{actual[:12]}…]')
    midi = ROOT / MIDI_PATH
    if midi.exists():
        contents = midi.read_bytes()
        if b'Roland' in contents or b'ROLAND' in contents.upper():
            problems.append('Old SoundFont identifier present in libmidi.wasm')
        if b'PoP Mobile Original FM GM' not in contents:
            problems.append('Replacement FM SoundFont identifier missing')
    for name in ('PoP JAR Database 2026', '.pop-mobile-local-cache',
                 '.jarchive-cache'):
        if (ROOT / name).exists():
            problems.append(f'Excluded/generated directory present: {name}')
    for path in ROOT.rglob('*.jar'):
        if '_site' in path.relative_to(ROOT).parts[:1] or '.git' in path.relative_to(ROOT).parts:
            continue  # generated Pages deployment and VCS internals are not source files
        if path.relative_to(ROOT).as_posix() != EMULATOR_JAR:
            problems.append(f'Unexpected JAR (possible game file): {path.relative_to(ROOT)}')
    for path in ROOT.rglob('*.sf2'):
        if '_site' in path.relative_to(ROOT).parts[:1] or '.git' in path.relative_to(ROOT).parts:
            continue
        problems.append(f'SoundFont file unexpectedly bundled: {path.relative_to(ROOT)}')
    for path in ROOT.rglob('.git'):
        if '_site' in path.relative_to(ROOT).parts[:1]:
            continue
        if path != ROOT / '.git':
            problems.append(f'Nested Git metadata present: {path.relative_to(ROOT)}')
    if (ROOT / '.gitmodules').exists():
        problems.append('Submodule metadata should not be present')
    if (ROOT / '.git').exists():
        # One new initial commit is okay, but any existing private history is not.
        result = git('rev-list', '--count', '--all', check=False)
        if result.returncode != 0:
            problems.append('Could not inspect Git history')
        else:
            count = int(result.stdout.strip() or b'0')
            print(f'Git history: {count} reachable commits')
            if count > 1:
                problems.append('More than one reachable Git commit; use a fresh git init')
            if count == 1:
                refs = git('rev-list', '--all').stdout.decode().strip().splitlines()
                commit = refs[0]
                # A single commit can still be the *old* initial private commit.
                for rel, wanted in EXPECTED.items():
                    stored = git('show', f'{commit}:{rel}', check=False)
                    if stored.returncode or digest(stored.stdout) != wanted:
                        problems.append(f'Git commit does not contain expected approved binary: {rel}')
                tracked = git('ls-tree', '-r', '--name-only', commit).stdout.decode().splitlines()
                if any(p.lower().endswith('.jar') and p != EMULATOR_JAR for p in tracked):
                    problems.append('A game JAR is in committed history')
                if any(p.endswith('.sf2') for p in tracked):
                    problems.append('A SoundFont is in committed history')
                if any(p.startswith('_site/') or p.startswith('PoP JAR Database 2026/') for p in tracked):
                    problems.append('Generated site or game database was committed')
                print('PASS: single root commit matches approved emulator binaries' if not problems else 'FAIL: Git commit verification')
    else:
        print('PASS: no .git directory; exporting a fresh history is possible')
    if problems:
        print('\nNOT SAFE FOR A CLEAN INITIAL PUSH:', file=sys.stderr)
        for item in problems:
            print(' - ' + item, file=sys.stderr)
        raise SystemExit(1)
    print('PASS: public-history snapshot integrity checks')
    print('NOTE: this is NOT approval to publish: verify source access, licensing and gameplay first.')


if __name__ == '__main__':
    validate()
