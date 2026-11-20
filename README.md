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

## GitHub Pages deployment

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

The workflow `.github/workflows/pages.yml` tests, builds, and deploys `_site/`
on pushes that affect the website or its static build process. Pushes affecting
only `docs/`, `tests/`, or research scripts do **not** trigger deployment.
You can always deploy manually from **Actions → Deploy PoP Mobile to GitHub Pages**.
The workflow retains the repository Actions variable
`POP_MOBILE_PUBLICATION_APPROVED=true` as a release safety gate. GitHub Pages
must be configured with **Settings → Pages → Build and deployment → GitHub Actions**.
The deployed site was tested in Firefox with a user-provided game JAR and audio.

## Emulator sources and MIDI

The bundled MIDI module uses **PoP Mobile Original FM GM**, a procedurally
generated SoundFont rather than upstream sampled instruments. The generator is
`tools/generate_fm_soundfont.py`. For SHA-256 build fingerprints, source
revisions, regeneration instructions, and build qualifications, see
[Emulator source and build provenance](https://github.com/PoPRuns/pop-mobile-browser/blob/main/docs/EMULATOR_SOURCE.md).

The v0.1.0 corresponding-source archive is available from the
[GitHub release](https://github.com/PoPRuns/pop-mobile-browser/releases/tag/v0.1.0).
The main repository contains the reduced runtime, while its matching build
sources are distributed as a separate release asset.

## Licensing and credits

- PoP Mobile original source code: **GPL-3.0-or-later**; see [`LICENSE`](LICENSE).
- Third-party emulator, dependencies, CheerpJ, and game-related artwork:
  see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and
  `assets/covers/POPRUNS-LICENSE.txt`. Software licensing does not grant
  rights to copyrighted game assets.
- This project uses [CheerpJ](https://cheerpj.com/), loaded from its official
  CDN; the website displays **Built with CheerpJ** attribution.

The Prince of Persia games and associated intellectual property belong to
their respective rights holders. This independent catalogue contains no
original game JAR files.

## Usage of AI

Parts of this project were developed with substantial ChatGPT assistance and have not all been reviewed line by line. While the site's content and functionality have been tested, correct operation is not guaranteed for every file, browser or configuration.
