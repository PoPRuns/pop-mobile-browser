# PoP Mobile Browser

An independent archival catalogue of **950 SHA-256-identified Prince of Persia Java ME builds** across nine collections (including Needs Review). Browse metadata, compare experimental gameplay groups, and run verified JARs in the browser through **freej2me-web / CheerpJ**.

**No Prince of Persia game JAR files are included in this repository.** The checked-in `freej2me-web.jar` is the emulator, not a game.

## Start the local preview

Requirements: Python 3.10+ and a current browser supporting Service Workers, Cache Storage and Web Crypto. The emulator also loads CheerpJ from its official CDN and requires an internet connection for that runtime.

```sh
python3 server.py
```

Open <http://127.0.0.1:8000/>. **A fresh clone works without `PoP JAR Database 2026/`.** All game records are visible, and you can import individual JARs through the player. Do not open `index.html` via `file://`.

To use an existing local collection, create `PoP JAR Database 2026/` beside `server.py` (or provide a separate directory):

```sh
python3 server.py --jar-dir '/path/to/your/JAR collection'
```

The server scans it recursively at startup, matches JARs using size and SHA-256 rather than filenames, and re-verifies each JAR before serving. The legacy `--jar-source local` spelling is also supported. Game JARs are **not** copied into public website directories. Keep your local game directory in `.gitignore`.

## Play a game

1. Select a game, then a JAR build, and click **Play / Load**.
2. If that SHA-256 is in your local collection or already cached in the browser, the emulator launches it automatically.
3. Otherwise, click **Find JAR on the J2ME index** (opens the exact SHA-256 entry), download a JAR from the original archive site, and click **Choose JAR file…** in PoP Mobile.
4. PoP Mobile checks ZIP signature, expected size and **full SHA-256** before saving the imported JAR to browser Cache Storage and launching it. A mismatched file is rejected.

PoP Mobile does **not** automatically request JARs from external mirrors or launch a Python downloader. Browser cache storage can be cleared or evicted by the browser. Controls include fullscreen, a restart button, automatic closest-fit emulated resolution and a persistent numpad-layout toggle.

The emulator has known compatibility limitations; individual builds may not work. Audio and CheerpJ initialization can take some time.

## Repository layout

- `index.html`, `assets/home.*`: game selection gallery
- `catalogue.html`, `assets/app.js`, `assets/site.css`: build browser and emulation controls
- `assets/jar-library.js`, `sw-jar.js`: SHA-256-verified imported files and byte-range service-worker responses
- `data/catalogue.json`: catalogue of JAR metadata and experimental gameplay groups (no game binaries)
- `server.py`: standard-library-only local preview, SHA-256 matching, local JAR serving, and runtime-only keyboard/resolution adapters
- `vendor/freej2me-web/web/`: reduced browser emulator runtime; not its full build-source checkout
- `tests/`: catalogue, server, player adapter and caching regression tests
- `tools/import_pop_workbook.py`: optional catalogue regeneration from the research workbook; its non-standard Python dependencies are not needed for normal browsing

The separate JAR inspection and gameplay fingerprint research utilities are intentionally **not** included in this slim runtime repository.

To rebuild the catalogue after editing the research workbook, obtain the [underlying spreadsheet](https://docs.google.com/spreadsheets/d/1hBohTK19FVDa8wyGCd-a4xfeli0SKkFb) and run:

```sh
python3 tools/import_pop_workbook.py '/PATH/TO/SPREADSHEET.xlsm' data/catalogue.json
```

## Testing

Python tests (stdlib):

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Optional JavaScript cache / service-worker test (Node.js 18+):

```sh
node tests/test_jar_library.cjs
```

## GitHub Pages deployment (after completing the source audit)

A serverless GitHub Pages build is included. It works at the project subpath
`https://popruns.github.io/pop-mobile-browser/` and does not require Python at
runtime or host game JARs. A visitor selects a build, opens its SHA-specific
J2ME index entry, downloads a game JAR, then imports it with **Choose JAR file…**.
The browser verifies the SHA-256 and saves it to Cache Storage. The service
worker handles byte ranges for both imported game JARs and the emulator's own JAR.

To inspect a static build locally:

```sh
python3 tools/build_pages.py
python3 -m http.server 8090 --directory _site  # preview only; lacks HTTP Range support
```

For accurate CheerpJ runtime testing locally, use a server with HTTP byte-range support
(e.g. the bundled `python3 server.py` serves the local development version). The
static site builder generates `emulator/src/main.js` with the same resolution and
numpad adapters as the local preview server, leaving vendored upstream source unchanged.

After **all licensing/source/artwork requirements below are resolved**, create
repository Actions variable `POP_MOBILE_PUBLICATION_APPROVED` = `true` under
**Settings → Secrets and variables → Actions → Variables**. This is an explicit
release gate: without it, the deployment job is skipped. Next, push to `main`,
make the repository public, and select **Settings → Pages → Build and deployment
→ Source: GitHub Actions**. Run the workflow manually from **Actions** if needed.
The workflow `.github/workflows/pages.yml` tests, builds and deploys the `_site/`
directory. Visit the resulting URL and verify a user-imported game in a real
browser. Publishing is not yet tested
on the live GitHub Pages environment.

The GitHub Pages site can be public even if a private repo is allowed to use
Pages on your plan: **do not enable Pages while licensing review is incomplete**.

## Rebuilt MIDI component

The bundled `libmidi.wasm` uses the original, procedurally synthesized **PoP Mobile Original FM GM** SoundFont instead of the upstream sample bank. The generator is `tools/generate_fm_soundfont.py`; a build provenance record is in [`docs/MIDI_BUILD_PROVENANCE.md`](docs/MIDI_BUILD_PROVENANCE.md). See [`docs/MIDI_AUDIO_TEST.md`](docs/MIDI_AUDIO_TEST.md) for the manual browser-audio acceptance test. The matching complete emulator-source archive must be publicly linked alongside the binaries before a public release; see [`docs/SOURCE_COMPLIANCE.md`](docs/SOURCE_COMPLIANCE.md).

## Clean public repository history

For the separate, history-clean GitHub repository (without the legacy MIDI SoundFont binary in earlier commits), follow [`docs/CLEAN_PUBLIC_HISTORY.md`](docs/CLEAN_PUBLIC_HISTORY.md). **Do not publish the existing private development history.**

## Licensing and credits

- Original PoP Mobile source code: **GPL-3.0-or-later**; see [`LICENSE`](LICENSE).
- Third-party emulator, dependencies, CheerpJ and cover artwork: **separately licensed**; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and `assets/covers/POPRUNS-LICENSE.txt`.
- **Before publicly distributing the compiled emulator runtime**, publish and verify the assembled version-matched corresponding-source archive alongside the JAR and WebAssembly runtime, test MIDI playback, and resolve cover-image rights. Follow [`docs/SOURCE_COMPLIANCE.md`](docs/SOURCE_COMPLIANCE.md) before switching visibility or deploying Pages. The upstream freej2me-web commit alone does not establish complete compliance.
- Built with [CheerpJ](https://cheerpj.com/). The site includes a visible attribution in its footers.

The Prince of Persia games and associated intellectual property belong to their respective rights holders. This is an independent archival and research project, and the repository contains no original game JAR files.

## Usage of AI

Parts of this project were developed with substantial ChatGPT assistance and have not all been reviewed line by line. While the site's content and functionality have been tested, correct operation is not guaranteed for every file, browser or configuration.
