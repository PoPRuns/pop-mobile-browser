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
        '9c291d8d25159181d103c5e3bfc78a74dffe6661378af7601a9141c669528d43',
    'vendor/freej2me-web/web/libmedia/transcode/transcode.wasm':
        'a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b',
}
EMULATOR_JAR = 'vendor/freej2me-web/web/freej2me-web.jar'
MIDI_PATH = 'vendor/freej2me-web/web/libmidi/libmidi.wasm'
# The original Java binary is still approved in historical commits.
HISTORICAL_JAVA_SHA256 = {'08ffc41af9e1bf815012a03d87e0af0e894eb98181f42b2302a2febf12b343eb', '70d84f5335e16842cdda59249af83e98dfa18c1da713a0a12364715b6f4961ce', EXPECTED[EMULATOR_JAR]}


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
        # Normal updates must not make this verifier fail. Audit *every*
        # reachable commit/branch/tag rather than requiring exactly one commit.
        history = git('rev-list', '--all', check=False)
        if history.returncode != 0:
            problems.append('Could not inspect Git history')
        else:
            refs = history.stdout.decode().splitlines()
            print(f'Git history: {len(refs)} reachable commits')
            if not refs:
                problems.append('Git repository has no reachable commit')
            roots = git('rev-list', '--max-parents=0', '--all', check=False)
            if roots.returncode or len(roots.stdout.decode().splitlines()) != 1:
                problems.append('Expected a single independent root history')
            for commit in refs:
                # Check *every* historical copy; deleting a file later does
                # not hide it after making the repository public.
                for rel, wanted in EXPECTED.items():
                    stored = git('show', f'{commit}:{rel}', check=False)
                    approved = HISTORICAL_JAVA_SHA256 if rel == EMULATOR_JAR else {wanted}
                    if stored.returncode or digest(stored.stdout) not in approved:
                        problems.append(f'Unexpected emulator binary in commit {commit[:12]}: {rel}')
                tree = git('ls-tree', '-r', '--name-only', commit, check=False)
                if tree.returncode:
                    problems.append(f'Could not read tree of commit {commit[:12]}')
                    continue
                tracked = tree.stdout.decode().splitlines()
                if any(x.lower().endswith('.jar') and x != EMULATOR_JAR for x in tracked):
                    problems.append(f'A game or unknown JAR was committed: {commit[:12]}')
                if any(x.endswith('.sf2') for x in tracked):
                    problems.append(f'A SoundFont was committed: {commit[:12]}')
                if any(x.startswith('_site/') or x.startswith('PoP JAR Database 2026/') for x in tracked):
                    problems.append(f'Generated site or game database was committed: {commit[:12]}')
            if not problems:
                print('PASS: all reachable commits contain only the approved emulator binaries')
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
