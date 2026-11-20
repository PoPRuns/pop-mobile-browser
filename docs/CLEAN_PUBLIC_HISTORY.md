# Clean public Git history for PoP Mobile

This project snapshot is a **history-clean release candidate**. It was exported
from the reviewed Pages + replacement-MIDI files, **not** cloned from the
original private development repository. The source ZIP has no `.git` directory.

Why: the original private repository committed an older MIDI WebAssembly module
that contained a SoundFont identified as copyrighted by Roland. Replacing
`libmidi.wasm` in a later commit would not remove the old bytes from Git history.

## Verified runtime bytes

- Replacement `vendor/freej2me-web/web/libmidi/libmidi.wasm` SHA-256:
  `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98`
- Emulator JAR SHA-256:
  `08ffc41af9e1bf815012a03d87e0af0e894eb98181f42b2302a2febf12b343eb`
- Media transcoder WASM SHA-256:
  `a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b`

`python3 tools/verify_public_snapshot.py` checks these and, once Git has been
initialized, verifies that the only reachable commit contains the same bytes.

## Create new local history (safe now, no GitHub publication required)

1. Keep `~/pop-mobile-browser/` and its current Git history **untouched**.
2. Extract this ZIP into the home folder, **only if**
   `~/pop-mobile-browser-public/` does not already exist. Never unzip it over
   your existing development checkout or into an existing `.git` directory.
3. In a terminal:

   ```sh
   cd ~/pop-mobile-browser-public
   python3 tools/verify_public_snapshot.py
   python3 -m unittest discover -s tests -p 'test_*.py'
   node tests/test_jar_library.cjs
   node tests/test_pages_sw.cjs
   git init -b main
   git add -A
   git diff --cached --name-only
   git commit -m 'Initial public snapshot: PoP Mobile with rebuilt MIDI'
   python3 tools/verify_public_snapshot.py
   git rev-list --count HEAD  # expect 1
   ```

The result is a separate local repository with one new root commit. No old Git
commit, tag, reflog or Git object has been copied into it. Do **not** use
`git clone`, `git bundle`, `git merge`, `git pull`, or GitHub's **Import repository**
feature to transfer the private development history into this public history.

## Later: reserve the desired GitHub Pages URL

**Only after the remaining publication requirements are satisfied:**

1. On GitHub, rename the **existing private** repository
   `PoPRuns/pop-mobile-browser` to `PoPRuns/pop-mobile-browser-development`,
   keeping its visibility **Private**. Renaming it does not expose its history.
2. On your **original development checkout**, change its `origin` remote to
   `https://github.com/PoPRuns/pop-mobile-browser-development.git` to avoid
   accidentally pushing private history to the newly created repository.
3. Create a **new empty** `PoPRuns/pop-mobile-browser` repository (without
   generating a README, `.gitignore`, or license). You may create it as Private
   while performing final testing and switch it to Public later.
4. From `~/pop-mobile-browser-public` alone, add the new origin and push:

   ```sh
   git remote add origin https://github.com/PoPRuns/pop-mobile-browser.git
   git push -u origin main
   ```

5. On GitHub, confirm the new repository has **one initial commit** and contains
   the replacement MIDI file. Do not enable Pages/public visibility until the
   corresponding-source archive is publicly available with a working link,
   applicable third-party notices are complete, and browser testing passes.

Reusing the old repository name ends GitHub's redirect from that old name to
the renamed private repository. This is expected for the intended Pages URL.

## Still pending

The full emulator corresponding-source archive must be accessible alongside
the binary distribution, the notices must contain the real direct source URL,
and MIDI playback needs a real-browser test. See `docs/SOURCE_COMPLIANCE.md`.

**History cleanliness does not, by itself, establish licensing compliance.**
