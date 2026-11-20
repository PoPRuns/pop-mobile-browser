# PoP Mobile — next release steps

**Current state:** `~/pop-mobile-browser-public` is the clean-history release candidate. The original `~/pop-mobile-browser` and its GitHub repository must stay private: their older history contains the previous MIDI binary.

## 1. Apply the missing-JAR preflight fix and test

Apply the drop-in ZIP only to `~/pop-mobile-browser-public`, then:

```sh
cd ~/pop-mobile-browser-public
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/test_jar_library.cjs
node tests/test_pages_sw.cjs
python3 tools/build_pages.py
python3 tools/verify_public_snapshot.py
python3 server.py --jar-dir "$HOME/pop-mobile-browser/PoP JAR Database 2026"
```

In Firefox, launch a known working build and listen for MIDI music using the new FM SoundFont. Test Restart, numpad switching, and the **Choose JAR file…** picker. As a negative check, stop the server, start plain `python3 server.py`, pick an uncached JAR, and verify it *asks for a file* rather than showing an emulator crash.

After confirming functionality, you may commit the fix locally. The updated history verifier accepts ordinary follow-up commits and audits **every reachable commit** for the approved runtime binaries.

## 2. Create the clean GitHub destination (private first)

After the audio test, rename the existing **private** GitHub repository `PoPRuns/pop-mobile-browser` to `PoPRuns/pop-mobile-browser-development`, without changing visibility. This retains the old project history privately.

Update the old local checkout's remote so it cannot accidentally push to the new destination:

```sh
cd ~/pop-mobile-browser
git remote set-url origin https://github.com/PoPRuns/pop-mobile-browser-development.git
```

Create a **new empty PRIVATE** `PoPRuns/pop-mobile-browser` GitHub repository, without README, license, or `.gitignore`. Push **only** the new clean checkout:

```sh
cd ~/pop-mobile-browser-public
python3 tools/verify_public_snapshot.py
git remote add origin https://github.com/PoPRuns/pop-mobile-browser.git
git push -u origin main
```

If `origin` is already set, inspect `git remote -v` before changing it. Do not merge, import, clone or pull the old development history into this new repository.

## 3. Attach the corresponding source to a release

Prepare this verified file on Ubuntu:

`pop-mobile-emulator-corresponding-source-v1.tar.gz`

SHA-256: `ad711845e72f1fbbd0491c3642bd2e35b98f4dfd959444e580a88b331cc3fcd9`

On the **new** GitHub repository, open **Releases → Draft a new release**. Target `main`, create the tag `v0.1.0`, enter a title such as *PoP Mobile v0.1.0 — emulator corresponding source*, upload the exact `.tar.gz` under release assets, and publish the release. A private repository release is initially available only to authorized users. Its download link will become accessible publicly when that repository is made public.

Planned direct asset URL (NOT LIVE UNTIL CREATED AND PUBLISHED):

`https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz`

Before public site deployment, update `THIRD_PARTY_NOTICES.md` and the website footer to point to the **actually published release asset**, state its SHA-256, and commit the notice update. Do not claim the URL works until it can be retrieved. Preserve all original component license notices and source-generation instructions.

## 4. Public visibility and Pages

Only once the source release is attached, the notices updated, and real browser gameplay/audio tests pass:

1. Make the **new history-clean** repository Public. Keep `pop-mobile-browser-development` Private.
2. Confirm the release archive downloads anonymously from its direct URL. Download a copy and run `sha256sum` on it; compare the hash above.
3. In GitHub repository **Settings → Pages → Build and deployment**, select **GitHub Actions**.
4. Under **Settings → Secrets and variables → Actions → Variables**, add `POP_MOBILE_PUBLICATION_APPROVED` set to `true`.
5. Run the `Deploy PoP Mobile to GitHub Pages` workflow manually under **Actions**. The public target is `https://popruns.github.io/pop-mobile-browser/`.
6. On a fresh Firefox browser profile, import a correctly hashed game JAR, start the player, test sound, test keypad toggle, and confirm the license/source footer links.

No Prince of Persia JARs should ever be committed or included in `_site/`.

> This is a deployment and engineering checklist rather than a legal opinion. The exact third-party licensing and source obligations should be reviewed before publication.
